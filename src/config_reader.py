import yaml

from src.test_case import TestCase
from src.service import Service


def read_input_config(config):
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
            if 'nginx' in y and 'services' in y['nginx']:
                y['nginx']['services'] = [(list(c.keys())[0], list(c.values())[0]) for c in y['nginx']['services']]

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

    def port():
        exposed_port = 5000
        while True:
            yield exposed_port
            exposed_port += 1

    exposed_port = port()

    for name, service_config in spec:
        if not name or not service_config:
            raise ParseException("Error parsing service. Is your yaml well-formed?")
        services[name] = _parse_service(name, service_config, next(exposed_port))
    return services


def _parse_service(name, config, exposed_port):
    service = Service(name)
    service.type_ = config.get('type', [])
    service.sockpath = config.get('sockpath', None)
    service.exposed_port = exposed_port
    service.add_home_route()
    for route_ in config['routes']:
        service.add_route(route_)
    return service

def parse_nginx(spec):
    """
    Returns *optional* NGINX config specified in yml.

    This is for the BASE nginx, the one exposed at 4999, the one
    tests are run through.

    Can contain SERVICEs, probably a uwsgi service running on the
    same server as the nginx file under test.
    """
    nginx_services = {}
    if 'services' in spec:
        nginx_services['services'] = {}
        for name, config in spec['services']:
            # TODO need to give sock name to support multiple uwsgi services
            nginx_services['services'][name] = _parse_service(name, config, 4999)
    return nginx_services


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
