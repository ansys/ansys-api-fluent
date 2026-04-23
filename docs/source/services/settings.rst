Settings
========

The Settings service provides hierarchical access to Fluent simulation configuration,
including problem setup, solver parameters, boundary conditions, and case settings.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``Settings`` service allows you to:

- Query the settings hierarchy structure and metadata
- Retrieve and modify configuration values (scalars, strings, lists, maps)
- Create, rename, and delete named objects (boundary conditions, etc.)
- Manage list objects (resizing, querying size)
- Execute commands and queries on settings objects
- Access object attributes with optional recursive retrieval

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.settings``

**Main Classes:**

- ``SettingsStub``: Client stub for settings operations
- ``PathInfo``: Specifies root and path to a settings object
- ``Value``: Container for typed settings values (oneof: bool, int64, double, string, list, map)
- ``StaticInfo``: Metadata about settings objects (type, children, commands, queries, help)

Core RPC Operations
~~~~~~~~~~~~~~~~~~~

Hierarchy and Metadata Discovery
---------------------------------

Query the settings structure and object metadata.

- ``GetStaticInfo(GetStaticInfoRequest)`` → ``StaticInfo``
  Request fields: ``root: string``, ``optional_attrs: repeated string``

Getting and Setting Values
---------------------------

Retrieve and modify typed configuration values.

- ``GetVar(GetVarRequest)`` → ``GetVarResponse``
  Request field: ``path_info: PathInfo``
- ``SetVar(SetVarRequest)`` → ``SetVarResponse``
  Request fields: ``path_info: PathInfo``, ``value: Value``

Example: retrieve and modify operating pressure setting

.. code-block:: python

   # Get current operating pressure
   get_resp = stub.GetVar(
       settings_pb2.GetVarRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure"
           )
       ),
       metadata=metadata,
       timeout=10.0,
   )
   
   # Extract the value (could be bool, int, string, or nested)
   current_pressure = get_resp.value
   if current_pressure.WhichOneof("value") == "integer":
       print(f"Current operating pressure: {current_pressure.integer}")

   # Set operating pressure to a new value
   set_resp = stub.SetVar(
       settings_pb2.SetVarRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure"
           ),
           value=settings_pb2.Value(integer=101329)
       ),
       metadata=metadata,
       timeout=10.0,
   )

Object Creation, Deletion, and Renaming
----------------------------------------

Manage named objects in the settings hierarchy.

- ``Create(CreateRequest)`` → ``CreateResponse``
  Request fields: ``path_info: PathInfo``, ``name: string``
- ``Delete(DeleteRequest)`` → ``DeleteResponse``
  Request fields: ``path_info: PathInfo``, ``name: string``
- ``Rename(RenameRequest)`` → ``RenameResponse``
  Request fields: ``path_info: PathInfo``, ``old_name: string``, ``new_name: string``

Example: create a new contour, rename it, and then delete it

.. code-block:: python

   # Create a new contour named "contour-1"
   create_resp = stub.Create(
       settings_pb2.CreateRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="results/graphics/contour"
           ),
           name="contour-1"
       ),
       metadata=metadata,
       timeout=10.0,
   )

   # Rename the contour to "contour-renamed"
   rename_resp = stub.Rename(
       settings_pb2.RenameRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="results/graphics/contour"
           ),
           old_name="contour-1",
           new_name="contour-renamed"
       ),
       metadata=metadata,
       timeout=10.0,
   )

   # Delete the contour
   delete_resp = stub.Delete(
       settings_pb2.DeleteRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="results/graphics/contour"
           ),
           name="contour-renamed"
       ),
       metadata=metadata,
       timeout=10.0,
   )

Object and List Queries
-----------------------

Query object names and list sizes.

- ``GetObjectNames(GetObjectNamesRequest)`` → ``GetObjectNamesResponse``
  Request field: ``path_info: PathInfo``
- ``GetListSize(GetListSizeRequest)`` → ``GetListSizeResponse``
  Request field: ``path_info: PathInfo``
- ``ResizeListObject(ResizeListObjectRequest)`` → ``ResizeListObjectResponse``
  Request fields: ``path_info: PathInfo``, ``size: int32``

