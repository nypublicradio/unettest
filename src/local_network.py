import os
import requests
import subprocess
import time

from src.ondisk_config import WORK_DIR
from src.ondisk_config import reload_nginx_config

def tear_down():
    os.system('docker-compose down')
    os.system(f'rm -rf {WORK_DIR}')
    os.system(f'echo "unettest has finished its business"')


def spin_up(detach=True, build=True, reboot_openresty=False):
    """
    reboot_openresty: when openresty is running side by side with a uwsgi
                      app it needs a kick in the seat of the pants after
                      startup to connect. set to True to administer said
                      kick.
    """
    build_arg = " --build " if build else ""
    detach_arg = " --detach " if detach else ""
    if not detach:
        p = subprocess.Popen(['/usr/local/bin/docker-compose', 'up', '--build'])
        if reboot_openresty:
            print('nginx reloading!!!!')
            reload_nginx_config()
            print('nginx reloaded!!!!')
        p.wait()
    else:
        os.system(f'docker-compose up {build_arg} {detach_arg}')
        if reboot_openresty:
            print('nginx reloading!!!!')
            reload_nginx_config()
            print('nginx reloading!!!!')
