import unittest

from app.main import RouterCheck

class TestBasic(unittest.TestCase):
    router_check: RouterCheck

    def setUp(self):
        self.router_check = RouterCheck()
        self.router_check.config_file = 'tests/fixtures/basic_config.json'

    def test_load_file(self):
        self.router_check.load_envoy_config()

        self.assertNotEqual(self.router_check.envoy_config, {})
        self.assertIsNotNone(self.router_check.envoy_config['name'])
        self.assertIsNotNone(self.router_check.envoy_config['virtualHosts'])

    def test_cleanup(self):
        self.router_check.load_envoy_config()
        self.assertIsNotNone(self.router_check.envoy_config['virtualHosts'][0]["routes"][0]['route']['retryPolicy']["retryHostPredicate"])

        self.router_check.cleanup_envoy_config()
        self.assertRaises(KeyError, self.router_check.envoy_config['virtualHosts'][0]["routes"][0]['route']['retryPolicy'].__getitem__,"retryHostPredicate")

if __name__ == '__main__':
    unittest.main()
