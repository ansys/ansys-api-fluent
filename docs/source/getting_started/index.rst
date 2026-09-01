.. _getting_started:

===============
Getting started
===============

Introduction
~~~~~~~~~~~~

You can use gRPC to drive your Fluent simulations from any
language that supports gRPC. A suite of neatly segregated services allows you to
perform meshing, solver setup and execution, live monitoring, field-data
extraction, and more.

Fluent's gRPC server is built in — you only need to set
up the client layer. Below, you'll find the prerequisites for setting up your
gRPC client, instructions for getting everything installed, and guidance on
building and using your gRPC client code.

Getting the proto files
~~~~~~~~~~~~~~~~~~~~~~~

The ``.proto`` files that define every Fluent gRPC service, method, and message
are available in the
`ansys-api-fluent repository <https://github.com/ansys/ansys-api-fluent>`_.

Prerequisites
~~~~~~~~~~~~~

Before compiling the ``.proto`` files you need:

- A Protocol Buffers compiler (``protoc``) on your ``PATH``, at a version
  compatible with the repository's ``.proto`` files.
- A language-specific `gRPC <https://grpc.io/>`_ plug-in or toolchain:

  - **Python** – ``grpcio-tools`` (``pip install grpcio-tools``), which bundles
    ``protoc`` and the Python plug-in.
  - **C++** – ``grpc_cpp_plugin`` and a C++ toolchain.
  - **Go** – Go toolchain plus ``protoc-gen-go`` and ``protoc-gen-go-grpc``.
  - **Java** – JDK and the ``protoc-gen-grpc-java`` plug-in.
  - **C#** – ``grpc_csharp_plugin``, or the ``Grpc.Tools`` NuGet package for
    MSBuild integration.

Ensure ``protoc`` and any ``protoc-gen-*`` plug-ins are on ``PATH``, or pass
``--plugin=protoc-gen-<lang>=<path>`` explicitly when invoking ``protoc``.

.. note::

   Each example shows the same core step (using the protocol
   compiler) but relies on a different language plug-in. The Python example uses
   the ``python -m grpc_tools.protoc`` wrapper, which bundles ``protoc`` and
   the Python plug-in together.

Compiling proto files
~~~~~~~~~~~~~~~~~~~~~

Clone the `ansys-api-fluent <https://github.com/ansys/ansys-api-fluent>`_
repository, then run ``protoc``
with the appropriate gRPC plug-in against the files in ``ansys/api/fluent/v1/``.

.. note::

   The commands below are illustrative. Exact flags and plug-in paths vary
   by platform and installed toolchain. Each command compiles a single
   ``.proto`` file (``health.proto`` is used as an example); repeat the
   invocation for each service, or pass multiple ``.proto`` files in one call,
   to generate stubs for the full API.

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
             --go_opt=Mhealth.proto=github.com/ansys/ansys-api-fluent/ansys/api/fluent/v1 \
             --go-grpc_out=<out> \
             --go-grpc_opt=Mhealth.proto=github.com/ansys/ansys-api-fluent/ansys/api/fluent/v1 \
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

Making a service call
~~~~~~~~~~~~~~~~~~~~~

The examples below fetch the health status from a running Fluent server.
Before running them, ensure you have:

- A running Fluent server (Ansys Fluent 27R1 or later)
- Its address and password

.. note::

   When Fluent starts its gRPC server, it writes the connection details to a
   server info file. Launch Fluent with the ``-sifile=<file>``
   argument to specify where that file is written. The file contains two
   lines in order: the server address and the password. Read those
   values from the file and substitute them for ``<server-address>`` and
   ``<password>`` in the examples below.

The following snippets illustrate the common pattern across languages.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import grpc
         from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc

         channel = grpc.insecure_channel("<server-address>")
         stub = health_pb2_grpc.HealthStub(channel)
         request = health_pb2.HealthCheckRequest()
         response = stub.Check(
             request,
             metadata=[("password", "<password>")],
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
                 "<server-address>", grpc::InsecureChannelCredentials());
             grpc::ClientContext ctx;
             ctx.AddMetadata("password", "<password>");
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
             conn, _ := grpc.Dial("<server-address>",
                 grpc.WithTransportCredentials(insecure.NewCredentials()))
             defer conn.Close()
             ctx := metadata.AppendToOutgoingContext(
                 context.Background(), "password", "<password>")
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
                     Metadata.ASCII_STRING_MARSHALLER), "<password>");
                 ManagedChannel channel = ManagedChannelBuilder
                     .forAddress("<server-address>").usePlaintext().build();
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

         var channel = new Channel("<server-address>", ChannelCredentials.Insecure);
         var headers = new Metadata { { "password", "<password>" } };
         var client = new Health.HealthClient(channel);
         var resp = client.Check(new HealthCheckRequest(),
             new CallOptions(headers: headers));
         Console.WriteLine($"Status: {resp.Status}");
         await channel.ShutdownAsync();

Python package (Python 3.10+)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python stubs are pre-generated and published to
`PyPI <https://pypi.org/project/ansys-api-fluent/>`_ which provides a ready-made
alternative to compiling the proto files to Python yourself. Install the Python
package and import the generated modules directly:

.. code-block:: bash

   pip install ansys-api-fluent

Next step
~~~~~~~~~

- :doc:`../user_guide/client_examples/index` — annotated Python examples for
  every service
