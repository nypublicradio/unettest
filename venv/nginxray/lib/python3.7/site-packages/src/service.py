import re

class Service:
    """
    Representation of a single SERVICE as represented in YAML.
    """
    class Route:
        """
        Each SERVICE has 1+ routes. A route has a name, route, method, status and 
        optional query params.
        """
        def __init__(self, name, route_, method, status, params):
            self.name, self.route_, self.method, self.status, self.params = \
                    name, route_, method, status, params

        def __str__(self):
            return f'Route {self.name} {self.method} {self.route_} {self.status}'

    def __init__(self, name):
        self.name = name
        self.routes = []
        self.exposed_port = 0

    def __str__(self):
        return "Service " + self.name

    def load_home_route(self):
        """
        Give a simple / response identifying the server.
        """
        r = self.Route("home", '/', 'GET', 200, None)
        self.routes.append(r)

    def load_route(self, route_config):
        """
        Accept well-formatted config dict and add the route to the service.
        """
        r = self.Route(route_config['name'], route_config['route'], route_config['method'], 
                route_config['status'],  route_config['params'])
        self.routes.append(r)

    def insert_requirements(self, filename):
        requirements = ['flask']
        with open(filename, 'w') as f:
            for requirement in requirements:
                f.write(requirement + '\n')

    def generate_service(self, filename):
        """
        Dynamically create a Flask app defining the service and its routes, exporting it
        to the given filepath.
        """
        route_vars = re.compile(r'<(\w*)>')
        with open(filename, 'w') as f:
            f.write('from flask import Flask, request\n')
            f.write('import inspect\n')
            f.write('import time\n')
            f.write('app = Flask(__name__)\n')
            f.write('last_requests = []\n')
            f.write(f"""
@app.route('/last_call')
def last_call():
    return last_requests[-1]

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

