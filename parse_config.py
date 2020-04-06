import yaml
import re
import sys
import os

def parse_input_config():
    with open(sys.argv[1]) as f:
        try:
            y = yaml.safe_load(f)
            return y
        except yaml.YAMLError as e:
            print(e)

class Service:
    class Route:
        def __init__(self, name, route_, method, status, params):
            self.name, self.route_, self.method, self.status, self.params = \
                    name, route_, method, status, params

        def __str__(self):
            return f'Route {self.name} {self.method} {self.route_} {self.status}'

    def __init__(self, name):
        self.name = name
        self.routes = []

    def __str__(self):
        return "Service " + self.name

    def load_route(self, route_config):
        r = self.Route(route_config['name'], route_config['route'], route_config['method'], 
                route_config['status'],  route_config['params'])
        self.routes.append(r)

    def generate_service(self, filename):
        route_vars = re.compile(r'<(\w*)>')
        with open(filename, 'w') as f:
            f.write('from flask import Flask, request\n')
            f.write('app = Flask(__name__)\n')
            for r in self.routes:
                route_vars = route_vars.findall(r.route_)
                method_sig = ""
                if route_vars:
                    method_sig = ','.join(route_vars)
                f.write(f"""
@app.route('{r.route_}')
def {r.name}({method_sig}, methods=['{r.method}']):
    return 'thanx', {r.status}

""")


config = parse_input_config()
services = []
for service in config['services']:
    s = Service(service)
    for route_ in config['services'][service]['routes']:
        s.load_route(route_)
    services.append(s)

for service in services:
    if not os.path.exists(f'./{service.name}'):
        os.mkdir(f'./{service.name}')
    service.generate_service(f'./{service.name}/main.py')
