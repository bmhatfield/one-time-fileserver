#!/usr/bin/env python
"""
A simple one-time-pad style fileserver.

The goal of this application is to serve files, but only for a short period of time.
Once a URL has been requested, it will expire. Administrators can re-generate tokens for files, if needed.

Dependencies:
    python-paste
    python-bottle
    python-openssl
    redis-server
    python-redis
"""

import redis
import bottle

from paste import httpserver
from paste.translogger import TransLogger

app = bottle.Bottle(catchall=False)
redb = redis.StrictRedis(host='localhost', port=6379)

expire_secs = 600


@app.route("/download/<filename>")
def download_handler(filename):
    if filename == redb.get(bottle.request.query.t):
        redb.expire(bottle.request.query.t, expire_secs)
        return bottle.static_file(filename, root='downloads')
    else:
        bottle.abort(403, "No Valid Token.")


@app.post("/upload/<filename>")
def upload_handler(filename):
    # Accepts an upload as a POST stream to be saved to disk
    pass


@app.route("/token/<filename>")
def token_generator(filename):
    # Create and store a token for the provided filename
    pass

httpserver.serve(TransLogger(app), host='0.0.0.0', port='443',
                    ssl_pem="secure.osfix.net-combined.pem")
