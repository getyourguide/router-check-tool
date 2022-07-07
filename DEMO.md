# Demo Notes

We have a demo application (`httpbin`) running on Kubernetes. One can call its endpoints from the internet:

```shell
curl https://httpbin.sandbox25.gygkube.com/headers
```

The configuration used to expose this application to the internet is the following:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: httpbin
  namespace: httpbin
spec:
  gateways:
  - istio-system/external-ingressgateway
  - mesh
  hosts:
  - httpbin.sandbox25.gygkube.com
  http:
  - match:
    - uri:
        exact: /headers
    route:
    - destination:
        host: httpbin.httpbin.svc.cluster.local
```

The team wants to make sure the `/headers` endpoint would be reachable and will go to their httpbin service. The configuration is deployed to a test cluster and above they write a test case for it:

```json
      {
        "test_name": "httpbin",
        "input": {
          "authority": "httpbin.sandbox25.gygkube.com",
          "path": "/headers",
          "method": "GET"
        },
        "validate": {
          "cluster_name": "outbound|80||httpbin.httpbin.svc.cluster.local",
        }
      }
```

Running the tool we get:

```shell
./route-check-tool --namespace istio-system --deploy external-ingressgateway  --tests-dir examples/

# output
httpbin
Current route coverage: 50%
```

The test is making sure GET requests to the /headers path would be routed to their service. With this confidence they can push this configuration to production.


After some days the team notice a unusual traffic on that endpoint and it is overloading their service. After some investigations they notice a pattern, the requests does not come with a authorization header which they authenticate the users, but still resources was being starved serving invalid requests.

To give them more time, they decide to do a check on the ingress level, if the requests does not contain an authorization header we'd return a 404 error.

With Istio we just need to add another condition to the route matching.


```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: httpbin
  namespace: httpbin
spec:
  gateways:
  - istio-system/external-ingressgateway
  - mesh
  hosts:
  - httpbin.sandbox25.gygkube.com
  http:
  - match:
    - uri:
        exact: /headers
      headers:
        authorization:
          regex: Basic .+
    route:
    - destination:
        host: httpbin.httpbin.svc.cluster.local
```

Applying the above configuration in a testing cluster we can validate it works:

```shell
curl https://httpbin.sandbox25.gygkube.com/headers -H "Authorization: Basic token"  -o /dev/null -s -v 2>&1 | grep "< HTTP"
< HTTP/2 200

curl https://httpbin.sandbox25.gygkube.com/headers -o /dev/null -s -v 2>&1 | grep "< HTTP"
< HTTP/2 404

```
To make sure nobody override this configuration they also add a test case for it.

```json
{
  "tests": [
    {
      "test_name": "httpbin",
      "input": {
        "authority": "httpbin.sandbox25.gygkube.com",
        "path": "/headers",
        "method": "GET",
        "additional_request_headers": [
          {
            "key": "authorization",
            "value": "Basic dXNlcjpzZWNyZXQtcGFzcwo="
          }
        ]
      },
      "validate": {
        "cluster_name": "outbound|80||httpbin.httpbin.svc.cluster.local"
      }
    },
    {
      "test_name": "httpbin-without-authorization-header",
      "input": {
        "authority": "httpbin.sandbox25.gygkube.com",
        "path": "/headers",
        "method": "GET"
      },
      "validate": {
        "cluster_name": ""
      }
    }
  ]
}
```

```shell
./route-check-tool --namespace istio-system --deploy external-ingressgateway  --tests-dir examples/ 2>&1 | head -n 50

# output
httpbin
httpbin-without-authorization-header
Current route coverage: 50%
```

Now, if one teams removes the header matching configuration from the VirtualService, the tests will fail with the following output:

```shell
httpbin
httpbin-without-authorization-header
expected: [], actual: [outbound|80||httpbin.httpbin.svc.cluster.local], test type: cluster_name
```
