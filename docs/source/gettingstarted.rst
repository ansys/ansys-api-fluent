Getting started
===============

This guide shows how to use the packaged Python gRPC interface in ``ansys-api-fluent`` 
to connect to a Fluent v1 gRPC server and call services directly.

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

Typical imports look like:

.. code-block:: python

   from ansys.api.fluent.v1 import field_data_pb2
   from ansys.api.fluent.v1 import field_data_pb2_grpc
   from ansys.api.fluent.v1 import health_pb2
   from ansys.api.fluent.v1 import health_pb2_grpc

Prerequisites
~~~~~~~~~~~~~

Before writing a client, you need:

- Python 3.10 or later
- A running v1 gRPC server
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

Next steps
~~~~~~~~~~

Now that you understand the basic pattern, explore the :doc:`services` to learn about:

- **Health Service** (:doc:`services/health`): Monitor server status
- **Field Data Service** (:doc:`services/field_data`): Retrieve simulation field data
- **App Utilities** (:doc:`services/app_utilities`): Access Fluent application settings
- Other specialized services for your use case

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
