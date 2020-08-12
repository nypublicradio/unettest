import json
import os
import re
import requests
import socket

class Service:
    """
    Representation of a single SERVICE as represented in YAML.
    """
    class Route:
        """
        Each SERVICE has 1+ ROUTEs. A ROUTE has a name, route, method, status and
        optional query params.
        """
        HOME_ROUTE_NAME = "home"

        def __init__(self, name, route_, method, status, params):
            self.name, self.route_, self.method, self.status, self.params = \
                    name, route_, method, status, params


        def __str__(self):
            return f'Route -- {self.name} {self.method} {self.route_} {self.status}'


    def __init__(self, name):
        self.name = name
        self.type_ = []
        self.routes = []
        self.exposed_port = 0


    def __str__(self):
        return "Service -- " + self.name


    def get_route(self, name):
        """
        Get Route with name `name`.
        """
        matching_routes = [r for r in self.routes if r.name == name]
        if matching_routes:
            return matching_routes.pop()
        return None

    def last_call(self):
        # if 'uwsgi' in self.type_:
        #     status_code, report = self.ask_socket_for_status()
        #     return status_code, report
        # else:
        #     last_req = requests.get(f'http://localhost:{self.exposed_port}/last_call')
        #     return last_req.status_code, json.loads(last_req.text)
        last_req = requests.get(f'http://localhost:{self.exposed_port}/last_call')
        return last_req.status_code, json.loads(last_req.text)

    def ask_socket_for_status(self):
        """
        low-level connection to the socket

        not in use rn, but leaving it around in case i need it
        it in the future (sorry konmari)
        """
        resp = None
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', self.exposed_port))
            s.send(b'GET /last_call HTTP/1.1\r\nHost: localhost\r\n\r\n')
            raw_resp = s.recv(4096)
            resp = raw_resp.decode('utf-8')
        resp_elems = resp.split('\r\n')
        status = re.search('\d{3}', resp_elems[0]).group(0)
        try:
            report = json.loads(resp_elems[-1])
        except JSONDecodeError as e:
            return int(status), None
        return int(status), report




    def add_home_route(self):
        """
        Add a simple '/' response identifying the server.
        """
        r = Service.Route(Service.Route.HOME_ROUTE_NAME, '/', 'GET', 200, None)
        self.routes.append(r)


    def add_route(self, route_config):
        """
        Accept well-formatted Route config dict and add the Route to the Service.
        """
        try:
            if route_config['name'] == Service.Route.HOME_ROUTE_NAME:
                raise Exception(f"'{Service.Route.HOME_ROUTE_NAME}' is a reserved name. Please choose something else for your route name.")

            r = Service.Route(route_config['name'], route_config['route'], route_config['method'],
                           route_config['status'],  route_config.get('params', None))

        except KeyError as k:
            import pprint
            exit(f"The config file is malformed :(\n   Missing required configuration {k} in \n\n{pprint.pformat(route_config, width=20)}")

        self.routes.append(r)


    def generate_service(self, filename):
        """
        Dynamically create a Flask app defining the Service and its Routes, saving it
        to the given filename.
        """
        route_vars = re.compile(r'<(\w*)>')
        with open(filename, 'w') as f:
            f.write('from flask import Flask, request\n')
            f.write('import inspect\n')
            f.write('import time\n')
            f.write('import json\n')
            f.write('app = Flask(__name__)\n')
            f.write('last_requests = []\n')
            f.write("""
@app.route('/last_call')
def last_call():
    try:
        return json.dumps(last_requests.pop())
    except IndexError:
        return "No Previous Requests Recorded.", 404

""")
            for r in self.routes:
                path_vars = route_vars.findall(r.route_)
                method_vars = ""
                if path_vars:
                    method_vars = ','.join(path_vars)
                f.write(f"""
@app.route('{r.route_}', methods=['{r.method}'])
def {r.name}({method_vars}):
    func_name = inspect.currentframe().f_code.co_name
    last_requests.append({{"test": func_name, "route": "{r.route_}",
        "status_code": {r.status}, "method": "{r.method}",
        "params": request.args, "time": time.time()}})
    return str({r.params})

""")


    def insert_requirements(self, filename):
        """
        Populate a `requirements.txt` at the given filename.
        """
        requirements = ['flask']
        with open(filename, 'w') as f:
            for requirement in requirements:
                f.write(requirement + '\n')


    def insert_dockerfile(self, filename, exposed_port):
        with open(filename, 'w') as f:
            f.write(f"""FROM python:3.7-alpine
WORKDIR /code
ENV FLASK_APP main.py
ENV FLASK_ENV development
ENV FLASK_RUN_HOST 0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run", "-p", "{exposed_port}"]
""")

    def insert_uwsgi(self, service_dir):
        ini = os.path.join(service_dir, 'main.ini')
        wsgi = os.path.join(service_dir, 'wsgi.py')
        with open(ini, 'w') as f:
            f.write(f"""[uwsgi]
module = wsgi:app

wsgi-file = /code/wsgi.py

master = true
processes = 1
threads = 1
callable = app

socket = /tmp/{self.name}.sock
chmod-socket = 666
vacuum = true
die-on-term = true """)

        with open(wsgi, 'w') as f:
            f.write("""from main import app

if __name__ == "__main__":
    app.run() """)
