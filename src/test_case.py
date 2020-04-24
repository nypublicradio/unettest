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
