import yaml
import sys
import os
import shutil
import time

from service import Service
from docker import generate_dockercompose
from tests import run_test

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


config = parse_input_config()
services = {}
exposed_port = 5000
for service_name in config['services']:
    service = Service(service_name)
    service.exposed_port = exposed_port
    exposed_port += 1
    service.load_home_route()
    for route_ in config['services'][service_name]['routes']:
        service.load_route(route_)
    services[service_name] = service

for service_name, service in services.items():
    if not os.path.exists(f'./{service_name}'):
        os.mkdir(f'./{service_name}')
    service.generate_service(f'./{service_name}/main.py')
    service.insert_dockerfile(f'./{service_name}/Dockerfile', service.exposed_port)
    service.insert_requirements(f'./{service_name}/requirements.txt')

if not os.path.exists('./nginx_server'):
    os.mkdir('./nginx_server')
if not os.path.exists('./nginx_server/conf'):
    os.mkdir('./nginx_server/conf')
os.system('rm ./nginx_server/conf/*')
os.system('cp ./nginx/* ./nginx_server/conf')
with open('./nginx_server/Dockerfile', 'w') as f:
    f.write("""from openresty/openresty:buster-fat""")


generate_dockercompose(services)

ready_to_run = input('are you ready to run tests? y/n\n')

if ready_to_run == 'y':
    os.system('docker-compose up --build -d')
    time.sleep(3)
elif ready_to_run == 'n':
    quit()

print()
success_fail = []
for test in config['tests']:
    print("testing", test)
    success = run_test(config['tests'][test], services)
    success_fail.append((test, success))

failures = list(filter((lambda report: not report[1]), success_fail))

for fail in failures:
    print("FAIL ", fail[0])

print()
assert len(failures) == 0

os.system('docker-compose down')
