import os

from src.ondisk_config import WORK_DIR

def tear_down():
    os.system('docker-compose down')
    os.system(f'rm -rf {WORK_DIR}')
    os.system(f'echo "unettest has finished its business"')


def spin_up(detach=True, build=True):
    build_arg = " --build " if build else ""
    detach_arg = " --detach " if detach else ""
    os.system(f'docker-compose up {build_arg} {detach_arg}')
