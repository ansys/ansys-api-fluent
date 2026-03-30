App Utilities Service
=====================

The App Utilities service provides access to Fluent application-level operations and information.

Overview
~~~~~~~~

The ``AppUtilities`` service gives you access to:

- Product version and build information
- Application mode information
- Python journal operations
- Beta feature management
- Solution data availability checks
- Working directory management

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.app_utilities``

**Main Classes:**

- ``AppUtilitiesStub``: Client stub for application operations

Core RPC Operations
~~~~~~~~~~~~~~~~~~~

GetProductVersion
------------------

Retrieve the Fluent product version information.

.. code-block:: python

   response = app_stub.GetProductVersion(
       app_utilities_pb2.ProductVersionRequest(),
       metadata=metadata,
       timeout=5.0
   )
   print(f"Version: {response.version}")

GetBuildInfo
------------

Get detailed build information.

.. code-block:: python

   response = app_stub.GetBuildInfo(
       app_utilities_pb2.BuildInfoRequest(),
       metadata=metadata,
       timeout=5.0
   )

GetAppMode
----------

Check the current application mode (standalone, client, etc.).

.. code-block:: python

   response = app_stub.GetAppMode(
       app_utilities_pb2.AppModeRequest(),
       metadata=metadata,
       timeout=5.0
   )
   print(f"Mode: {response.mode}")

SetWorkingDirectory
-------------------

Set the working directory for Fluent operations.

.. code-block:: python

   request = app_utilities_pb2.SetWorkingDirectoryRequest(
       path="/path/to/working/directory"
   )
   response = app_stub.SetWorkingDirectory(
       request,
       metadata=metadata,
       timeout=10.0
   )

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import app_utilities_pb2, app_utilities_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def get_app_info():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = app_utilities_pb2_grpc.AppUtilitiesStub(channel)
       
       try:
           # Get version
           version_response = stub.GetProductVersion(
               app_utilities_pb2.ProductVersionRequest(),
               metadata=metadata,
               timeout=5.0
           )
           print(f"Fluent Version: {version_response.version}")
           
           # Get build info
           build_response = stub.GetBuildInfo(
               app_utilities_pb2.BuildInfoRequest(),
               metadata=metadata,
               timeout=5.0
           )
           print(f"Build: {build_response}")
           
           # Get app mode
           mode_response = stub.GetAppMode(
               app_utilities_pb2.AppModeRequest(),
               metadata=metadata,
               timeout=5.0
           )
           print(f"Application Mode: {mode_response.mode}")
           
       except grpc.RpcError as err:
           print(f"Error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       get_app_info()

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`health` - Health service for connectivity checks
