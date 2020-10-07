import json
import os
import re
import requests
import socket

from src.unettest_exceptions import RouteConfigException


def last_call(headers=None):
    reqs = requests.get('http://localhost:4888/log')
    return reqs.json()

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
        REQD_ROUTE_ATTRS = ['name', 'route', 'method', 'status']

        def __init__(self, config):
            self.validate_required_attrs(config)

            self.name, self.route_, self.method, self.status = \
                config['name'], config['route'], config['method'], config['status']

            self.params = config.get('params', None)
            if 'redirect_30x_target' in config:
                self.redirect_30x_target = config['redirect_30x_target']


        def __str__(self):
            return f'Route -- {self.name} {self.method} {self.route_} {self.status}'

        @staticmethod
        def validate_required_attrs(route_config):
            for attr in Service.Route.REQD_ROUTE_ATTRS:
                if attr not in route_config:
                    raise RouteConfigException(attr)


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

    def ask_socket_for_status(self):
        """
        low-level connection to the socket

        not in use rn, but leaving it around in case i need it
        it in the future (sorry konmari)
        """
        resp = None
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', self.exposed_port))
            s.send(b'GET /last_call HTTP/1.1\r\nHost: wnycstudios.demo2.wnyc.net\r\n\r\n')
            raw_resp = s.recv(4096)
            resp = raw_resp.decode('utf-8')
        resp_elems = resp.split('\r\n')
        status = re.search('\d{3}', resp_elems[0]).group(0)
        try:
            report = json.loads(resp_elems[-1])
        except json.JSONDecodeError as e:
            return int(status), None
        return int(status), report


    def add_home_route(self):
        """
        Add a simple '/' response identifying the server.
        """
        home_route = Service.Route( {
            'name': Service.Route.HOME_ROUTE_NAME,
            'route': '/',
            'method': 'GET',
            'status': 200
        } )
        self.routes.append(home_route)


    def add_route(self, route_config):
        """
        Accept well-formatted Route config dict and add the Route to the Service.
        """
        try:
            if route_config['name'] == Service.Route.HOME_ROUTE_NAME:
                raise Exception(f"'{Service.Route.HOME_ROUTE_NAME}' is a reserved name. Please choose something else for your route name.")

            r = Service.Route(route_config)

        except RouteConfigException as k:
            import pprint
            exit(f"The config file is malformed :(\n   Missing required configuration {k} in \n\n{pprint.pformat(route_config, width=20)}")

        self.routes.append(r)


    def generate_ledger(name, filename, routes):
        """
        unused routes arg is for signature conformity with `generate_service`
        """
        with open(filename, 'w') as f:
            f.write('''from flask import Flask, request
import json

app = Flask(__name__)

ledger = []

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/log', methods=['GET', 'POST'])
def log():
    if request.method == 'POST':
        ledger.append(request.json)
        return 'added to ledger'
    elif request.method == 'GET':
        try:
            json_ledger = json.dumps(ledger.pop())
            return json_ledger
        except IndexError:
            return json.dumps([])
''')


    def generate_service(name, filename, routes):
        """
        Dynamically create a Flask app defining the Service and its Routes, saving it
        to the given filename.
        """
        route_vars = re.compile(r'<(\w*)>')
        with open(filename, 'w') as f:
            f.write('from flask import Flask, request, redirect\n')
            f.write('import inspect\n')
            f.write('import requests\n')
            f.write('import time\n')
            f.write('import json\n')
            f.write('app = Flask(__name__)\n')

            for rt in routes:
                return_stmnt = ''
                method_vars = ''

                path_vars = route_vars.findall(rt.route_)

                if path_vars:
                    method_vars = ','.join(path_vars)

                if rt.status // 100 == 3:
                    return_stmnt = f'return redirect("{rt.redirect_30x_target}", {rt.status})'
                else:
                   return_stmnt = f'return str({rt.params}), {rt.status}'

                f.write(f"""
@app.route('{rt.route_}', methods=['{rt.method}'])
def {rt.name}({method_vars}):
    func_name = inspect.currentframe().f_code.co_name
    rq = requests.post('http://ledger:4888/log', json={{"service": "{name}", "test": func_name, "route": "{rt.route_}",
        "status_code": {rt.status}, "method": "{rt.method}",
        "params": request.args, "time": time.time()}})
    app.logger.info(f'{{"success" if rq.status_code == 200 else "failure"}} saving to ledger')
    {return_stmnt}

""")
            f.write('''if __name__ == "__main__":
    app.run(host='0.0.0.0')''')


    def insert_requirements(filename):
        """
        Populate a `requirements.txt` at the given filename.
        """
        requirements = ['flask', 'requests']
        with open(filename, 'w') as f:
            for requirement in requirements:
                f.write(requirement + '\n')


    def insert_dockerfile(filename, exposed_port):
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
buffer-size = 32768

socket = {self.sockpath}
chmod-socket = 666
vacuum = true
die-on-term = true """)

        with open(wsgi, 'w') as f:
            f.write("""from main import app

if __name__ == "__main__":
    app.run() """)
