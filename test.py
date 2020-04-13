import json
import requests

from collections import namedtuple

def run_tests(tests, services):
    test_reports = []
    Report = namedtuple('Report', ['test_name', 'success'])
    for test, conf in tests:
        print("testing", test)
        success = run_test(conf, services)
        test_reports.append(Report(test, success))
    return test_reports


def analyze_test_results(test_reports):
    failures = list(filter((lambda report: not report.success), test_reports))

    for fail in failures:
        print("FAIL ", fail.test_name)
    return failures


def run_test(test, services):
    successes = []

    request_type, target = test['send'], test['target']

    if request_type == 'GET':
        response = requests.get(f'http://localhost:4999{target}')
    elif request_type == 'POST':
        # TODO post
        pass

    expect = test['expect']
    sys_route, expected_results = list(expect.items())[0]
    system, route_ = sys_route.split('.')
    sys_under_test = services.get(system)

    last_req = requests.get(f'http://localhost:{sys_under_test.exposed_port}/last_call')

    stats = json.loads(last_req.text)
    target = test['target']
    for varname, varvalue in test['vars'].items():
        # un-interpolate variables
        target = target.replace(varvalue, f'<{varname}>')

    print('  asserting target route was called . . . ', end='')
    target_called = stats['route'] == target
    if target_called:
        print('Yes')
        successes.append(True)
    else:
        print('No')
        successes.append(False)


    assert response.status_code == expected_results['return_status']

    return all(successes)
