from config_tools import WORK_DIR

def generate_dockercompose(services):
    """
    Accept list of services and generate a docker-compose file.
    """
    with open(f'{WORK_DIR}/docker-compose.yml', 'w') as f:
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
        f.write(f'    expose:\n')
        f.write(f'      - 4999\n')
        f.write(f'    volumes:\n')
        f.write(f'      - {WORK_DIR}/nginx_server/conf:/etc/nginx/conf.d\n')
