import yaml
import sys
import requests

def parse_input_config():
    """
    Opens and parses well-formatted yaml as defined in the DOCS.
    """
    with open(sys.argv[1]) as f:
        try:
            y = yaml.safe_load(f)
            return y
        except yaml.YAMLError as e:
            print(e)


config = parse_input_config()

for test in config['tests']:
    print("testing", test)
    mytest = config['tests'][test]
    request_type, target = mytest['send'], mytest['target']

    if request_type == 'GET':
        response = requests.get(f'http://localhost:4999{target}')
    elif request_type == 'POST':
        response = None

    expect = mytest['expect']
    print(expect)
    print(response)
    assert response.status_code == expect['return_status']
