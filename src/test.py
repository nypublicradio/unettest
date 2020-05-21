import json
import requests

from collections import namedtuple


def run_tests(tests, services):
    test_reports = []
    Report = namedtuple('Report', ['test_name', 'success'])
    for test in tests:
        print()
        print("Testing", test.name)
        success = run_test(test, services)
        test_reports.append(Report(test.name, success))
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


def run_test(test, services):
    """
    return true if success, false if failure
    """
    successes = []

    send_to_nginx(test.uri, test.req_method)

    for expect in test.expects:
        sys_under_test = services.get(expect.service)
        sys_route = sys_under_test.get_route(expect.route_)
        if not sys_route:
            print(f"  no route found '{expect.route_}' in {sys_under_test}")
            successes.append(False)
            break

        last_req = requests.get(f'http://localhost:{sys_under_test.exposed_port}/last_call')

        if last_req.status_code == 404:
            print(f'  request {test.req_method} {test.uri} was never called')
            successes.append(False)
            break

        report_from_service = json.loads(last_req.text)
        # target = test.uri
        # if test.uri_vars:
        #     for varname, varvalue in test.uri_vars.items():
        #         # un-interpolate variables
        #         # NGINX can take a var like /my/<awesome>/route/
        #         # and you might have called it with /my/gnarly/route
        #         # and now to cross reference it against the original definition
        #         # we take out `gnarly` and replace it with the <awesome> placeholder again.
        #         target = target.replace(varvalue, f'<{varname}>')

        target_called = report_from_service['route'] == sys_route.route_
        print(f'  asserting target route {sys_route.route_} was called . . . ', end='')
        if target_called:
            print('\tYes')
            successes.append(True)
        else:
            print('\tNo')
            successes.append(False)

        print(f'            that endpoint returned {expect.return_status} . . . ', end='')
        if report_from_service['status_code'] == expect.return_status:
            print('\tYes')
            successes.append(True)
        else:
            print('\tNo')
            successes.append(False)

        print(f'            it was invoked with {expect.method} . . . ', end='')
        if report_from_service['method'] == expect.method:
            print('\tYes')
            successes.append(True)
        else:
            print('\tNo')
            successes.append(False)

    # print(f'            included query params {expect.params} . . . ', end='')
    # TODO query params to come

    return all(successes)
