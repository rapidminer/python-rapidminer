from flask import Flask
from gevent.pywsgi import WSGIServer

app = Flask(__name__)
endpoints = {}

def start_webservice(host, port):
    http_server = WSGIServer((host, port), app)
    http_server.serve_forever()

class WebServiceException(Exception):
    def __init__(self, msg=""):
        super(WebServiceException, self).__init__(msg)

def route(endpoint, methods=["GET"]):
    if endpoint in endpoints.keys():
        raise WebServiceException("Endpoint {endpoint} is already defined.".format(endpoint=endpoint))
    if len(methods) == 0:
        raise WebServiceException("No method defined for endpoint {endpoint}.".format(endpoint=endpoint))
    decorator = app.route(endpoint, methods=methods)
    endpoints[endpoint] = methods
    return decorator