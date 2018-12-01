#!/usr/bin/env python3

import glob
import hashlib
import os
import re

from flask import Flask, request, make_response, send_from_directory, redirect, abort
from werkzeug.routing import BaseConverter

app = Flask(__name__)

MFDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifests")

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

@app.route("/fixity/<path:urim>", defaults={"mfdt": "9"*14, "mfh": ""})
@app.route("/fixity/<regex('(\d{2}){2,7}'):mfdt>/<path:urim>", defaults={"mfh": ""})
@app.route("/fixity/<regex('\d{14}'):mfdt>/<regex('[a-f0-9]{32}'):mfh>/<path:urim>")
def fixity(mfh, mfdt, urim):
    qs = request.query_string.decode()
    if qs != '':
        urim += '?' + qs
    urimh = hashlib.md5(urim.encode()).hexdigest()
    if mfh:
        fpath = f"{urimh}/{mfdt}-{mfh}.json"
        print(f"Retrieving {fpath} for {urim}")
        resp = make_response(send_from_directory(MFDIR, fpath))
        resp.set_etag(mfh)
        return resp
    mfs = sorted([os.path.basename(f) for f in glob.glob(f"{MFDIR}/{urimh}/{'[0-9]'*14}-{'?'*32}.json")])
    if not mfs:
        abort(404)
    pmf = mfs[-1]
    for mf in mfs:
        if mf > mfdt:
            pmf = mf
            break
    mfdt, mfh, _ = re.split("\W", pmf)
    return redirect(f"/fixity/{mfdt}/{mfh}/{urim}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
