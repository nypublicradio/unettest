import yaml
import os

from src.service import Service
from src.test_case import TestCase
WORK_DIR='./nxr_apps'

def parse_services(configuration):
    services = {}
    exposed_port = 5000

    for name, config in configuration:
        service = Service(name)
        service.exposed_port = exposed_port
        exposed_port += 1
        service.load_home_route()
        for route_ in config['routes']:
            service.load_route(route_)
        services[name] = service
    return services

def parse_tests(configuration):
    tests = []
    for test_name, conf in configuration:
        tests.append(TestCase(test_name, conf))
    return tests

def tear_down_local_network():
    os.system('docker-compose down')


def spin_up_local_network(detach=True, build=True):
    build_arg = " --build " if build else ""
    detach_arg = " --detach " if detach else ""
    os.system(f'docker-compose up {build_arg} {detach_arg}')


def parse_input_config(config):
    """
    Opens and parses well-formatted yaml as defined in the DOCS.
    """
    with open(config) as f:
        try:
            y = yaml.safe_load(f)

            # load in my configs as lists of tuples (not supported by yaml afaik)
            # comes from yaml like {'serv_name': {'route': '/', 'stat...}}
            # comes from yaml like {'test_name': {'target': '/', 'var...}}
            # IE {name: content}
            # I don't want a dict with one key pointing to all the content.
            # Now it will look like ('serv_name', {'route': '/', 'stat...})
            # Now it will look like ('test_name', {'target': '/', 'var...})
            # IE (name, content)
            # Much better.
            y['services'] = [(list(c.keys())[0], list(c.values())[0]) for c in y['services']]
            y['tests'] = [(list(c.keys())[0], list(c.values())[0]) for c in y['tests']]
            
            return y
        except yaml.YAMLError as e:
            print(e)

def mk_workspace_ondisk():
    if not os.path.exists(WORK_DIR):
        os.mkdir(WORK_DIR)


def configure_service_ondisk(service_name, service):
    """
    Configure local directory to later build into SERVICE docker image.
    
    MAKES DIR service
    """
    if not os.path.exists(f'{WORK_DIR}/{service_name}'):
        os.mkdir(f'{WORK_DIR}/{service_name}')
    service.generate_service(f'{WORK_DIR}/{service_name}/main.py')
    service.insert_dockerfile(f'{WORK_DIR}/{service_name}/Dockerfile', service.exposed_port)
    service.insert_requirements(f'{WORK_DIR}/{service_name}/requirements.txt')


def configure_nginx_ondisk(input_nginxconf='./nginx/'):
    """
    Configure local directory to later build into NGINX docker image.

    MAKES DIR nginx_server
    """
    if not os.path.exists(f'{WORK_DIR}/nginx_server'):
        os.mkdir(f'{WORK_DIR}/nginx_server')
    if not os.path.exists(f'{WORK_DIR}/nginx_server/conf'):
        os.mkdir(f'{WORK_DIR}/nginx_server/conf')
    os.system(f'rm -rf {WORK_DIR}/nginx_server/conf/*')
    input_nginxconf = input_nginxconf.rstrip('/')
    os.system(f'cp -r {input_nginxconf}/* {WORK_DIR}/nginx_server/conf')
    with open(f'{WORK_DIR}/nginx_server/Dockerfile', 'w') as f:
        f.write("""from openresty/openresty:buster-fat""")


def generate_dockercompose(services):
    """
    Accept list of services and generate a docker-compose file.
    """
    with open(f'docker-compose.yml', 'w') as f:
        f.write("version: '3'\n")
        f.write("services:\n")
        for name, service in services.items():
            f.write(f'  {name}:\n')
            f.write(f'    build: {WORK_DIR}/{name}\n')
            f.write(f'    ports:\n')
            f.write(f'      - "{service.exposed_port}:{service.exposed_port}"\n')
            f.write(f'    expose:\n')
            f.write(f'      - {service.exposed_port}\n')
        f.write(f'  nginx_server:\n')
        f.write(f'    build: {WORK_DIR}/nginx_server\n')
        f.write(f'    ports:\n')
        f.write(f'      - "4999:80"\n')
        f.write(f'    environment:\n')
        f.write(f'      - env=dev\n')
        f.write(f'    expose:\n')
        f.write(f'      - 4999\n')
        f.write(f'    volumes:\n')
        # f.write(f'      - {WORK_DIR}/nginx_server/conf:/etc/nginx/conf.d\n')
        # f.write(f'      - ./scripts:/usr/local/openresty/scripts\n')
        f.write(f'      - {WORK_DIR}/nginx_server/conf:/usr/local/openresty/nginx/conf\n')


def mk_architecture_ondisk(services, nginx_conf_dir=None):
    """
    Catch-all env-creator. Run to set up everything.
    """

    mk_workspace_ondisk()

    for service_name, service in services.items():
        configure_service_ondisk(service_name, service)
    if nginx_conf_dir:
        configure_nginx_ondisk(nginx_conf_dir)
    else:
        configure_nginx_ondisk()

    generate_dockercompose(services)
