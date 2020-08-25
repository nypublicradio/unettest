import sys
import time
import requests
import argparse
import signal

import traceback

import src.ondisk_config as ondisk_config
import src.config_reader as config_reader
import src.local_network as local_network
import src.test as test

QUIT = 'q'
RUN_TESTS = 'r'
START_N_WAIT = 's'
TEST_ONLY = 't'


def signal_handler(signal, frame):
    local_network.tear_down()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

def print_success():
    print("Success!! No failures (✿◠ ‿ ◠)")

def exit_with_failures(num_failures):
    sys.exit(f'Sorry babes, you have {num_failures} failures')

def has_wsgi_service(spec):
    if not spec or 'services' not in spec:
        return False
    for serv in spec['services'].values():
        if 'uwsgi' in serv.type_:
            return True
    return False

def choose_behavior(services, nginx_spec, tests, what_to_do):
    what_to_do = input(f"""
Running interactive mode.

        What would you like to do?

        ({RUN_TESTS})un tests
        ({START_N_WAIT})pin up servers and let them run
        ({TEST_ONLY})est without starting servers (async mode)
        ({QUIT})uit

""") if what_to_do is None else what_to_do

    if what_to_do.lower() == RUN_TESTS:
        ondisk_config.mk_architecture(services, nginx_spec, args.nginx_conf)
        has_wsgi = has_wsgi_service(nginx_spec)
        local_network.spin_up(reboot_openresty=has_wsgi)

        wait_until_up(services)

        services = {**services, **nginx_spec['services']} if nginx_spec and 'services' in nginx_spec \
                else services
        test_results = test.run_tests(tests, services)
        failures = test.analyze_test_results(test_results)

        try:
            assert len(failures) == 0
        except AssertionError:
            local_network.tear_down()
            exit_with_failures(len(failures))

        local_network.tear_down()
        print_success()

    elif what_to_do.lower() == START_N_WAIT:
        ondisk_config.mk_architecture(services, nginx_spec, args.nginx_conf)
        has_wsgi = has_wsgi_service(nginx_spec)
        local_network.spin_up(detach=False, reboot_openresty=has_wsgi)
        local_network.tear_down()

    elif what_to_do.lower() == TEST_ONLY:
        try:
            services = {**services, **nginx_spec['services']} if nginx_spec and 'services' in nginx_spec \
                    else services
            test_results = test.run_tests(tests, services)
            failures = test.analyze_test_results(test_results)
            assert len(failures) == 0
            print_success()
        except requests.exceptions.ConnectionError:
            sys.exit("ERROR: Cannot connect to services. Make sure they are running in a separate process.")
        except AssertionError:
            exit_with_failures(len(failures))

    elif what_to_do.lower() == QUIT:
        quit()

    else:
        choose_behavior(services, tests, input('\nplease give a useful selection\n'))


def wait_until_up(services):
    up = [False]
    while not all(up):
        try:
            up = [requests.get(f'http://localhost:{s.exposed_port}/').status_code == 200 for s in services.values()]
        except requests.exceptions.ConnectionError:
            up = [False]


parser = argparse.ArgumentParser(usage='unettest [-hrst] [--nginx-conf NGINX_CONF] file',
            description='if u got a network, u net test - - - NYPR - - - v0.2.0',
            epilog='help, tutorials, documentation: available ~~ http://unettest.net',
            formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=35))
parser.add_argument('config', help='unettest yaml config', type=str)
parser.add_argument('-r', '--run-tests', help='start unettest and run tests', action='store_true')
parser.add_argument('-s', '--spin-up', help='spin up servers and wait', action='store_true')
parser.add_argument('-t', '--test-only', help='run tests async', action='store_true')
parser.add_argument('--nginx-conf', help='dir with nginx confs (default: ./nginx/)')
args = parser.parse_args()

tests, services, nginx_spec = None, None, None

try:
    config = config_reader.read_input_config(args.config)
    tests = config_reader.parse_tests(config['tests'])
    services = config_reader.parse_services(config['services'])
    if 'nginx' in config:
        nginx_spec = config_reader.parse_nginx(config['nginx'])
except Exception as e:
    print("There was an error parsing your config:", e)
    sys.exit(1)

what_to_do = None

if args.run_tests:
    what_to_do = RUN_TESTS
elif args.spin_up:
    what_to_do = START_N_WAIT
elif args.test_only:
    what_to_do = TEST_ONLY

try:
    choose_behavior(services, nginx_spec, tests, what_to_do)
except Exception as e:
    print("Error running unettest:", e)
    # traceback.print_exc() # uncomment to debug
    sys.exit(1)
