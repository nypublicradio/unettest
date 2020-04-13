import os
import time
# import requests
import argparse

import config_tools
import test

from service import Service
from docker import generate_dockercompose

RUN_TESTS = 'r'
START_N_WAIT = 's'
QUIT = 'q'

def choose_behavior(services, tests, what_to_do=None):
    what_to_do = input(f"""
Running interactive mode.

        What would you like to do?

        ({RUN_TESTS})un tests
        ({START_N_WAIT})pin up servers and let them run
        ({QUIT})uit

""") if what_to_do is None else what_to_do

    if what_to_do.lower() == RUN_TESTS:
        config_tools.spin_up_local_network()
        # wait for systems to come up
        time.sleep(3)
        # TODO HOW TO DO BELOW WITHOUT REMOTE DISCONNECT ERR??
        # all_up, up = False, []
        # while not all_up:
            # try:
            #     up = [requests.get(f'http://localhost:{s.exposed_port}/').status_code == 200 for s in services.values()]
            # except http.client.RemoteDisconnected:
            #     all_up = [False]
            #     pass
            # all_up = all(up)
        test_results = test.run_tests(tests, services)
        failures = test.analyze_test_results(test_results)
        assert len(failures) == 0
        config_tools.tear_down_local_network()
        print("Success!! No failures")

    elif what_to_do.lower() == START_N_WAIT:
        config_tools.spin_up_local_network(detach=False)

    elif what_to_do.lower() == QUIT:
        quit()

    else:
        choose_behavior(services, tests, input('\nplease give a useful selection\n'))



parser = argparse.ArgumentParser(description='NGINX test harness', 
        formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=35))
parser.add_argument('config', help='nginxray yaml config', type=str)
parser.add_argument('-t', '--run-tests', help='run the tests', action='store_true')
parser.add_argument('--nginx-conf', help='dir with nginx confs (default: ./nginx/)')
args = parser.parse_args()


config = config_tools.parse_input_config(args.config)
tests = config['tests']
services = config_tools.configure_services(config['services'])

config_tools.mk_workspace_ondisk()
for service_name, service in services.items():
    config_tools.configure_service_ondisk(service_name, service)
if args.nginx_conf:
    config_tools.configure_nginx_ondisk(args.nginx_conf)
else:
    config_tools.configure_nginx_ondisk()

generate_dockercompose(services)


what_to_do = RUN_TESTS if args.run_tests else None

choose_behavior(services, tests, what_to_do)
