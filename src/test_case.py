from src.unettest_exceptions import ParseException

class TestCase:
    def __init__(self, name, test_configuration):
        """
        For reference, this is what a test_configuration can look like:
        {
            'send': 'GET',
            'target': '/api/v1/playlists/prophet_xml_import/wqxr/?xml_contents=%3Ctitle%3Eparty%204%20u%3C%2Ftitle%3E%0A%3Ccomposer%3ECharli%20XCX%3C%2Fcomposer%3E',
            'vars': {'stream': 'wqxr'},
            'expect':[
                // not sure how to twist the yaml into a better data structure than a
                // list of single-key dicts. i couldn't find a way to make it easy
                // to write the yaml and also easy to parse later, so i chose yaml
                // writability over data structure elegance
                { 'publisher.prophet_xml_import':
                    { 'called_times': 1,
                        'method': 'GET',
                        'return_status': 200,
                        'called_with':{
                            'xml_contents': '%3Ctitle%3Eparty%204%20u%3C%2Ftitle%3E%0A%3Ccomposer%3ECharli%20XCX%3C%2Fcomposer%3E'
                        }
                    }
                },
                { 'woms.nexgen_update':
                    { 'called_times': 1,
                        'method': 'GET',
                        'return_status': 200,
                        'called_with':{
                            'params': {
                                'stream': 'wqxr',
                                'xml_contents': '%3Ctitle%3Eparty%204%20u%3C%2Ftitle%3E%0A%3Ccomposer%3ECharli%20XCX%3C%2Fcomposer%3E'
                            }
                        }
                    }
                }
            ]
        }
        """
        self.name = name
        self.req_method = test_configuration['send']
        self.uri = test_configuration['target']
        self.uri_vars = test_configuration.get('vars', None)
        self.expects = self.parse_expects(test_configuration['expect'])

    def __str__(self):
        return f"testing {self.name}"

    class ExpectAssertion:
        """
        a test is (1) setup
                  (2) execute
                  (3) assert
        ExpectAssertion is an ORM for (3)
        """
        def __init__(self, unit_under_test, test_configuration):
            self.service, self.route_ = unit_under_test.split('.')
            self.called_times = test_configuration.get('called_times', None)
            self.method = test_configuration.get('method', None)
            self.return_status = test_configuration.get('return_status', None)
            called_with = test_configuration.get('called_with', None)
            if called_with:
                self.params = called_with.get('params', None)


    @staticmethod
    def parse_expects(configuration):
        try:
            expects = []
            for expectdef in configuration:
                unit_under_test, expect = list(expectdef.items())[0]
                assertion = TestCase.ExpectAssertion(unit_under_test, expect)
                expects.append(assertion)
            return expects
        except Exception as e:
            raise ParseException("Error parsing test `expects`. Is your yaml well-formed?")
