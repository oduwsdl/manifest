#!/usr/bin/env python3

import hashlib

from flask import Flask, request, make_response, send_from_directory, redirect

app = Flask(__name__)

@app.route("/fixity/<int:mdatetime>/<path:urir>", defaults={"hash": None})
@app.route("/fixity/<hash>/<int:mdatetime>/<path:urir>")
def fixity(hash, mdatetime, urir):
    qs = request.query_string.decode()
    if qs != '':
        urir += '?' + qs
    urirh = hashlib.md5(urir.encode()).hexdigest()
    print(f"Retrieving {urirh}-{mdatetime}.json for {urir}")
    resp = make_response(send_from_directory("manifests", f"{urirh}-{mdatetime}.json"))
    resp.direct_passthrough = False
    resp.add_etag(True)
    chash, _ = resp.get_etag()
    if not chash == hash:
        return redirect(f"/fixity/{chash}/{mdatetime}/{urir}")
    resp.headers["Content-Type"] = "application/json"
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
