#!/usr/bin/env python3

import glob
import hashlib
import os
import re

from flask import Flask, Response, request, make_response, send_from_directory, redirect, abort, render_template
from werkzeug.routing import BaseConverter

app = Flask(__name__)

MFDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifests")
BLKDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blocks")
BLKFILE = re.compile("^(?P<dttm>\d{14})-(?P<prev>[a-f0-9]{64})-(?P<crnt>[a-f0-9]{64}).ukvs.gz$")
PROXY = os.getenv("MANIFESTHOST", "http://localhost").strip("/")

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


def latest_block():
    ldttm = ""
    lblkid = ""
    with os.scandir(BLKDIR) as blkd:
        for blk in blkd:
            parts = BLKFILE.match(blk.name)
            if parts and parts["dttm"] > ldttm:
                ldttm = parts["dttm"]
                lblkid = parts["crnt"]
    return lblkid


def block_links(blkid):
    navs = {"self": blkid}
    blkp = glob.glob(f"{BLKDIR}/{'[0-9]'*14}-{'?'*64}-{blkid}.ukvs.gz")
    if blkp:
        prev = os.path.basename(blkp[0]).split(".")[0].split("-")[1]
        if prev != "0" * 64:
            navs["prev"] = prev
    blkp = glob.glob(f"{BLKDIR}/{'[0-9]'*14}-{blkid}-{'?'*64}.ukvs.gz")
    if blkp:
        navs["next"] = os.path.basename(blkp[0]).split(".")[0].split("-")[-1]
    blkp = glob.glob(f"{BLKDIR}/{'[0-9]'*14}-{'0'*64}-{'?'*64}.ukvs.gz")
    if blkp:
        navs["first"] = os.path.basename(blkp[0]).split(".")[0].split("-")[-1]
    lblkid = latest_block()
    if lblkid:
        navs["last"] = lblkid
    return ", ".join([f'{PROXY}/blocks/<{v}.ukvs.gz>; rel="{k}"' for k, v in navs.items()])


@app.route("/")
def serve_block_index():
    blkfs = sorted([os.path.basename(f) for f in glob.glob(f"{BLKDIR}/*.ukvs.gz")], reverse=True)
    return render_template("index.html", blks=[{"id": bl, "dttm": bl.split('-')[0], "hash": bl.split('.')[0].split('-')[-1]} for bl in blkfs])


@app.route("/blocks", strict_slashes=False)
def serve_latest_block():
    lblkid = latest_block()
    if lblkid:
        return redirect(f"{PROXY}/blocks/{lblkid}.ukvs.gz")
    abort(404)


@app.route("/blocks/<blkid>.ukvs.gz")
def serve_block(blkid):
    blkp = glob.glob(f"{BLKDIR}/{'[0-9]'*14}-{'?'*64}-{blkid}.ukvs.gz")
    if blkp:
        crntblkf = os.path.basename(blkp[0])
        resp = make_response(send_from_directory(BLKDIR, crntblkf))
        resp.headers["Content-Type"] = "application/ukvs"
        resp.headers["Content-Encoding"] = "gzip"
        resp.headers["Link"] = block_links(blkid)
        resp.set_etag(blkid)
        return resp
    abort(404)


@app.route("/manifest/<path:urim>", defaults={"mfdt": "9"*14, "mfh": ""})
@app.route("/manifest/<regex('(\d{2}){2,7}'):mfdt>/<path:urim>", defaults={"mfh": ""})
@app.route("/manifest/<regex('\d{14}'):mfdt>/<regex('[a-f0-9]{64}'):mfh>/<path:urim>")
def fixity(mfh, mfdt, urim):
    qs = request.query_string.decode()
    if qs != '':
        urim += '?' + qs
    urimh = hashlib.md5(urim.encode()).hexdigest()
    print(f"Requested => (MD5:{urimh}, Time: {mfdt}) {urim}")
    if mfh:
        fpath = f"{urimh}/{mfdt}-{mfh}.json"
        print(f"Retrieving {fpath}")
        resp = make_response(send_from_directory(MFDIR, fpath))
        resp.set_etag(mfh)
        return resp
    mfs = sorted([os.path.basename(f) for f in glob.glob(f"{MFDIR}/{urimh}/{'[0-9]'*14}-{'?'*64}.json")])
    if not mfs:
        abort(404)
    pmf = mfs[-1]
    for mf in mfs:
        if mf > mfdt:
            pmf = mf
            break
    mfdt, mfh, _ = re.split("\W", pmf)
    loc = f"{PROXY}/manifest/{mfdt}/{mfh}/{urim}"
    print(f"Redirecting to {loc}")
    return redirect(loc)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
