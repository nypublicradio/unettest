import yaml
import os

from src.unettest_exceptions import ParseException

WORK_DIR = './unettest_apps'
NGINX_DEFAULT_DIR = './nginx/'


def mk_architecture(services, nginx_conf_dir):
    """
    Catch-all env-creator. Run this to set up everything.
    """
    if not nginx_conf_dir:
        nginx_conf_dir = NGINX_DEFAULT_DIR

    __mk_workspace()

    if 'NGINX_CONFIG' in os.environ:
        print('USING NGINX CONFS set by env var NGINX_CONFIG')
        nginx_conf_dir = os.environ['NGINX_CONFIG']

    print(f'LOADING NGINX CONFS located at {nginx_conf_dir}')

    for service_name, service in services.items():
        __add_service(service_name, service)

    __configure_nginx(nginx_conf_dir)

    __add_dockercompose(services)


def __mk_workspace():
    if not os.path.exists(WORK_DIR):
        os.mkdir(WORK_DIR)


def __add_service(service_name, service):
    """
    Configure local directory to later build into SERVICE docker image.

    MAKES DIR service
    """
    if not os.path.exists(f'{WORK_DIR}/{service_name}'):
        os.mkdir(f'{WORK_DIR}/{service_name}')
    service.generate_service(f'{WORK_DIR}/{service_name}/main.py')
    service.insert_dockerfile(f'{WORK_DIR}/{service_name}/Dockerfile', service.exposed_port)
    service.insert_requirements(f'{WORK_DIR}/{service_name}/requirements.txt')


def __add_dockercompose(services):
    """
    Accept list of Services and write to disk a docker-compose file.
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


def __configure_nginx(input_nginxconf=''):
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