import json
from dolmen.api_engine.responder import reply
from dolmen.api_engine.validation import allowed, validate, cors_aware

def options(environ):
    response = reply(200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Headers"] = (
        "Authorization, Content-Type")
    return response


def allow(response):
    if response.status[0] == '2':  # 2XX Response, OK !
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@cors_aware(options, allow)
def Search(action_request, overhead):
        listing = {'status': 'ok'}
        return reply(
            200, 
            text=json.dumps(listing), 
            content_type="application/json") 


module = {
   'search': Search, 
}
