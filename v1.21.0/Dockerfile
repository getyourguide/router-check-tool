# https://github.com/envoyproxy/envoy/blob/v1.21.0/ci/README.md#ubuntu-envoy-image
FROM envoyproxy/envoy-build-ubuntu:81a93046060dbe5620d5b3aa92632090a9ee4da6 as builder

ENV ENVOY_TAG v1.21.0

RUN git clone https://github.com/envoyproxy/envoy.git

WORKDIR /envoy

RUN git checkout ${ENVOY_TAG}

RUN bazel build --verbose_failures --sandbox_debug --subcommands //test/tools/router_check:router_check_tool

FROM ubuntu

COPY --from=builder /envoy/bazel-bin/test/tools/router_check/router_check_tool /usr/local/bin/
RUN apt-get update && apt-get install -y \
  libatomic1 \
  && rm -rf /var/lib/apt/lists/*

ENTRYPOINT [ "/usr/local/bin/router_check_tool"]
