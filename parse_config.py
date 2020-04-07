import yaml
import re
import sys
import os
import shutil

def parse_input_config():
    """
    Opens and parses well-formatted yaml as defined in the DOCS.
    """
    with open(sys.argv[1]) as f:
        try:
            y = yaml.safe_load(f)
            return y
        except yaml.YAMLError as e:
            print(e)

def generate_dockercompose(services):
    """
    Accept list of services and generate a docker-compose file.
    """
    with open('docker-compose.yml', 'w') as f:
        f.write("version: '3'\n")
        f.write("services:\n")
        for service in services:
            f.write(f'  {service.name}:\n')
            f.write(f'    build: ./{service.name}\n')
            f.write(f'    ports:\n')
            f.write(f'      - "{service.exposed_port}:{service.exposed_port}"\n')
            f.write(f'    expose:\n')
            f.write(f'      - {service.exposed_port}\n')
        f.write(f'  nginx_server:\n')
        f.write(f'    build: ./nginx_server\n')
        f.write(f'    ports:\n')
        f.write(f'      - "4999:80"\n')
        f.write(f'    expose:\n')
        f.write(f'      - 4999\n')
        f.write(f'    volumes:\n')
        f.write(f'      - ./nginx_server/conf:/etc/nginx/conf.d\n')

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
            f.write('app = Flask(__name__)\n')
            for r in self.routes:
                path_vars = route_vars.findall(r.route_)
                method_vars = ""
                if path_vars:
                    method_vars = ','.join(path_vars) + ', '
                f.write(f"""
@app.route('{r.route_}')
def {r.name}({method_vars}methods=['{r.method}']):
    return 'thanx', {r.status}

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


config = parse_input_config()
services = []
exposed_port = 5000
for service_name in config['services']:
    s = Service(service_name)
    s.load_home_route()
    for route_ in config['services'][service_name]['routes']:
        s.load_route(route_)
    s.exposed_port = exposed_port
    exposed_port += 1
    services.append(s)

for service in services:
    if not os.path.exists(f'./{service.name}'):
        os.mkdir(f'./{service.name}')
    service.generate_service(f'./{service.name}/main.py')
    service.insert_dockerfile(f'./{service.name}/Dockerfile', service.exposed_port)
    service.insert_requirements(f'./{service.name}/requirements.txt')

if not os.path.exists('./nginx_server'):
    os.mkdir('./nginx_server')
if not os.path.exists('./nginx_server/conf'):
    os.mkdir('./nginx_server/conf')
os.system('rm ./nginx_server/conf/*')
os.system('cp ./nginx/* ./nginx_server/conf')
with open('./nginx_server/Dockerfile', 'w') as f:
    f.write("""from openresty/openresty:buster-fat
""")


generate_dockercompose(services)
