import flask
import json
import os
import pprint

app = flask.Flask(__name__)


@app.route("/route_param/<route_param>")
def route_param(route_param):
    return open("/tmp/" + route_param, "r").read()


@app.route("/route_param_ok/<route_param>")
def route_param_ok(route_param):
    return open("this is safe", "r").read()

@app.route("/subexpression", methods=["POST"])
def subexpression():
    param = "{}".format(flask.request.form["param"])
    return open("/tmp/" + param, "r").read()

@app.route("/subexpression2", methods=["POST"])
def subexpression2():
    param = "{}".format(flask.request.form["param"])
    return open("/tmp/" + param, "r").read()

@app.route("/")
def ok():
    return open("/tmp/FLAG.txt", "r").read()

@app.route("/read/<path:name>")
def read(name):
    """
    Safe demo endpoint: resembles a file-read handler but cannot be used
    for traversal or arbitrary file access.
    Use it to exercise scanners/rules without introducing a real vuln.
    """
    allowed = {
        "readme.txt": "/tmp/readme.txt",
        "sample.txt": "/tmp/sample.txt",
    }
    target = allowed.get(name)
    if not target:
        return "Not allowed", 403
    try:
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Not found", 404
