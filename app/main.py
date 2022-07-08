import argparse
import os
import sys
import subprocess
import json


class RouterCheck(object):
    """
    RouterCheck is a helper to retrieve envoy route configuration
    from an istio proxy and run the envoy router table check tool against it.

    Args:
        namespace (str): The namespace where the deployment with a istio proxy is running.
        deployment (str): The Kubernetes deployment name you want to retrive envoy route configuration to run the tests.
        tests_dir (str): The directory where the router check tool tests are. Note: The route configuration will be writen on the same dir.
    """

    namespace: str
    deployment: str
    tests_dir: str

    _routes: list = []

    def __init__(self, namespace: str, deployment: str, tests_dir: str):
        self.namespace = namespace
        self.deployment = deployment
        self.tests_dir = tests_dir

    def run_tests(self, offline: bool):
        """Dumps the Envoy route configuration, clean the incompatible bits of it and runs
        the envoy router check tool in a docker container.

        Args:
            offline (bool): Set it to true to skip dumping a new configuration from a Pod and sanitizing it.
                            It will just run docker with the files already present in disk.
        """

        if not offline:
            self._get_envoy_routes()
            self._config_cleanup()
            self._write_to_disk()

        volume_mount: str = f"{os.getcwd()}/examples:/examples"
        image_name: str = "cainelli/router_check_tool:v1.21.0"

        for f in os.listdir(self.tests_dir):
            if "_test" not in f:
                continue

            config_name: str = f.replace("_test", "", 1)
            config_path: str = f"{self.tests_dir}{config_name}"
            tests_path: str = f"{self.tests_dir}{f}"

            if not os.path.exists(config_path):
                sys.exit(f'could not find the envoy config for test "{f}"')

            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                volume_mount,
                image_name,
                "--useproto",
                "--details",
                "--disable-deprecation-check",
                "-c",
                config_path,
                "-t",
                tests_path,
            ]

            result = subprocess.run(cmd)
            if result.returncode != 0:
                sys.exit("test failed")

    def _get_envoy_routes(self):
        cmd = [
            "istioctl",
            "proxy-config",
            "route",
            f"deploy/{self.deployment}.{self.namespace}",
            "-o",
            "json",
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        try:
            self._routes = json.loads(result.stdout)
        except:
            sys.exit("Expected json from istioctl output")

    def _config_cleanup(self):
        for route in self._routes:
            for vh in route["virtualHosts"]:
                if vh.get("rateLimits") is not None: del vh["rateLimits"]
                for route in vh["routes"]:
                    if route.get("typedPerFilterConfig") is not None: del route["typedPerFilterConfig"]
                    try:
                        del route["route"]["retryPolicy"]["retryHostPredicate"]
                    except:
                        continue

    def _write_to_disk(self):
        for route in self._routes:
            route_name: str = route.get("name")
            if route_name is None:
                continue

            output_file: str = f"{self.tests_dir}/{route_name}.json"
            with open(output_file, "w") as f:
                json.dump(route, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Istio Envoy Router Check Tool')
    parser.add_argument('--namespace',  type=str, default="istio-system", help='The namespace of the Deployment')
    parser.add_argument('--deploy',  type=str, default="ingressgateway", help='The deployment name to retrieve istio proxy route configuration from')
    parser.add_argument('--tests-dir',  type=str, required=True, help='The envoy router check tool tests directory')
    parser.add_argument('--offline',  action='store_true', help='Runs the tool without retrieving configuration from a live Pod')

    args = parser.parse_args()

    print()
    router_check = RouterCheck(
        namespace=args.namespace,
        deployment=args.deploy,
        tests_dir=args.tests_dir,
    )

    router_check.run_tests(offline=args.offline)


if __name__ == "__main__":
    main()
