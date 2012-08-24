#!/usr/bin/env python
"""
A simple one-time-fileserver.

The goal of this application is to serve files, but only for a short period of time after the first request.
Once a URL has been requested, its token will expire. Administrators can re-generate tokens for files, if needed.

Dependencies:
    python-paste
    python-bottle
    python-openssl
    python-daemon
    python-redis
    redis-server
"""
import os
import random
import hashlib

from optparse import OptionParser

# http://pypi.python.org/pypi/python-daemon/
import daemon

# http://redis.io/commands
import redis

# http://bottlepy.org/docs/dev/api.html
import bottle

# http://pythonpaste.org/modules/httpserver.html
from paste import httpserver
# http://pythonpaste.org/modules/translogger.html
from paste.translogger import TransLogger

# TODO: Implement logging

parser = OptionParser()
parser.add_option("-f", "--file-store", dest="file_store", default="downloads", help="Where the static files are served from")
parser.add_option("-e", "--expiry-time", dest="expiry", default=300, help="Seconds before a token is deleted after being accessed")
parser.add_option("-c", "--certificate", dest="ssl_cert", default="secure-combined.pem", help="SSL Key and PEM combo file")
parser.add_option("--dev-mode", dest="dev_mode", action='store_true', default=False, help="Disable SSL, Disable Daemon Mode")
parser.add_option("--redis-host", dest="redis_host", default="localhost", help="Hostname of Redis Datastore")
parser.add_option("--redis-port", dest="redis_port", default=6379, help="Redis Port")
parser.add_option("--chunk-size", dest="chunk_size", default=4096, help="Chunk Size for reading from a socket")
(options, args) = parser.parse_args()

app = bottle.Bottle(catchall=False)
redb = redis.StrictRedis(host=options.redis_host, port=options.redis_port)


def token(filename, redb=redb):
    digest = hashlib.sha256(filename + str(random.random())).hexdigest()
    redb.set(digest, filename)
    return digest


def admin_token(filename, redb=redb):
    digest = hashlib.sha256("admin" + filename + str(random.random())).hexdigest()
    redb.set("admin:%s" % digest, filename)
    return digest


@app.get("/upload")
def upload_view():
    return bottle.template("upload_view")


@app.post("/upload")
def upload_handler():
    data = bottle.request.files['data']

    with open(os.path.join(options.file_store, data.filename), 'wb') as handle:
        while True:
            chunk = data.file.read(options.chunk_size)
            if chunk:
                handle.write(chunk)
            else:
                break

    return bottle.template("upload_result",
                            filename=data.filename,
                            token=token(data.filename),
                            admin_token=admin_token(data.filename))


@app.route("/download/<filename>")
def download_handler(filename):
    if filename == redb.get(bottle.request.query.token):
        redb.expire(bottle.request.query.token, options.expiry)
        return bottle.static_file(filename, root=options.file_store, download=filename)
    else:
        bottle.abort(403, "Valid Token Not Found.")


@app.route("/token/<filename>")
def token_generator(filename):
    if filename == redb.get("admin:%s" % (bottle.request.query.token)):
        return bottle.template("token_generator_result", filename=filename, token=token(filename))
    else:
        bottle.abort(403, "Valid Token Not Found.")


if not options.dev_mode:
    try:
        with daemon.DaemonContext(working_directory="."):
            httpserver.serve(TransLogger(app), host='0.0.0.0', port='443', ssl_pem=options.ssl_cert)
    except Exception as e:
        with open("daemon.log", 'a+') as fh:
            fh.write(str(e))
else:
    app.run(host="127.0.0.1", port=8080, debug=True, reloader=True)
