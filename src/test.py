import json
import requests

from collections import namedtuple
from src.service import last_call

from src.unettest_exceptions import MockServiceConnectionException, MockServiceNotFound, NginxConfigurationException

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


def send_to_nginx(path, request_type, headers):
    if request_type == 'GET':
        return requests.get(f'http://localhost:4999{path}', headers=headers)
    elif request_type == 'POST':
        return requests.post(f'http://localhost:4999{path}', headers=headers)


def run_test(test, services):
    """
    return true if success, false if failure
    """
    successes = []

    try:
        send_to_nginx(test.uri, test.req_method, test.headers)
    except requests.exceptions.ConnectionError:
        raise MockServiceConnectionException("can't connect to service under test. perhaps an nginx misconfiguration? Is Host header correct?")
    except requests.exceptions.TooManyRedirects:
        raise NginxConfigurationException("nginx config: too many redirects")

    test_reports = []
    report = last_call(test.headers)
    while report:
        test_reports.append(report)
        report = last_call(test.headers)


    for expect in test.expects:
        sys_under_test = services.get(expect.service)
        if sys_under_test is None:
            servs = [s for s in services.keys()]
            raise MockServiceNotFound(f'service {expect.service} not found in {servs}')
        sys_route = sys_under_test.get_route(expect.route_)
        if not sys_route:
            print(f"  no route found '{expect.route_}' in {sys_under_test}")
            successes.append(False)
            break

        test_report = None
        for report in test_reports:
            if report['service'] == expect.service and report['test'] == expect.route_:
                test_report = report
                break

        # target = test.uri
        # if test.uri_vars:
        #     for varname, varvalue in test.uri_vars.items():
        #         # un-interpolate variables
        #         # NGINX can take a var like /my/<awesome>/route/
        #         # and you might have called it with /my/gnarly/route
        #         # and now to cross reference it against the original definition
        #         # we take out `gnarly` and replace it with the <awesome> placeholder again.
        #         target = target.replace(varvalue, f'<{varname}>')

        target_called = test_report['route'] == sys_route.route_
        print(f'  asserting target route {sys_route.name} {sys_route.route_} was called . . . ', end='')
        if target_called:
            print('Yes')
            successes.append(True)
        else:
            print('\tNo')
            successes.append(False)

        print(f'            that endpoint returned {expect.return_status} . . . ', end='')
        if test_report['status_code'] == expect.return_status:
            print('\tYes')
            successes.append(True)
        else:
            print('\tNo')
            successes.append(False)

        print(f'            it was invoked with {expect.method} . . . ', end='')
        if test_report['method'] == expect.method:
            print('\tYes')
            successes.append(True)
        else:
            print('\tNo')
            successes.append(False)

        print()

    # print(f'            included query params {expect.params} . . . ', end='')
    # TODO query params to come

    return all(successes)
