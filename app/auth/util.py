import json
from urllib.parse import urlparse, urljoin

from flask import make_response, request


def make_json_response(body, status=200):
    res = make_response(json.dumps(body), status)
    res.headers["Content-Type"] = "application/json"
    return res


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
