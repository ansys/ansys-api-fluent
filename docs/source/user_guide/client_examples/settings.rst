Settings service
=================

Python client examples for the ``Settings`` gRPC service.

See :doc:`../../api/services/settings`
for this service's complete reference material.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   channel = grpc.insecure_channel(
       "<server-address>",
       options=[
           # Defaults are 4 MiB receive / unlimited send. Raise the receive
           # cap so large responses (e.g. GetSchema) don't fail with 
           # RESOURCE_EXHAUSTED.       
           ("grpc.max_receive_message_length", 32 * 1024 * 1024),
       ],
   )
   metadata = [("password", "<password>")]
   stub = settings_pb2_grpc.SettingsStub(channel)

Every RPC addresses a settings node via a ``PathInfo`` message; pass
``root="fluent"`` and a slash-separated ``path`` for the Fluent solver.

.. code-block:: python
   :caption: Python

   def path(p: str) -> settings_pb2.PathInfo:
       return settings_pb2.PathInfo(root="fluent", path=p)

Discovering the schema
-----------------------

``GetSchema`` returns the static tree of objects, commands, and queries — walk
it to confirm valid paths before making runtime calls.

.. code-block:: python
   :caption: Python

   schema_response = stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent"),
       metadata=metadata,
   )
   print(schema_response.info.type)           # -> 'group'
   print(len(schema_response.info.children))  # -> 10  (number of top-level nodes)

   def walk(node, indent=0):
       prefix = "  " * indent
       for child in node.children:
           print(f"{prefix}{child.name}/")
           walk(child.value, indent + 1)
       for cmd in node.commands:
           print(f"{prefix}{cmd.name}()")
       for qry in node.queries:
           print(f"{prefix}{qry.name}?")

   walk(schema_response.info)

   # Request only specific attributes on a sub-tree.
   schema_response = stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent", optional_attrs=["type"]),
       metadata=metadata,
   )
   assert schema_response.info is not None

.. raw:: html

   <details>
   <summary style="cursor:pointer;user-select:none;font-weight:bold;padding:4px 0">
    Schema output (click to expand)
   </summary>
   <pre style="background:#2b2b2b;color:#f8f8f2;border:1px solid #444;border-radius:4px;padding:12px;margin-top:6px;overflow:auto;font-size:0.85em;line-height:1.5">
   file/
   mesh/
   server/
   setup/
     general/
       solver/
       operating-conditions/
         operating-pressure
         gravity/
         ...
     models/
       energy/
         enabled
         ...
       viscous/
       ...
     materials/
     boundary-conditions/
       wall/
       ...
     cell-zone-conditions/
     ...
   solution/
     methods/
     controls/
     report-definitions/
     monitor/
     run-calculation/
       iterate()
       ...
     ...
   results/
     graphics/
       contour/
       lighting/
         lights/
       ...
     ...
   ...
   exit()
   switch-to-meshing-mode()
   get-modified-state?
   </pre>
   </details>

Reading and writing state
--------------------------

``GetState`` returns a ``Value`` carrying one active ``oneof`` field; call
``WhichOneof("value")`` to identify it before accessing it.

.. code-block:: python
   :caption: Python

   def value_to_python(v):
       kind = v.WhichOneof("value")
       if kind == "boolean":   return v.boolean
       if kind == "integer":   return v.integer
       if kind == "real":      return v.real
       if kind == "string":    return v.string
       if kind == "value_list": return [value_to_python(i) for i in v.value_list.lsts]
       if kind == "value_map":  return {k: value_to_python(val) for k, val in v.value_map.m.items()}
       return None

   # Read a scalar parameter.
   state_response = stub.GetState(
       settings_pb2.GetStateRequest(
           path_info=path("/setup/general/operating-conditions/operating-pressure")
       ),
       metadata=metadata,
   )
   print(value_to_python(state_response.value))  # -> 101325.0

   # Read the energy model map.
   state_response = stub.GetState(
       settings_pb2.GetStateRequest(path_info=path("/setup/models/energy")),
       metadata=metadata,
   )
   print(value_to_python(state_response.value))  # -> {'enabled': True, 'viscous-dissipation': False, ...}

``SetState`` writes a ``Value`` back; the integer roundtrip below confirms the
write is reflected by a subsequent ``GetState``.

.. code-block:: python
   :caption: Python

   path_info = path("/setup/general/operating-conditions/operating-pressure")

   # Read original value.
   orig = stub.GetState(
       settings_pb2.GetStateRequest(path_info=path_info),
       metadata=metadata,
   ).value

   # Write a new value.
   stub.SetState(
       settings_pb2.SetStateRequest(
           path_info=path_info,
           value=settings_pb2.Value(integer=101000),
       ),
       metadata=metadata,
   )

   # Confirm the change.
   check = stub.GetState(
       settings_pb2.GetStateRequest(path_info=path_info),
       metadata=metadata,
   )
   print(value_to_python(check.value))  # -> 101000

   # Restore original.
   stub.SetState(
       settings_pb2.SetStateRequest(path_info=path_info, value=orig),
       metadata=metadata,
   )

Querying attributes
--------------------

