import sys
import time
import requests
import argparse
import signal

import src.config_tools as config_tools
import src.test as test

QUIT = 'q'
RUN_TESTS = 'r'
START_N_WAIT = 's'
TEST_ONLY = 't'


def signal_handler(signal, frame):
    config_tools.tear_down_local_network()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def choose_behavior(services, tests, what_to_do=None):
    what_to_do = input(f"""
Running interactive mode.

        What would you like to do?

        ({RUN_TESTS})un tests
        ({START_N_WAIT})pin up servers and let them run
        ({TEST_ONLY})est without starting servers (async mode)
        ({QUIT})uit

""") if what_to_do is None else what_to_do

    if what_to_do.lower() == RUN_TESTS:
        config_tools.mk_architecture_ondisk(services, nginx_conf_dir=args.nginx_conf)
        config_tools.spin_up_local_network()

        wait_until_up(services)

        test_results = test.run_tests(tests, services)
        failures = test.analyze_test_results(test_results)
        try:
            assert len(failures) == 0
        except AssertionError:
            config_tools.tear_down_local_network()
            sys.exit(f'Sorry pal, you have {len(failures)} failures')

        config_tools.tear_down_local_network()
        print("Success!! No failures")

    elif what_to_do.lower() == START_N_WAIT:
        config_tools.mk_architecture_ondisk(services, nginx_conf_dir=args.nginx_conf)
        config_tools.spin_up_local_network(detach=False)
        config_tools.tear_down_local_network()

    elif what_to_do.lower() == TEST_ONLY:
        try:
            test_results = test.run_tests(tests, services)
            failures = test.analyze_test_results(test_results)
            assert len(failures) == 0
            print("Success!! No failures")
        except requests.exceptions.ConnectionError:
            sys.exit("ERROR:Cannot connect to services. Make sure they are running in a separate process.")
        except AssertionError:
            sys.exit(f'Sorry pal, you have {len(failures)} failures')

    elif what_to_do.lower() == QUIT:
        quit()

    else:
        choose_behavior(services, tests, input('\nplease give a useful selection\n'))


def wait_until_up(services):
    time.sleep(3)
    # up = [False]
    # while not all(up):
    #     try:
    #         up = [requests.get(f'http://localhost:{s.exposed_port}/').status_code == 200 for s in services.values()]
    #     except requests.exceptions.ConnectionError:
    #         up = [False]


parser = argparse.ArgumentParser(usage='unettest [-hrst] [--nginx-conf NGINX_CONF] file',
            description='if u got a network, u net test - - - NYPR - - - v0.1.0',
            epilog='help, tutorials, documentation: available ~~ http://unettest.net',
            formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=35))
parser.add_argument('config', help='unettest yaml config', type=str)
parser.add_argument('-r', '--run-tests', help='start unettest and run tests', action='store_true')
parser.add_argument('-s', '--spin-up', help='spin up servers and wait', action='store_true')
parser.add_argument('-t', '--test-only', help='run tests async', action='store_true')
parser.add_argument('--nginx-conf', help='dir with nginx confs (default: ./nginx/)')
args = parser.parse_args()

config, tests, services = None, None, None

config = config_tools.parse_input_config(args.config)
try:
    tests = config_tools.parse_tests(config['tests'])
except Exception as e:
    print("Error parsing TESTS from config yaml:", e)
    sys.exit(1)

try:
    services = config_tools.parse_services(config['services'])
except Exception as e:
    print("Error parsing SERVICES from config yaml:", e)
    sys.exit(1)

what_to_do = None

if args.run_tests:
    what_to_do = RUN_TESTS
elif args.spin_up:
    what_to_do = START_N_WAIT
elif args.test_only:
    what_to_do = TEST_ONLY

choose_behavior(services, tests, what_to_do)