Example: enumerate boundary conditions and check list sizes

.. code-block:: python

   # Get all wall boundary condition names
   names_resp = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/boundary-conditions/wall"
           )
       ),
       metadata=metadata,
       timeout=10.0,
   )

   print(f"Wall BCs: {names_resp.names}")

   # Get size of lights list
   size_resp = stub.GetListSize(
       settings_pb2.GetListSizeRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="results/graphics/lighting/lights"
           )
       ),
       metadata=metadata,
       timeout=10.0,
   )

   print(f"Lights list size: {size_resp.size}")

   # Resize to 10 elements
   resize_resp = stub.ResizeListObject(
       settings_pb2.ResizeListObjectRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="results/graphics/lighting/lights"
           ),
           size=10
       ),
       metadata=metadata,
       timeout=10.0,
   )

Commands and Queries
--------------------

Execute commands and queries on settings objects.

- ``ExecuteCommand(ExecuteCommandRequest)`` → ``ExecuteCommandResponse``
  Request fields: ``path_info: PathInfo``, ``command: string``, ``args: Value``
- ``ExecuteQuery(ExecuteQueryRequest)`` → ``ExecuteQueryResponse``
  Request fields: ``path_info: PathInfo``, ``query: string``, ``args: Value``

Example: execute a command and query

.. code-block:: python

   # Execute a command (e.g., reset to defaults)
   cmd_resp = stub.ExecuteCommand(
       settings_pb2.ExecuteCommandRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="solution/run-calculation"
           ),
           command="iterate",
       ),
       metadata=metadata,
       timeout=10.0,
   )

   # Execute a query (e.g., validate settings)
   query_resp = stub.ExecuteQuery(
       settings_pb2.ExecuteQueryRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/models/system-coupling"
           ),
           query="get-tensor-type",
       ),
       metadata=metadata,
       timeout=10.0,
   )

   # Check query result
   if query_resp.reply.WhichOneof("value") == "string":
       print(f"Tensor type: {query_resp.reply.string}")

Attribute Access
----------------

Retrieve attributes from settings objects.

- ``GetAttrs(GetAttrsRequest)`` → ``GetAttrsResponse``
  Request fields: ``path_info: PathInfo``, ``attrs: repeated string``, ``recursive: bool``

Example: retrieve object attributes

.. code-block:: python

   response = stub.GetAttrs(
       settings_pb2.GetAttrsRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/models/energy"
           ),
           attrs=["type", "active?", "read-only?"],
           recursive=False
       ),
       metadata=metadata,
       timeout=10.0,
   )

   # response.values contains the attribute data
   attrs_value = response.values
   if attrs_value.WhichOneof("value") == "value_map":
       for key, val in attrs_value.value_map.m.items():
           print(f"{key}: {val}")

Working with Value Results
~~~~~~~~~~~~~~~~~~~~~~~~~~

Settings RPCs return ``Value`` objects which use a ``oneof`` to hold one active type.
Use this helper to convert ``Value`` to native Python types.

.. code-block:: python

   def value_to_python(v):
       kind = v.WhichOneof("value")
       if kind == "boolean":
           return v.boolean
       if kind == "integer":
           return v.integer
       if kind == "real":
           return v.real
       if kind == "string":
           return v.string
       if kind == "value_list":
           return [value_to_python(item) for item in v.value_list.lsts]
       if kind == "value_map":
           return {key: value_to_python(val) for key, val in v.value_map.m.items()}
       return None

Complete Example
~~~~~~~~~~~~~~~~

