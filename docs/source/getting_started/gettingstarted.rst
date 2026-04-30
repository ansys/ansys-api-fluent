Getting started
===============

This guide shows how to install the package, connect to a running Fluent
server, and make your first service calls.

If you want a map of the whole API before diving in, read
:doc:`fluent_grpc_api` first — it explains the overall structure in two
pages you can scan in a few minutes.

Installation
~~~~~~~~~~~~

Install the package in your Python environment:

.. code-block:: bash

   pip install ansys-api-fluent

Or use a virtual environment:

.. code-block:: bash

   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   pip install ansys-api-fluent

What this package provides
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``ansys-api-fluent`` package contains generated Python files for the Fluent gRPC APIs:

- You do not need to run ``protoc`` yourself
- You import the generated v1 modules directly from ``ansys.api.fluent.v1``
- You can start building a client immediately
- The underlying ``.proto`` files are language-independent — see
  :ref:`other-languages` to generate native clients in C++, Go, Java, or C#

Typical imports look like:

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import field_data_pb2
   from ansys.api.fluent.v1 import field_data_pb2_grpc
   from ansys.api.fluent.v1 import health_pb2
   from ansys.api.fluent.v1 import health_pb2_grpc

Prerequisites
~~~~~~~~~~~~~

Before writing a client, you need:

- Python 3.10 or later
- A running Fluent server (Ansys Fluent 27R1 or later)
- The server IP address or host name
- The server port
- The server password

Basic pattern
~~~~~~~~~~~~~

Every v1 gRPC client follows the same steps:

1. Create a gRPC channel to the server
2. Create a stub for the service
3. Create a request message
4. Call the RPC with metadata (including password)
5. Read the response

Example:

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   
   stub = health_pb2_grpc.HealthStub(channel)
   request = health_pb2.HealthCheckRequest()
   response = stub.Check(request, metadata=metadata)
   
   print(f"Server health status: {response.status}")
   channel.close()

Complete example
~~~~~~~~~~~~~~~~

Here is a complete script that demonstrates connecting to a server and using multiple services:

