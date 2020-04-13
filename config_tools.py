import yaml
import os

from service import Service
WORK_DIR='.'

def configure_services(configuration):
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
    os.system(f'rm {WORK_DIR}/nginx_server/conf/*')
    input_nginxconf = input_nginxconf.rstrip('/')
    os.system(f'cp {input_nginxconf}/* {WORK_DIR}/nginx_server/conf')
    with open(f'{WORK_DIR}/nginx_server/Dockerfile', 'w') as f:
        f.write("""from openresty/openresty:buster-fat""")
