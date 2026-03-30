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
       app_utilities_pb2.GetProductVersionRequest(),
       metadata=metadata,
       timeout=5.0
   )
   print(f"Version: {response.major}.{response.minor}.{response.patch}")

GetBuildInfo
------------

Get detailed build information.

.. code-block:: python

   response = app_stub.GetBuildInfo(
       app_utilities_pb2.GetBuildInfoRequest(),
       metadata=metadata,
       timeout=5.0
   )
   print(f"Build Time: {response.build_time}")
   print(f"Build ID: {response.build_id}")
   print(f"VCS Revision: {response.vcs_revision}")
   print(f"VCS Branch: {response.vcs_branch}")

GetAppMode
----------

Check the current application mode (meshing, solver, etc.).

.. code-block:: python

   response = app_stub.GetAppMode(
       app_utilities_pb2.GetAppModeRequest(),
       metadata=metadata,
       timeout=5.0
   )
   print(f"Mode: {response.app_mode}")

The ``app_mode`` field in the response is an ``AppMode`` enum value. Use the
following map to interpret it:

.. list-table:: AppMode enum values
   :header-rows: 1
   :widths: 10 35 55

   * - Value
     - Enum constant
     - Description
   * - ``0``
     - ``APP_MODE_UNSPECIFIED``
     - Unspecified application mode.
   * - ``1``
     - ``APP_MODE_MESHING``
     - Meshing mode.
   * - ``2``
     - ``APP_MODE_SOLVER``
     - Solver mode.
   * - ``3``
     - ``APP_MODE_SOLVER_ICING``
     - Solver icing mode.
   * - ``4``
     - ``APP_MODE_SOLVER_AERO``
     - Solver aero mode.

Example usage with the map:

.. code-block:: python

   from ansys.api.fluent.v1 import app_utilities_pb2

   APP_MODE_MAP = {
       app_utilities_pb2.APP_MODE_UNSPECIFIED: "Unspecified",
       app_utilities_pb2.APP_MODE_MESHING: "Meshing",
       app_utilities_pb2.APP_MODE_SOLVER: "Solver",
       app_utilities_pb2.APP_MODE_SOLVER_ICING: "Solver Icing",
       app_utilities_pb2.APP_MODE_SOLVER_AERO: "Solver Aero",
   }

   response = app_stub.GetAppMode(
       app_utilities_pb2.GetAppModeRequest(),
       metadata=metadata,
       timeout=5.0,
   )
   print(f"Mode: {APP_MODE_MAP.get(response.app_mode, 'Unknown')}")

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

   APP_MODE_MAP = {
       app_utilities_pb2.APP_MODE_UNSPECIFIED: "Unspecified",
       app_utilities_pb2.APP_MODE_MESHING: "Meshing",
       app_utilities_pb2.APP_MODE_SOLVER: "Solver",
       app_utilities_pb2.APP_MODE_SOLVER_ICING: "Solver Icing",
       app_utilities_pb2.APP_MODE_SOLVER_AERO: "Solver Aero",
   }

   def get_app_info():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = app_utilities_pb2_grpc.AppUtilitiesStub(channel)

       try:
           # Get version
           version_response = stub.GetProductVersion(
               app_utilities_pb2.GetProductVersionRequest(),
               metadata=metadata,
               timeout=5.0,
           )
           print(f"Fluent Version: {version_response.major}.{version_response.minor}.{version_response.patch}")

           # Get build info
           build_response = stub.GetBuildInfo(
               app_utilities_pb2.GetBuildInfoRequest(),
               metadata=metadata,
               timeout=5.0,
           )
           print(f"Build Time: {build_response.build_time}")
           print(f"Build ID: {build_response.build_id}")
           print(f"VCS Revision: {build_response.vcs_revision}")
           print(f"VCS Branch: {build_response.vcs_branch}")

           # Get app mode and resolve via map
           mode_response = stub.GetAppMode(
               app_utilities_pb2.GetAppModeRequest(),
               metadata=metadata,
               timeout=5.0,
           )
           print(f"Application Mode: {APP_MODE_MAP.get(mode_response.app_mode, 'Unknown')}")

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
