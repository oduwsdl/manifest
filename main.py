#!/usr/bin/env python3

import hashlib

from flask import Flask, request, make_response, send_from_directory

app = Flask(__name__)

@app.route("/fixity/<int:mdatetime>/<path:urir>", strict_slashes=False)
def fixity(mdatetime, urir):
    qs = request.query_string.decode()
    if qs != '':
        urir += '?' + qs
    urirh = hashlib.md5(f"{mdatetime}/{urir}".encode()).hexdigest()
    print(f"Retrieving {urirh}.json for {mdatetime}/{urir}")
    resp = make_response(send_from_directory("manifests", f"{urirh}.json"))
    resp.headers["Content-Type"] = "application/json"
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