.. code-block:: python
   :caption: Python

   from __future__ import annotations
   import grpc
   from ansys.api.fluent.v1 import (
       field_data_pb2, field_data_pb2_grpc,
       health_pb2, health_pb2_grpc
   )

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"
   NODE_VALUES = True

   def data_location(node_values: bool) -> field_data_pb2.DataLocation:
       return (
           field_data_pb2.DataLocation.DATA_LOCATION_NODES
           if node_values
           else field_data_pb2.DataLocation.DATA_LOCATION_ELEMENTS
       )

   def main() -> None:
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]

       health_stub = health_pb2_grpc.HealthStub(channel)
       field_stub = field_data_pb2_grpc.FieldDataStub(channel)

       try:
           # Health check
           print(f"Connecting to {HOST}:{PORT}...")
           health_response = health_stub.Check(
               health_pb2.HealthCheckRequest(),
               metadata=metadata,
           )
           print(f"Health status: {health_response.status}")

           # Get available surfaces
           surfaces_response = field_stub.GetSurfacesInfo(
               field_data_pb2.GetSurfacesInfoRequest(),
               metadata=metadata,
           )
           
           surfaces = []
           for info in surfaces_response.surface_info:
               for surface_id in info.surface_ids:
                   surfaces.append((surface_id.id, info.surface_name or "<unnamed>"))

           print(f"Available surfaces ({len(surfaces)} total):")
           for sid, sname in surfaces[:5]:
               print(f"  id={sid} name={sname}")

           # Get available scalar fields
           fields_response = field_stub.GetFieldsInfo(
               field_data_pb2.GetFieldsInfoRequest(),
               metadata=metadata,
           )

           print(f"Available scalar fields ({len(fields_response.field_info)} total):")
           for field_info in fields_response.field_info[:5]:
               print(f"  {field_info.solver_name}: {field_info.display_name}")

       except grpc.RpcError as err:
           print(f"gRPC error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       main()

.. _other-languages:

Using the API with other languages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``.proto`` source files that define the Fluent gRPC API are
language-independent. Any language with a gRPC implementation can generate a
native client from them. Clone the repository to obtain the source files:

.. code-block:: bash

   git clone https://github.com/ansys/ansys-api-fluent.git
   cd ansys-api-fluent

The ``.proto`` files are located under ``ansys/api/fluent/v1/``.

Generating stubs
^^^^^^^^^^^^^^^^

Install the ``protoc`` compiler and the appropriate gRPC plugin for your
language, then run the relevant command below from the repository root.
Replace ``<out>`` with your project's source directory.

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

         # Requires protoc and grpc_cpp_plugin on PATH
         protoc \
             -I ansys/api/fluent/v1 \
             --cpp_out=<out> \
             --grpc_out=<out> \
             --plugin=protoc-gen-grpc=grpc_cpp_plugin \
             ansys/api/fluent/v1/health.proto

   .. tab:: Go

      .. code-block:: bash

         go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
         go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
         protoc \
             -I ansys/api/fluent/v1 \
             --go_out=<out> \
             --go_opt=M health.proto=github.com/ansys/ansys-api-fluent/v1 \
             --go-grpc_out=<out> \
             --go-grpc_opt=M health.proto=github.com/ansys/ansys-api-fluent/v1 \
             ansys/api/fluent/v1/health.proto

      .. note::

         The Fluent ``.proto`` files do not declare a ``go_package`` option, so
         ``--go_opt=M<file>=<import_path>`` and ``--go-grpc_opt=M<file>=<import_path>``
         mappings are required for every proto file you compile. Repeat the
         ``M`` flag for each ``.proto`` you pass to ``protoc``.

   .. tab:: Java

      .. code-block:: bash

         # Requires protoc and protoc-gen-grpc-java plugin on PATH
         protoc \
             -I ansys/api/fluent/v1 \
             --java_out=<out> \
             --grpc-java_out=<out> \
             --plugin=protoc-gen-grpc-java=protoc-gen-grpc-java \
             ansys/api/fluent/v1/health.proto

   .. tab:: C#

      .. code-block:: bash

         # Requires protoc and grpc_csharp_plugin on PATH
         protoc \
             -I ansys/api/fluent/v1 \
             --csharp_out=<out> \
             --grpc_out=<out> \
             --plugin=protoc-gen-grpc=grpc_csharp_plugin \
             ansys/api/fluent/v1/health.proto

Health check example
^^^^^^^^^^^^^^^^^^^^

The following minimal health check uses the generated stubs to verify that
the Fluent server is ready. All examples connect to ``127.0.0.1:50051``
and pass the server password as channel metadata.

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
                 "127.0.0.1:50051",
                 grpc::InsecureChannelCredentials());

             grpc::ClientContext ctx;
             ctx.AddMetadata("password", "your-server-password");

             auto stub = ansys::api::fluent::v1::Health::NewStub(channel);
             ansys::api::fluent::v1::HealthCheckRequest req;
             ansys::api::fluent::v1::HealthCheckResponse resp;
             stub->Check(&ctx, req, &resp);

             std::cout << "Status: " << resp.status() << std::endl;
             return 0;
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
             conn, err := grpc.Dial("127.0.0.1:50051",
                 grpc.WithTransportCredentials(insecure.NewCredentials()))
             if err != nil {
                 log.Fatal(err)
             }
             defer conn.Close()

             ctx := metadata.AppendToOutgoingContext(
                 context.Background(), "password", "your-server-password")

             client := pb.NewHealthClient(conn)
             resp, err := client.Check(ctx, &pb.HealthCheckRequest{})
             if err != nil {
                 log.Fatal(err)
             }
             fmt.Printf("Status: %v\n", resp.Status)
         }

   .. tab:: Java

      .. code-block:: java

         import io.grpc.ManagedChannel;
         import io.grpc.ManagedChannelBuilder;
         import io.grpc.Metadata;
         import io.grpc.stub.MetadataUtils;
         import ansys.api.fluent.v1.HealthGrpc;
         import ansys.api.fluent.v1.HealthCheckRequest;
         import ansys.api.fluent.v1.HealthCheckResponse;

         public class HealthCheckExample {
             public static void main(String[] args) {
                 Metadata headers = new Metadata();
                 headers.put(
                     Metadata.Key.of("password", Metadata.ASCII_STRING_MARSHALLER),
                     "your-server-password");

                 ManagedChannel channel = ManagedChannelBuilder
                     .forAddress("127.0.0.1", 50051)
                     .usePlaintext()
                     .build();

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

         var channel = new Channel(
             "127.0.0.1:50051", ChannelCredentials.Insecure);
         var headers = new Metadata { { "password", "your-server-password" } };
         var options = new CallOptions(headers: headers);

         var client = new Health.HealthClient(channel);
         var resp = client.Check(new HealthCheckRequest(), options);

         Console.WriteLine($"Status: {resp.Status}");
         await channel.ShutdownAsync();

Next steps
~~~~~~~~~~

Now that you understand the basic connection pattern, follow
:doc:`../user_guide/build_a_client` for a step-by-step walkthrough that covers:

- Discovering available paths via the DataModel API schema and the Settings API schema
- Reading and writing state with the DataModel service and the Settings service
- Subscribing to live solver events

Or jump directly to a service reference:

- **Health service** (:doc:`../api/services/health`): verify server readiness
- **DataModel service** (:doc:`../api/services/datamodel_se`): read/write object-model state
- **Settings service** (:doc:`../api/services/settings`): read/write solver configuration
- **Events service** (:doc:`../api/services/events`): stream solver lifecycle events
- **Field Data service** (:doc:`../api/services/field_data`): retrieve simulation field data
- **ApplicationRuntime service** (:doc:`../api/services/app_utilities`): version, journal, app mode

Common errors and solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**ImportError**
   The ``ansys-api-fluent`` package is not installed in your Python environment.
   
   *Solution:* Install the package with ``pip install ansys-api-fluent``

**UNAVAILABLE**
   Wrong host/port, server not running, or network issues.
   
   *Solution:* Verify server address, ensure it's running, check network connectivity

**Authentication Failure**
   Wrong password or missing metadata.
   
   *Solution:* Verify password and ensure each RPC includes ``metadata=[("password", PASSWORD)]``

**DEADLINE_EXCEEDED**
   The timeout was too short for the operation.
   
   *Solution:* Increase the timeout, especially for large field data requests
