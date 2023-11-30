import requests
import json


def selectRequestUrl(url):
    request = requests.get(url)
    response = json.loads(request.content)
    return response
