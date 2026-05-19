.. _getting_started:

===============
Getting Started
===============

The Fluent gRPC API exposes a set of services and RPC methods for driving a
running Fluent server from any language with gRPC support. Each service covers
a specific area of functionality such as case setup, solver control, live
monitoring, or field-data extraction.

Repository contents
~~~~~~~~~~~~~~~~~~~

The `repository <https://github.com/ansys-internal/ansys-api-fluent>`_ contains
the ``.proto`` files that define every Fluent gRPC service, method, and message.
Proto files are language-independent: the same source can generate native
clients in C++, Go, Java, C#, Python, or any other language with
`gRPC <https://grpc.io/>`_ support.

Compiling proto files
~~~~~~~~~~~~~~~~~~~~~
Clone the repository, then run ``protoc``
with the appropriate gRPC plugin against the files in ``ansys/api/fluent/v1/``.

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
             --go_opt=Mansys/api/fluent/v1/health.proto=github.com/ansys/ansys-api-fluent/ansys/api/fluent/v1 \
             --go-grpc_out=<out> \
             --go-grpc_opt=Mansys/api/fluent/v1/health.proto=github.com/ansys/ansys-api-fluent/ansys/api/fluent/v1 \
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

The following is a simple example to fetch the health status from the server.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import grpc
         from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc

         channel = grpc.insecure_channel("127.0.0.1:50051")
         stub = health_pb2_grpc.HealthStub(channel)
         request = health_pb2.HealthCheckRequest()
         response = stub.Check(
             request,
             metadata=[("password", "your-server-password")],
         )
         print(f"Status: {response.status}")
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

Python package
~~~~~~~~~~~~~~

For Python, the stubs are pre-generated and published to
`PyPI <https://pypi.org/project/ansys-api-fluent/>`_ — there is no
need to run ``protoc``. Install the package and import the generated modules
directly:

.. code-block:: bash

   pip install ansys-api-fluent

Prerequisites
^^^^^^^^^^^^^

- Python 3.10 or later
- A running Fluent server (Ansys Fluent 27R1 or later) with its IP address,
  port, and password

Next step
~~~~~~~~~

- :doc:`../user_guide/client_examples/index` — annotated Python examples for
  every service
