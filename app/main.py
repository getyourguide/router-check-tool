import os
import subprocess
import json


class RouterCheck(object):
    config_file: str = "" # TODO: Remove when getting configuration from istio
    output_config: str = ""
    envoy_config: dict = {}

    # Load Envoy configuration from a running Istio Ingress Gateway
    # and store it in to memory.
    def load_envoy_config(self):
        # TODO: Get the configuration from Istio Ingress Gateway

        with open(self.config_file, encoding = 'utf-8') as f:
            self.envoy_config = json.load(f)

    # Clean up the configuration by removing Istio specifics.
    def cleanup_envoy_config(self):
        for vh in self.envoy_config["virtualHosts"]:
            for route in vh["routes"]:
                del (route["route"]["retryPolicy"]["retryHostPredicate"])

    # Save the cleanned up version in a file to be used by envoy router check tool
    def save_config_to_file(self):
        with open(self.output_config, 'w') as outfile:
            json.dump(self.envoy_config, outfile, indent=2)

    # Run envoy router check tool with the config generated.
    def run_tests(self):
        cmd = [
            "docker", "run", "--rm", "-v", f'{os.getcwd()}/examples:/examples',
            "cainelli/router_check_tool:v1.21.0", "--useproto", "--details", "--disable-deprecation-check",
            "-c", self.output_config,
            "-t", "examples/test.json",
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        print(result.stdout)


def main():
    router_check = RouterCheck()
    router_check.config_file = "tests/fixtures/basic_config.json"
    router_check.output_config = "examples/routes.json"

    router_check.load_envoy_config()
    router_check.cleanup_envoy_config()
    router_check.save_config_to_file()
    router_check.run_tests()

if __name__ == '__main__':
    main()
