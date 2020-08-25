import yaml
import os
import subprocess

from src.service import Service

from src.unettest_exceptions import ParseException

WORK_DIR = './.unettest_apps'
NGINX_DEFAULT_DIR = './nginx/'


def mk_architecture(services, nginx_spec, nginx_conf_dir):
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
        __add_service(service_name, service.routes, service.exposed_port, Service.generate_service)

    __add_service('ledger', [], 4888, Service.generate_ledger)

    __configure_nginx(nginx_spec, nginx_conf_dir)

    custom_mounts = nginx_spec.get('custom_mount', [])
    __add_dockercompose(services, custom_mounts)


def reload_nginx_config():
    """ HACK ALERT!!!
    
        I've run into a problem where after uwsgi starts, nginx
        is not really working. I looked into a real solution, solving
        the problem at the root, but I couldn't hack it. So here's a 
        hack. It seems to work pretty good, but it might not be durable
        or portable. I'll leave it here until it becomes a problem ¯\_(ツ)_/¯
        
        What's going on is that openresty needs to be invoked after the 
        container is up. Would love to get a Dockerfile solution for this.

    """
    nid = __get_nginx_dockerid()
    while not nid:
        nid = __get_nginx_dockerid()
    openresty_restart = f'docker exec -it {nid} openresty'
    os.system(openresty_restart)

def __get_nginx_dockerid():
    return subprocess.getoutput("docker ps --filter name='nginx' -q")


def __mk_workspace():
    if not os.path.exists(WORK_DIR):
        os.mkdir(WORK_DIR)


def __add_service(name, routes, exposed_port, constructor):
    """
    Configure local directory to later build into SERVICE docker image.

    MAKES DIR service
    """
    if not os.path.exists(f'{WORK_DIR}/{name}'):
        os.mkdir(f'{WORK_DIR}/{name}')
    constructor(name, f'{WORK_DIR}/{name}/main.py', routes)
    Service.insert_dockerfile(f'{WORK_DIR}/{name}/Dockerfile', exposed_port)
    Service.insert_requirements(f'{WORK_DIR}/{name}/requirements.txt')

def __add_dockercompose(services, custom_mounts):
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
        f.write(f'  ledger:\n')
        f.write(f'    build: {WORK_DIR}/ledger\n')
        f.write(f'    ports:\n')
        f.write(f'      - "4888:4888"\n')
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

        for mount in custom_mounts:
            f.write(f'      - {mount}\n')


def __configure_nginx(nginx_spec, input_nginxconf=''):
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
        f.write("""from openresty/openresty:buster-fat\n""")

    if nginx_spec and 'services' in nginx_spec:
        for service_name, service in nginx_spec['services'].items():
            Service.generate_service(service_name, f'{WORK_DIR}/nginx_server/main.py', service.routes)
            Service.insert_requirements(f'{WORK_DIR}/nginx_server/requirements.txt')
            service.insert_uwsgi(f'{WORK_DIR}/nginx_server/')

        with open(f'{WORK_DIR}/nginx_server/Dockerfile', 'a') as f:
            f.write("""RUN apt-get update
RUN apt-get install python3 python3-pip python3-dev -y
WORKDIR /code
COPY . .
RUN apt-get install git -y
COPY requirements.txt requirements.txt
ENV runenv test
ENV ENV test
RUN git clone https://github.com/nginx/nginx.git && cp ./nginx/conf/* /etc/nginx
RUN echo 'proxy_set_header Host $http_host;' >> /etc/nginx/proxy_params
RUN echo 'proxy_set_header X-Real-IP $remote_addr; ' >> /etc/nginx/proxy_params
RUN echo 'proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; ' >> /etc/nginx/proxy_params
RUN echo 'proxy_set_header X-Forwarded-Proto $scheme; ' >> /etc/nginx/proxy_params
RUN mkdir -p /var/log/nginx/
RUN mkdir -p /run/uwsgi
RUN pip3 install -r requirements.txt
RUN pip3 install uwsgi flask
CMD ["uwsgi", "main.ini"] """)
