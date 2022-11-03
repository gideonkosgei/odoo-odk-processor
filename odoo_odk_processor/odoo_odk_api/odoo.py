import json
import random
import urllib.request


class OdooProcessor:
    def __init__(self, host, port, db, user, password):
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password

    def json_rpc(self, url, method, params):
        data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": random.randint(0, 1000000000),
        }
        req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={
            "Content-Type": "application/json",
        })
        reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
        if reply.get("error"):
            raise Exception(reply["error"])
        return reply["result"]

    def call(self, url, service, method, *args):
        return self.json_rpc(url, "call", {"service": service, "method": method, "args": args})

    def get_url(self):
        return "http://%s:%s/jsonrpc" % (self.host, self.port)

    # get user id
    def get_uid(self):
        return self.call(self.get_url(), "common", "login", self.db, self.user, self.password)

    def process(self, db_model, payload):
        return self.call(self.get_url(), "object", "execute", self.db, self.get_uid(), self.password, db_model,
                         'create', payload)


















