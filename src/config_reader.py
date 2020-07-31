import yaml

from src.test_case import TestCase
from src.service import Service


def parse_input_config(config):
    """
    Opens and parses well-formatted yaml as defined in the DOCS.
    """
    with open(config) as f:
        try:
            y = yaml.safe_load(f)

            # load in my configs as lists of tuples (not supported by yaml afaik)
            # comes from yaml like {'serv_name': {'route': '/', 'stat...}}
            # comes from yaml like {'test_name': {'target': '/', 'var...}}
            # IE {name: content}
            # I don't want a dict with one key pointing to all the content.
            # Now it will look like ('serv_name', {'route': '/', 'stat...})
            # Now it will look like ('test_name', {'target': '/', 'var...})
            # IE (name, content)
            # Much better.
            y['services'] = [(list(c.keys())[0], list(c.values())[0]) for c in y['services']]
            y['tests'] = [(list(c.keys())[0], list(c.values())[0]) for c in y['tests']]

            return y
        except yaml.YAMLError as e:
            print(e)


def parse_services(spec):
    """
    Returns list of Services configured to spec.
    e.g.:
    [ ('$SERVICE_NAME', { 'routes': [
                                    {'name': '$ROUTE_NAME', 
                                     'route': '/route/path', 
                                     'method': 'GET', 
                                     'status': 200, 
                                     'params': ['$QUERY_PARAM_NAME'] } 
                                   ] }
    ) ]
    """
    services = {}
    exposed_port = 5000

    for name, service_config in spec:
        if not name or not service_config:
            raise ParseException("Error parsing service. Is your yaml well-formed?")
        service = Service(name)
        service.exposed_port = exposed_port
        exposed_port += 1
        service.add_home_route()
        for route_ in service_config['routes']:
            service.add_route(route_)
        services[name] = service
    return services


def parse_tests(spec):
    """
    Returns list of Tests configured to spec.
    e.g.:
    [ ('$TEST_NAME', {'send': 'GET', 
                      'target': '/test/uri/path', 
      // assertion -> 'expect': [{'$SERVICE_UNDER_TEST.$ROUTE_UNDER_TEST': 
                                    {'called_times': 1, 
                                     'method': 'GET', 
                                     'return_status': 200, 
                                     'called_with': {'params': {'author': 'davis'}}}
                                }]
                     }
    ) ]
    """
    tests = []
    for test_name, conf in spec:
        test_case = TestCase(test_name, conf)
        tests.append(test_case)
    return tests
