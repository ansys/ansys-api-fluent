Settings
========

Overview
--------

The ``Settings`` service provides hierarchical read/write access to Fluent's
simulation configuration - boundary conditions, solver controls, model
parameters, and results settings. Every RPC addresses a settings node by a
``PathInfo`` message that contains two fields: ``root``, a string that selects
which part of the Settings API you are working with (the common value is
``"fluent"``), and ``path``, a slash-separated location within that root such
as ``setup/boundary-conditions/wall``.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = settings_pb2_grpc.SettingsStub(channel)

Runtime API
-----------

Getting and setting values
~~~~~~~~~~~~~~~~~~~~~~~~~~

Read and write typed configuration values. The ``Value`` message uses a
``oneof`` to hold one active type - always call ``WhichOneof("value")`` on a
returned ``Value`` before accessing it.

- ``GetVar(GetVarRequest)`` → ``GetVarResponse``
  Request field: ``path_info: PathInfo``
- ``SetVar(SetVarRequest)`` → ``SetVarResponse``
  Request fields: ``path_info: PathInfo``, ``value: Value``

.. code-block:: python
   :caption: Python

   get_resp = stub.GetVar(
       settings_pb2.GetVarRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           )
       ),
       metadata=metadata,
   )
   if get_resp.value.WhichOneof("value") == "real":
       print("Operating pressure:", get_resp.value.real)

   stub.SetVar(
       settings_pb2.SetVarRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           ),
           value=settings_pb2.Value(real=101325.0),
       ),
       metadata=metadata,
   )

Object lifecycle
~~~~~~~~~~~~~~~~

Create, rename, and delete named objects such as boundary conditions or
graphics objects.

- ``Create(CreateRequest)`` → ``CreateResponse``
  Request fields: ``path_info: PathInfo``, ``name: string``
- ``Delete(DeleteRequest)`` → ``DeleteResponse``
  Request fields: ``path_info: PathInfo``, ``name: string``
- ``Rename(RenameRequest)`` → ``RenameResponse``
  Request fields: ``path_info: PathInfo``, ``old_name: string``, ``new_name: string``

.. code-block:: python
   :caption: Python

   stub.Create(
       settings_pb2.CreateRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="results/graphics/contour"),
           name="contour-1",
       ),
       metadata=metadata,
   )
   stub.Rename(
       settings_pb2.RenameRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="results/graphics/contour"),
           old_name="contour-1",
           new_name="contour-renamed",
       ),
       metadata=metadata,
   )
   stub.Delete(
       settings_pb2.DeleteRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="results/graphics/contour"),
           name="contour-renamed",
       ),
       metadata=metadata,
   )

Object and list queries
~~~~~~~~~~~~~~~~~~~~~~~

Enumerate existing named objects and inspect or resize list-typed settings.

- ``GetObjectNames(GetObjectNamesRequest)`` → ``GetObjectNamesResponse``
  Request field: ``path_info: PathInfo``
- ``GetListSize(GetListSizeRequest)`` → ``GetListSizeResponse``
  Request field: ``path_info: PathInfo``
- ``ResizeListObject(ResizeListObjectRequest)`` → ``ResizeListObjectResponse``
  Request fields: ``path_info: PathInfo``, ``size: int32``

.. code-block:: python
   :caption: Python

   names_resp = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/boundary-conditions/wall")
       ),
       metadata=metadata,
   )
   print("Wall boundary conditions:", names_resp.names)

   size_resp = stub.GetListSize(
       settings_pb2.GetListSizeRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="results/graphics/lighting/lights")
       ),
       metadata=metadata,
   )
   print("Lights list size:", size_resp.size)

Commands and queries
~~~~~~~~~~~~~~~~~~~~

Execute actions and ask computed questions on settings objects.
``ExecuteCommand`` performs a state-mutating action; ``ExecuteQuery`` returns a
computed result without side effects.

- ``ExecuteCommand(ExecuteCommandRequest)`` → ``ExecuteCommandResponse``
  Request fields: ``path_info: PathInfo``, ``command: string``, ``args: Value``
- ``ExecuteQuery(ExecuteQueryRequest)`` → ``ExecuteQueryResponse``
  Request fields: ``path_info: PathInfo``, ``query: string``, ``args: Value``

.. code-block:: python
   :caption: Python

   stub.ExecuteCommand(
       settings_pb2.ExecuteCommandRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="solution/run-calculation"),
           command="iterate",
       ),
       metadata=metadata,
   )

   query_resp = stub.ExecuteQuery(
       settings_pb2.ExecuteQueryRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/models/system-coupling"),
           query="get-tensor-type",
       ),
       metadata=metadata,
   )
   if query_resp.reply.WhichOneof("value") == "string":
       print("Tensor type:", query_resp.reply.string)

Attribute access
~~~~~~~~~~~~~~~~

Retrieve named attributes - for example, type, active status, or read-only
status - from a settings object.

- ``GetAttrs(GetAttrsRequest)`` → ``GetAttrsResponse``
  Request fields: ``path_info: PathInfo``, ``attrs: repeated string``, ``recursive: bool``

.. code-block:: python
   :caption: Python

   attrs_resp = stub.GetAttrs(
       settings_pb2.GetAttrsRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/models/energy"),
           attrs=["type", "active?", "read-only?"],
           recursive=False,
       ),
       metadata=metadata,
   )
   if attrs_resp.values.WhichOneof("value") == "value_map":
       for key, val in attrs_resp.values.value_map.m.items():
           print(f"{key}: {val}")

Wildcard detection
~~~~~~~~~~~~~~~~~~

``IsWildcard`` checks whether the solver application treats a given string as
a wildcard pattern. This is useful when building path queries that accept
wildcard syntax.

- ``IsWildcard(IsWildcardRequest)`` → ``IsWildcardResponse``
  Request field: ``input: string``
  Response field: ``is_wildcard: bool``

.. code-block:: python
   :caption: Python

   wc_resp = stub.IsWildcard(
       settings_pb2.IsWildcardRequest(input="wall-*"),
       metadata=metadata,
   )
   print(f"'wall-*' is wildcard: {wc_resp.is_wildcard}")

API schema
----------

``GetSchema`` returns the API schema for the Settings service - a complete
description of the paths, object types, available commands, queries, and help
text that exist for a given root, independent of any running simulation.

Use it when you need to enumerate what is available programmatically - for
example, to discover which commands exist before calling ``ExecuteCommand``, or
to build a higher-level settings client. See :doc:`../build_a_client` for a
step-by-step walkthrough of schema discovery.

- ``GetSchema(GetSchemaRequest)`` → ``GetSchemaResponse``
  Request fields: ``root: string``, ``optional_attrs: repeated string``
  Response field: ``info: Schema``

.. code-block:: python
   :caption: Python

   schema_resp = stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent"),
       metadata=metadata,
   )
   schema = schema_resp.info
   print("Top-level children:", [c.name for c in schema.children])
   print("Top-level commands:", [c.name for c in schema.commands])

.. ----------------------------------------------------------------------------
.. The block below is generated by docs/_ext/proto_docgen.py from the matching
.. .proto file in ansys/api/fluent/v1. Edit the proto comments to update it.
.. ----------------------------------------------------------------------------
