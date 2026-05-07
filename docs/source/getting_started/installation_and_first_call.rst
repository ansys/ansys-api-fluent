Installation and First Call
===========================

This guide shows how to install the package and make your first service calls.
For a map of the whole API, read :doc:`fluent_grpc_api` first.

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install ansys-api-fluent

Prerequisites
~~~~~~~~~~~~~

- Python 3.10 or later
- A running Fluent server (Ansys Fluent 27R1 or later) with its IP address,
  port, and password

What this package provides
~~~~~~~~~~~~~~~~~~~~~~~~~~

The package contains pre-generated Python stubs for every Fluent gRPC service.
There is no need to run ``protoc`` — import the generated modules directly:

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc
   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

The underlying ``.proto`` files are language-independent. If you need a client
in another language, clone the repository, then run ``protoc`` with the
appropriate gRPC plugin against the files in ``ansys/api/fluent/v1/``.

.. note::

   The commands below are illustrative. Exact flags and plugin paths vary
   by platform and installed toolchain.

.. tabs::

   .. tab:: Python

      .. code-block:: bash

         pip install grpcio-tools
         python -m grpc_tools.protoc \
             -I ansys/api/fluent/v1 \
             --python_out=<out> \
             --grpc_python_out=<out> \
             ansys/api/fluent/v1/health.proto

   .. tab:: C++

      .. code-block:: bash

         protoc \
             -I ansys/api/fluent/v1 \
             --cpp_out=<out> \
             --grpc_out=<out> \
             --plugin=protoc-gen-grpc=grpc_cpp_plugin \
             ansys/api/fluent/v1/health.proto

   .. tab:: Go

      .. code-block:: bash

         protoc \
             -I ansys/api/fluent/v1 \
             --go_out=<out> \
             --go_opt=Mhealth.proto=github.com/ansys/ansys-api-fluent/v1 \
             --go-grpc_out=<out> \
             --go-grpc_opt=Mhealth.proto=github.com/ansys/ansys-api-fluent/v1 \
             ansys/api/fluent/v1/health.proto

   .. tab:: Java

      .. code-block:: bash

         protoc \
             -I ansys/api/fluent/v1 \
             --java_out=<out> \
             --grpc-java_out=<out> \
             --plugin=protoc-gen-grpc-java=protoc-gen-grpc-java \
             ansys/api/fluent/v1/health.proto

   .. tab:: C#

      .. code-block:: bash

         protoc \
             -I ansys/api/fluent/v1 \
             --csharp_out=<out> \
             --grpc_out=<out> \
             --plugin=protoc-gen-grpc=grpc_csharp_plugin \
             ansys/api/fluent/v1/health.proto

Basic pattern
~~~~~~~~~~~~~

Every gRPC call follows the same steps: create a channel, create a stub,
build a request, and call the RPC with the server password in the metadata.
The health check below is the simplest possible example — and the right first
call to make before issuing any simulation work.

.. note::

   The code snippets below are for illustration only and have not been
   tested against a live server.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import grpc
         from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc

         channel = grpc.insecure_channel("127.0.0.1:50051")
         stub = health_pb2_grpc.HealthStub(channel)
         resp = stub.Check(
             health_pb2.HealthCheckRequest(),
             metadata=[("password", "your-server-password")],
         )
         print(f"Status: {resp.status}")
         channel.close()

   .. tab:: C++

      .. code-block:: cpp

         #include <iostream>
         #include <grpcpp/grpcpp.h>
         #include "health.grpc.pb.h"

         int main() {
             auto channel = grpc::CreateChannel(
                 "127.0.0.1:50051", grpc::InsecureChannelCredentials());
             grpc::ClientContext ctx;
             ctx.AddMetadata("password", "your-server-password");
             auto stub = ansys::api::fluent::v1::Health::NewStub(channel);
             ansys::api::fluent::v1::HealthCheckRequest req;
             ansys::api::fluent::v1::HealthCheckResponse resp;
             stub->Check(&ctx, req, &resp);
             std::cout << "Status: " << resp.status() << std::endl;
         }

   .. tab:: Go

      .. code-block:: go

         package main

         import (
             "context"
             "fmt"
             "log"
             "google.golang.org/grpc"
             "google.golang.org/grpc/credentials/insecure"
             "google.golang.org/grpc/metadata"
             pb "github.com/ansys/ansys-api-fluent/ansys/api/fluent/v1"
         )

         func main() {
             conn, _ := grpc.Dial("127.0.0.1:50051",
                 grpc.WithTransportCredentials(insecure.NewCredentials()))
             defer conn.Close()
             ctx := metadata.AppendToOutgoingContext(
                 context.Background(), "password", "your-server-password")
             resp, err := pb.NewHealthClient(conn).Check(ctx, &pb.HealthCheckRequest{})
             if err != nil {
                 log.Fatal(err)
             }
             fmt.Printf("Status: %v\n", resp.Status)
         }

   .. tab:: Java

      .. code-block:: java

         import io.grpc.*;
         import io.grpc.stub.MetadataUtils;
         import ansys.api.fluent.v1.*;

         public class HealthCheck {
             public static void main(String[] args) {
                 Metadata headers = new Metadata();
                 headers.put(Metadata.Key.of("password",
                     Metadata.ASCII_STRING_MARSHALLER), "your-server-password");
                 ManagedChannel channel = ManagedChannelBuilder
                     .forAddress("127.0.0.1", 50051).usePlaintext().build();
                 HealthGrpc.HealthBlockingStub stub =
                     MetadataUtils.attachHeaders(
                         HealthGrpc.newBlockingStub(channel), headers);
                 HealthCheckResponse resp =
                     stub.check(HealthCheckRequest.newBuilder().build());
                 System.out.println("Status: " + resp.getStatus());
                 channel.shutdown();
             }
         }

   .. tab:: C#

      .. code-block:: csharp

         using Grpc.Core;
         using Ansys.Api.Fluent.V1;

         var channel = new Channel("127.0.0.1:50051", ChannelCredentials.Insecure);
         var headers = new Metadata { { "password", "your-server-password" } };
         var client = new Health.HealthClient(channel);
         var resp = client.Check(new HealthCheckRequest(),
             new CallOptions(headers: headers));
         Console.WriteLine($"Status: {resp.Status}");
         await channel.ShutdownAsync();

A non-serving status means the server is not ready; further calls will fail.

Common errors
~~~~~~~~~~~~~

- **UNAVAILABLE** — wrong host/port or server not running. Check the address
  and confirm the server process is up.
- **Authentication failure** — wrong password or missing metadata. Ensure every
  RPC call includes ``metadata=[("password", PASSWORD)]``.
- **DEADLINE_EXCEEDED** — the timeout is too short. Increase it, especially
  for large streaming calls.

Next steps
~~~~~~~~~~

- :doc:`fluent_grpc_api` — understand the overall API structure before writing more code
- :doc:`../user_guide/build_a_client` — how the DataModel and Settings services
  work and how to use them as the foundation for a minimal client
- :doc:`../user_guide/client_examples/index` — annotated Python examples for
  every service

