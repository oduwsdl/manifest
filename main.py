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


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


@app.route("/")
def block_index():
    blkfs = sorted([os.path.basename(f) for f in glob.glob(f"{BLKDIR}/*.ors.gz")])
    return render_template("index.html", blks=[{"id": bl, "dttm": bl.split('-')[0], "hash": bl.split('.')[0].split('-')[-1]} for bl in blkfs])


@app.route("/blocks/<blkid>")
def serve_blocks(blkid):
    return send_from_directory(BLKDIR, blkid)


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
    loc = f"/manifest/{mfdt}/{mfh}/{urim}"
    print(f"Redirecting to {loc}")
    res = redirect(loc)
    res.autocorrect_location_header = False
    return res

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
