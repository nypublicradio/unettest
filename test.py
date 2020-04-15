import json
import requests

from collections import namedtuple

def run_tests(tests, services):
    test_reports = []
    Report = namedtuple('Report', ['test_name', 'success'])
    for test_name, configuration in tests:
        print()
        mytest = TestCase(test_name, configuration)
        print(mytest)

        success = run_test(mytest, services)
        test_reports.append(Report(mytest.name, success))
    print()
    return test_reports


def analyze_test_results(test_reports):
    failures = list(filter((lambda report: not report.success), test_reports))

    for fail in failures:
        print("FAIL ", fail.test_name)
    return failures


def send_to_nginx(path, request_type):
    if request_type == 'GET':
        return requests.get(f'http://localhost:4999{path}')
    elif request_type == 'POST':
        return requests.post(f'http://localhost:4999{path}')

class TestCase:
    class TestAssertion:
        def __init__(self, service, route_, test_configuration):
            self.service, self.route_ = service, route_
            self.called_times = test_configuration.get('called_times', None)
            self.method = test_configuration.get('method', None)
            self.return_status = test_configuration.get('return_status', None)
            called_with = test_configuration.get('called_with', None)
            if called_with:
                self.params = called_with.get('params', None)
            

    def __init__(self, name, test_configuration):
        """
        For reference, this is what a test_configuration can look like:
        {
            'send': 'GET',
            'target': '/api/v1/playlists/prophet_xml_import/wqxr/',
            'vars': {'stream': 'wqxr'},
            'expect':{
                # NOTE: atm there is support for only ever one expect value
                'publisher.prophet_xml_import':{
                    'called_times': 1,
                    'method': 'GET',
                    'return_status': 200,
                    'called_with':{
                        'params': {'stream': 'wqxr'}
                    }
                }
            }
        }
        """
        self.name = name
        self.req_method = test_configuration['send']
        self.uri = test_configuration['target']
        self.uri_vars = test_configuration.get('vars', None)
        # is expection a word?
        serv_route, expection = test_configuration['expect'].popitem()
        service, route_ = serv_route.split('.')
        self.expect = self.TestAssertion(service, route_, expection)
        # why can't expection be a word?
        # expectation has too many syllables

        self.service = service

    def __str__(self):
        return f"testing {self.name}"

def run_test(test, services):
    successes = []

    response = send_to_nginx(test.uri, test.req_method)

    sys_under_test = services.get(test.service)

    last_req = requests.get(f'http://localhost:{sys_under_test.exposed_port}/last_call')

    report_from_service = json.loads(last_req.text)
    target = test.uri
    if test.uri_vars:
        for varname, varvalue in test.uri_vars.items():
            # un-interpolate variables
            # NGINX can take a var like /my/<awesome>/route/
            # and you might have called it with /my/gnarly/route
            # and now to cross reference it against the original definition
            # we take out `gnarly` and replace it with the <awesome> placeholder again.
            target = target.replace(varvalue, f'<{varname}>')

    print(f'  asserting target route was called . . . ', end='')
    target_called = report_from_service['route'] == target
    if target_called:
        print('\tYes')
        successes.append(True)
    else:
        print('\tNo')
        successes.append(False)

    print(f'            that endpoint returned {test.expect.return_status} . . . ', end='')
    if report_from_service['status_code'] == test.expect.return_status:
        print('\tYes')
        successes.append(True)
    else:
        print('\tNo')
        successes.append(False)

    print(f'            it was invoked with {test.expect.method} . . . ', end='')
    if report_from_service['method'] == test.expect.method:
        print('\tYes')
        successes.append(True)
    else:
        print('\tNo')
        successes.append(False)

    # print(f'            included query params {test.expect.params} . . . ', end='')
    # TODO query params to come
        

    return all(successes)