``GetAttrs`` returns type, active status, and read-only flag without a prior
``GetSchema`` call; pass ``recursive=True`` to include child nodes.

.. code-block:: python
   :caption: Python

   # Read specific attributes for a single node.
   attrs_response = stub.GetAttrs(
       settings_pb2.GetAttrsRequest(
           path_info=path("/setup/models/energy/enabled"),
           attrs=["type", "active?", "read-only?"],
           recursive=False,
       ),
       metadata=metadata,
   )
   assert attrs_response.values.WhichOneof("value") == "value_map"
   for attr, val in attrs_response.values.value_map.m.items():
       print(f"{attr}: {value_to_python(val)}")
   # 'type': 'boolean', 'active?': True, 'read-only?': False

   # Recursive read — populates group_children for every child node.
   attrs_response = stub.GetAttrs(
       settings_pb2.GetAttrsRequest(
           path_info=path("/setup/models"),
           attrs=["type"],
           recursive=True,
       ),
       metadata=metadata,
   )
   print(len(attrs_response.group_children))  # -> > 4

Managing named objects
-----------------------

Use ``CreateObject``, ``GetObjectNames``, ``Rename``, and ``DeleteObject`` to
manage collections such as graphics contours under ``/results/graphics/contour``.

.. code-block:: python
   :caption: Python

   OBJ_PATH = path("/results/graphics/contour")

   # Create two contour objects.
   stub.CreateObject(
       settings_pb2.CreateObjectRequest(path_info=OBJ_PATH, name="contour-1"),
       metadata=metadata,
   )
   stub.CreateObject(
       settings_pb2.CreateObjectRequest(path_info=OBJ_PATH, name="contour-2"),
       metadata=metadata,
   )

   # List all names.
   objects = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(path_info=OBJ_PATH),
       metadata=metadata,
   )
   print(list(objects.names))  # -> ['contour-1', 'contour-2']

   # Rename contour-1.
   stub.Rename(
       settings_pb2.RenameRequest(
           path_info=OBJ_PATH,
           old_name="contour-1",
           new_name="contour-renamed",
       ),
       metadata=metadata,
   )

   objects = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(path_info=OBJ_PATH),
       metadata=metadata,
   )
   print(list(objects.names))  # -> ['contour-renamed', 'contour-2']

   # Delete both objects.
   for name in ("contour-renamed", "contour-2"):
       stub.DeleteObject(
           settings_pb2.DeleteObjectRequest(path_info=OBJ_PATH, name=name),
           metadata=metadata,
       )

   objects = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(path_info=OBJ_PATH),
       metadata=metadata,
   )
   print(list(objects.names))  # -> []

``GetObjectNames`` works on any named-object path, including boundary
conditions; ``GetListSize`` returns the current count for list settings.

.. code-block:: python
   :caption: Python

   # Named objects under a boundary-condition path.
   objects = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(
           path_info=path("/setup/boundary-conditions/wall")
       ),
       metadata=metadata,
   )
   print(list(objects.names))  # -> ['wall', ...]  (names of existing wall BCs)

   # Size of a list setting.
   list_size_response = stub.GetListSize(
       settings_pb2.GetListSizeRequest(
           path_info=path("/results/graphics/lighting/lights")
       ),
       metadata=metadata,
   )
   print(list_size_response.size)  # -> 0  (or more if lights have been configured)

Executing commands
-------------------

``ExecuteCommand`` performs a state-mutating action; pass arguments as a
``Value`` message.

.. code-block:: python
   :caption: Python

   command_response = stub.ExecuteCommand(
       settings_pb2.ExecuteCommandRequest(
           path_info=path("/solution/run-calculation"),
           command="iterate",
           args=settings_pb2.Value(
               value_map=settings_pb2.Value.ValueMap(
                   m={"number-of-iterations": settings_pb2.Value(integer=0)}
               )
           ),
       ),
       metadata=metadata,
   )
   assert hasattr(command_response, "reply")

Executing queries
------------------

``ExecuteQuery`` returns a computed result without side effects.

.. code-block:: python
   :caption: Python

   query_response = stub.ExecuteQuery(
       settings_pb2.ExecuteQueryRequest(
           path_info=path("/setup/models/system-coupling"),
           query="get-tensor-type",
           args=settings_pb2.Value(),
       ),
       metadata=metadata,
   )
   print(value_to_python(query_response.reply))  # -> 'symmetric'  (or None)

Checking wildcards
-------------------

``IsWildcard`` tests whether a string will be treated as a wildcard before
passing it to other RPCs.

.. code-block:: python
   :caption: Python

   for token in ("*", "?", "cold-inlet", ""):
       wildcard_response = stub.IsWildcard(
           settings_pb2.IsWildcardRequest(input=token),
           metadata=metadata,
       )
       print(f"{token!r:15} -> is_wildcard={wildcard_response.is_wildcard}")
   # '*'             -> is_wildcard=True
   # '?'             -> is_wildcard=True  (or False, depending on Fluent version)
   # 'cold-inlet'    -> is_wildcard=False
   # ''              -> is_wildcard=False

See :doc:`../../api/services/settings` for the complete reference material.
