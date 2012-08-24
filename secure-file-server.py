#!/usr/bin/env python
"""
A simple one-time-pad style fileserver.

The goal of this application is to serve files, but only for a short period of time.
Once a URL has been requested, its token will expire. Administrators can re-generate tokens for files, if needed.

Dependencies:
    python-paste
    python-bottle
    python-openssl
    python-daemon
    redis-server
    python-redis
"""
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
(options, args) = parser.parse_args()

app = bottle.Bottle(catchall=False)
redb = redis.StrictRedis(host=options.redis_host, port=options.redis_port)


@app.route("/download/<filename>")
def download_handler(filename):
    try:
        if filename == redb.get(bottle.request.query.token):
            redb.expire(bottle.request.query.token, options.expiry)
            return bottle.static_file(filename, root=options.file_store)
        else:
            bottle.abort(403, "Valid Token Not Found.")
    except:
        bottle.abort(403, "Valid Token Not Found.")


@app.get("/upload")
def upload_view():
    # Presents view for upload actions
    pass
    

@app.post("/upload")
def upload_handler():
    filename = request.files.filename
    filedata = request.files.file
    # Accepts an upload as a POST stream to be saved to disk
    pass


@app.route("/token/<filename>")
def token_generator(filename):
    # Create and store a token for the provided filename
    pass

if not options.dev_mode:
    try:
        with daemon.DaemonContext(working_directory="."):
            httpserver.serve(TransLogger(app), host='0.0.0.0', port='443', ssl_pem=options.ssl_cert)
    except Exception as e:
        with open("daemon.log", 'a+') as fh:
            fh.write(str(e))
else:
    app.run(host="127.0.0.1", port=8080, debug=True, reloader=True)
