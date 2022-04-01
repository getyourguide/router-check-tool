# Router Check Tool

 The route table check tool checks if the route returned by a router matches what is expected. The tool can be used to check cluster name, virtual cluster name, virtual host name, manual path rewrite, manual host rewrite, path redirect, and header field matches.
 
 Envoy route table check tool reads Envoy route and its own test cases to assert routing. We would, therefore, translate VirtualServices into Envoy routes/istio config to envoy config to use the native route table check tool. This whould allow much richer/lower maintenance test cases as we can cover all of Istio api surface.

# How it works

   - Step 1. It retrieves envoy route configuration rom a live Pod from an istio proxy. It leverages Istio CLI (istioctl) to facilitate gathering the route configuration.
   - Step 2. Dumps the Envoy route configuration in the same directory where the router check tool tests are.
   - Step 3. Cleans the incompatible bits of it. Example retry_host_predicate: used to reject a host based on predefined metadata match criteria. If any of the predicates reject the host, host selection will be reattempted.
   - Step 4. Runs the envoy router check tool against it in a docker container.

The route table check tool config is composed of an array of json test objects. Each test object is composed of three parts:

  1. Test name: This field specifies the name of each test object.
  2. Input values: The input value fields specify the parameters to be passed to the router. Input values are sent to the router that determine the returned route. Example input fields include the `:authority`, `:path`, and `:method` header fields. The `:authority` [The url authority. This value along with the path parameter define the url to be matched.] and `:path` [The url path. ] fields specify the url sent to the router and are required. All other input fields are optional.
  3. Validate: The validate fields specify the expected values and test cases to check. At least one test case is required.

# Usage

```shell
./route-check-tool
usage: main.py [-h] [--namespace NAMESPACE] [--deploy DEPLOY] --tests-dir TESTS_DIR [--offline]
```

   [--namespace]

   The namespace where the deployment with a istio proxy is running.

   [--deploy]

   The Kubernetes deployment name you want to retrive envoy route configuration to run the tests.

   [--tests_dir]

   The directory where the router check tool tests are. Note: The route configuration will be writen on the same dir.

   [--offline]

   Set it to true to skip dumping a new configuration from a Pod and sanitizing it.It will just run docker with the files already present in disk.
    

# Output

The program exits with status EXIT_FAILURE if any test case does not match the expected route parameter value.
If a test fails, details of the failed test cases are printed if --details flag is provided. The first field is the expected route parameter value. The second field is the actual route parameter value. The third field indicates the parameter that is compared. In the failed test cases, conflict details are printed.

Coverage

The router check tool will report route coverage at the end of a successful test run.This reporting can be leveraged to enforce a minimum coverage percentage by using the -f or --fail-under flag. If coverage falls below this percentage the test run will fail

# Building Envoy Router Check Tool

The tool can be built using docker:

```shell
docker build . -f v1.21.0/Dockerfile -t router-check-tool
```