An end-to-end workflow demonstrating hierarchy discovery, value retrieval/modification,
object management, and command execution.

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def value_to_python(v):
       kind = v.WhichOneof("value")
       if kind == "boolean":
           return v.boolean
       if kind == "integer":
           return v.integer
       if kind == "real":
           return v.real
       if kind == "string":
           return v.string
       if kind == "value_list":
           return [value_to_python(item) for item in v.value_list.lsts]
       if kind == "value_map":
           return {key: value_to_python(val) for key, val in v.value_map.m.items()}
       return None

   def run_settings_workflow():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = settings_pb2_grpc.SettingsServiceStub(channel)

       try:
           # Step 1: Query and display current settings
           print("\n=== Query Current Settings ===")
           dim_resp = stub.GetVar(
               settings_pb2.GetVarRequest(
                   path_info=settings_pb2.PathInfo(
                       root="fluent",
                       path="setup/general/operating-conditions/operating-pressure"
                   )
               ),
               metadata=metadata,
               timeout=10.0,
           )
           print(f"Dimension: {value_to_python(dim_resp.value)}")

           # Step 2: Modify a setting
           print("\n=== Modify Setting ===")
           set_resp = stub.SetVar(
               settings_pb2.SetVarRequest(
                   path_info=settings_pb2.PathInfo(
                       root="fluent",
                       path="setup/general/operating-conditions/operating-pressure"
                   ),
                   value=settings_pb2.Value(integer=101325)
               ),
               metadata=metadata,
               timeout=10.0,
           )
           print("Operating pressure set to 101325 Pa")

           # Step 3: Manage boundary conditions
           print("\n=== Manage Boundary Conditions ===")
           names_resp = stub.GetObjectNames(
               settings_pb2.GetObjectNamesRequest(
                   path_info=settings_pb2.PathInfo(
                       root="fluent",
                       path="setup/boundary-conditions/wall"
                   )
               ),
               metadata=metadata,
               timeout=10.0,
           )
           print(f"Existing walls: {names_resp.names}")

           # Step 4: Execute a command
           print("\n=== Execute Command ===")
           cmd_resp = stub.ExecuteCommand(
               settings_pb2.ExecuteCommandRequest(
                   path_info=settings_pb2.PathInfo(
                       root="fluent",
                       path="solution/run-calculation"
                   ),
                   command="iterate",
                   args=settings_pb2.Value()
               ),
               metadata=metadata,
               timeout=10.0,
           )
           print("Iteration command executed")

           # Create a contour object to demonstrate create/rename/delete
           create_resp = stub.Create(
               settings_pb2.CreateRequest(
                   path_info=settings_pb2.PathInfo(
                       root="fluent",
                       path="results/graphics/contour"
                   ),
                   name="contour-1"
               ),
               metadata=metadata,
               timeout=10.0,
           )
           print("Created contour: contour-1")

           # Rename it
           rename_resp = stub.Rename(
               settings_pb2.RenameRequest(
                   path_info=settings_pb2.PathInfo(
                       root="fluent",
                       path="results/graphics/contour"
                   ),
                   old_name="contour-1",
                   new_name="contour-renamed"
               ),
               metadata=metadata,
               timeout=10.0,
           )
           print("Renamed to: contour-renamed")

           # Cleanup: Delete the contour we created
           delete_resp = stub.Delete(
               settings_pb2.DeleteRequest(
                   path_info=settings_pb2.PathInfo(
                       root="fluent",
                       path="results/graphics/contour"
                   ),
                   name="contour-renamed"
               ),
               metadata=metadata,
               timeout=10.0,
           )
           print("Deleted contour: contour-renamed")

           print("\n=== Workflow Complete ===")

       except grpc.RpcError as err:
           print(f"Error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       run_settings_workflow()

Best Practices
~~~~~~~~~~~~~~

1. **Always use root="fluent"** - The root is always the literal string ``"fluent"``, not a path like ``/setup``.
2. **Use hierarchical paths** - Provide the full path in the ``path`` field, e.g., ``"setup/general/dimension"`` or ``"setup/boundary-conditions/wall"``.
3. **Decode Value types defensively** - Always check ``WhichOneof("value")`` before accessing a Value field to handle bool, int, float, string, list, or map types correctly.
4. **Use GetObjectNames to list children** - When managing named objects (e.g., boundary conditions), use GetObjectNames to enumerate existing names before creating new ones.
5. **Batch related modifications** - Group related SetVar calls to reduce round trips when configuring related settings.
6. **Set practical timeouts** - Complex hierarchy queries or large object operations may need longer RPC timeouts (15+ seconds).

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`datamodel_se` - Datamodel service for mesh and field-related settings
