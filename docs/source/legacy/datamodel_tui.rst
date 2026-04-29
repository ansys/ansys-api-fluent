TextInterface
=============

The ``TextInterface`` service provides structured access to Fluent's TUI datamodel.
You can use it to query the command hierarchy, retrieve documentation, and execute commands.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``TextInterface`` service allows you to:

- Retrieve child node names at a path
- Get documentation strings for nodes
- Execute TUI commands and queries
- Retrieve schema-like static information for menus and commands

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.datamodel_tui``

**Main Classes:**

- ``TextInterfaceStub``: gRPC client stub for TUI datamodel operations
- ``google.protobuf.Value``: Dynamic value container for response payloads
- ``google.protobuf.Struct``: Dynamic key/value container for command arguments
- ``StaticInfo``: Menu/command metadata tree

Key concepts
~~~~~~~~~~~~

- ``path``: TUI datamodel path (for example, ``/mesh/auto-mesh-controls``).
- ``Value``: Generic typed container (null, bool, number, string, list, struct).
- ``Struct``: Named argument map used in command args.
- ``Attribute``: Enum used by ``GetAttributeValue`` to request specific metadata.

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Get child names
---------------

Retrieve the names of direct child nodes at a path.

- ``GetAttributeValue(GetAttributeValueRequest)`` -> ``GetAttributeValueResponse``
  Request fields: ``path: string``, ``attribute: ATTRIBUTE_CHILD_NAMES``

Example: get child names

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import datamodel_tui_pb2, datamodel_tui_pb2_grpc
   from google.protobuf import struct_pb2

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = datamodel_tui_pb2_grpc.TextInterfaceStub(channel)

   resp = stub.GetAttributeValue(
       datamodel_tui_pb2.GetAttributeValueRequest(
           path="/mesh",
           attribute=datamodel_tui_pb2.ATTRIBUTE_CHILD_NAMES,
           args=struct_pb2.Struct(),
       ),
       metadata=metadata,
   )
   print("Child names kind:", resp.value.WhichOneof("kind"))

Get doc string
--------------

Retrieve documentation/help text for a node.

- ``GetAttributeValue(GetAttributeValueRequest)`` -> ``GetAttributeValueResponse``
  Request fields: ``path: string``, ``attribute: ATTRIBUTE_HELP_STRING``

Example: get documentation string

.. code-block:: python

   doc_resp = stub.GetAttributeValue(
       datamodel_tui_pb2.GetAttributeValueRequest(
           path="/mesh",
           attribute=datamodel_tui_pb2.ATTRIBUTE_HELP_STRING,
           args=struct_pb2.Struct(),
       ),
       metadata=metadata,
   )
   print("Help text kind:", doc_resp.value.WhichOneof("kind"))

Execute commands and queries
----------------------------

Execute commands and query endpoints on TUI nodes.

- ``ExecuteCommand(ExecuteCommandRequest)`` -> ``ExecuteCommandResponse``
  Request fields: ``path: string``, ``command: string``, ``args: google.protobuf.Struct``
- ``ExecuteQuery(ExecuteQueryRequest)`` -> ``ExecuteQueryResponse``
  Request field: ``path: string``

Example: execute a command with structured args

.. code-block:: python

   cmd_resp = stub.ExecuteCommand(
       datamodel_tui_pb2.ExecuteCommandRequest(
           path="/mesh/",
           command="check-verbosity",
       ),
       metadata=metadata,
   )
   print("Command result kind:", cmd_resp.result.WhichOneof("kind"))

Example: execute a query

.. code-block:: python

   query_resp = stub.ExecuteQuery(
       datamodel_tui_pb2.ExecuteQueryRequest(
           path="/mesh/quality"
       ),
       metadata=metadata,
   )
   print("Query result kind:", query_resp.result.WhichOneof("kind"))

Get static info
---------------

Retrieve schema-like static information for menus and commands at a path.

- ``GetStaticInfo(GetStaticInfoRequest)`` -> ``GetStaticInfoResponse``
  Request field: ``path: string``

Example: retrieve static info for a subtree

.. code-block:: python

   static_resp = stub.GetStaticInfo(
       datamodel_tui_pb2.GetStaticInfoRequest(path="/mesh"),
       metadata=metadata,
   )
   print("Available menus:", list(static_resp.info.menus.keys()))
   print("Available commands:", list(static_resp.info.commands.keys()))

Get and set state
-----------------

Read or write the current state at any TUI datamodel path.

- ``GetState(GetStateRequest)`` → ``GetStateResponse``
  Request field: ``path: string``
  Response field: ``state: google.protobuf.Value``
- ``SetState(SetStateRequest)`` → ``SetStateResponse``
  Request fields: ``path: string``, ``state: google.protobuf.Value``
  Response field: ``state: google.protobuf.Value`` (value after server normalisation)

Example: read then write state

.. code-block:: python

   state_resp = stub.GetState(
       datamodel_tui_pb2.GetStateRequest(path="/mesh/auto-mesh-controls"),
       metadata=metadata,
   )
   print("Current state:", state_resp.state.WhichOneof("kind"))

   stub.SetState(
       datamodel_tui_pb2.SetStateRequest(
           path="/mesh/auto-mesh-controls/growth-rate",
           state=struct_pb2.Value(number_value=1.2),
       ),
       metadata=metadata,
   )

Subscribe to change notifications
---------------------------------

``NotifyChanges`` is a server-streaming RPC. The client sends one request
containing the paths to watch; the server streams ``NotifyChangesResponse``
messages as those paths change.

- ``NotifyChanges(NotifyChangesRequest)`` → ``stream NotifyChangesResponse``
  Request fields: ``paths: google.protobuf.Value``, ``args: google.protobuf.Struct``
  Response fields: ``changed_paths: google.protobuf.Value``, ``state_difference: google.protobuf.Value``

Example: watch a subtree for changes

.. code-block:: python

   stream = stub.NotifyChanges(
       datamodel_tui_pb2.NotifyChangesRequest(
           paths=struct_pb2.Value(
               list_value=struct_pb2.ListValue(
                   values=[struct_pb2.Value(string_value="/mesh")]
               )
           ),
           args=struct_pb2.Struct(),
       ),
       metadata=metadata,
   )
   for notification in stream:
       print("Changed paths kind:", notification.changed_paths.WhichOneof("kind"))
       print("Difference kind:", notification.state_difference.WhichOneof("kind"))

Batch attribute and state reads
--------------------------------

``CompositeGet`` batches multiple ``GetAttributeValue`` or ``GetState``
requests into a single round trip. Each element in ``getters`` is a
``DataModelGetter`` with exactly one of its oneof fields set:
``get_attribute_value_request`` or ``get_state_request``.

- ``CompositeGet(CompositeGetRequest)`` → ``CompositeGetResponse``
  Request field: ``getters: repeated DataModelGetter``
  Response field: ``response: google.protobuf.Value``

Example: fetch child names and state in one call

.. code-block:: python

   composite_resp = stub.CompositeGet(
       datamodel_tui_pb2.CompositeGetRequest(
           getters=[
               datamodel_tui_pb2.DataModelGetter(
                   get_attribute_value_request=datamodel_tui_pb2.GetAttributeValueRequest(
                       path="/mesh",
                       attribute=datamodel_tui_pb2.ATTRIBUTE_CHILD_NAMES,
                       args=struct_pb2.Struct(),
                   )
               ),
               datamodel_tui_pb2.DataModelGetter(
                   get_state_request=datamodel_tui_pb2.GetStateRequest(
                       path="/mesh/auto-mesh-controls",
                   )
               ),
           ]
       ),
       metadata=metadata,
   )
   print("Composite result kind:", composite_resp.response.WhichOneof("kind"))

Working with ``google.protobuf.Value``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The TUI datamodel API uses ``google.protobuf.Value`` for response payloads.

.. code-block:: python

   from google.protobuf import struct_pb2

   def python_to_value(obj):
       if obj is None:
           return struct_pb2.Value(null_value=0)
       if isinstance(obj, bool):
           return struct_pb2.Value(bool_value=obj)
       if isinstance(obj, (int, float)):
           return struct_pb2.Value(number_value=float(obj))
       if isinstance(obj, str):
           return struct_pb2.Value(string_value=obj)
       if isinstance(obj, list):
           return struct_pb2.Value(
               list_value=struct_pb2.ListValue(
                   values=[python_to_value(item) for item in obj]
               )
           )
       if isinstance(obj, dict):
           return struct_pb2.Value(
               struct_value=struct_pb2.Struct(
                   fields={k: python_to_value(v) for k, v in obj.items()}
               )
           )
       raise TypeError(f"Unsupported type: {type(obj)}")

   def value_to_python(v):
       kind = v.WhichOneof("kind")
       if kind == "null_value":
           return None
       if kind == "bool_value":
           return v.bool_value
       if kind == "number_value":
           return v.number_value
       if kind == "string_value":
           return v.string_value
       if kind == "list_value":
           return [value_to_python(item) for item in v.list_value.values]
       if kind == "struct_value":
           return {k: value_to_python(val) for k, val in v.struct_value.fields.items()}
       return None

Complete end-to-end example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates an end-to-end TUI datamodel workflow using the core methods:

1. Initialize client connection and stub
2. Retrieve child names at a path
3. Get documentation for a node
4. Execute a command
5. Execute a query
6. Retrieve static metadata

.. code-block:: python

   from __future__ import annotations
   import grpc
   from ansys.api.fluent.v1 import datamodel_tui_pb2, datamodel_tui_pb2_grpc
   from google.protobuf import struct_pb2

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def value_to_python(v):
       kind = v.WhichOneof("kind")
       if kind == "null_value":
           return None
       if kind == "bool_value":
           return v.bool_value
       if kind == "number_value":
           return v.number_value
       if kind == "string_value":
           return v.string_value
       if kind == "list_value":
           return [value_to_python(item) for item in v.list_value.values]
       if kind == "struct_value":
           return {k: value_to_python(val) for k, val in v.struct_value.fields.items()}
       return None

   def python_to_value(obj):
       if obj is None:
           return struct_pb2.Value(null_value=0)
       if isinstance(obj, bool):
           return struct_pb2.Value(bool_value=obj)
       if isinstance(obj, (int, float)):
           return struct_pb2.Value(number_value=float(obj))
       if isinstance(obj, str):
           return struct_pb2.Value(string_value=obj)
       if isinstance(obj, list):
           return struct_pb2.Value(
               list_value=struct_pb2.ListValue(
                   values=[python_to_value(item) for item in obj]
               )
           )
       if isinstance(obj, dict):
           return struct_pb2.Value(
               struct_value=struct_pb2.Struct(
                   fields={k: python_to_value(v) for k, v in obj.items()}
               )
           )
       raise TypeError(f"Unsupported type: {type(obj)}")

   def run_tui_datamodel_workflow() -> None:
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = datamodel_tui_pb2_grpc.TextInterfaceStub(channel)

       try:
           # 1) Get child names at /mesh
           children_resp = stub.GetAttributeValue(
               datamodel_tui_pb2.GetAttributeValueRequest(
                   path="/mesh",
                   attribute=datamodel_tui_pb2.ATTRIBUTE_CHILD_NAMES,
                   args=struct_pb2.Struct(),
               ),
               metadata=metadata,
           )
           print("Child names:", value_to_python(children_resp.value))

           # 2) Get documentation for a node
           doc_resp = stub.GetAttributeValue(
               datamodel_tui_pb2.GetAttributeValueRequest(
                   path="/mesh",
                   attribute=datamodel_tui_pb2.ATTRIBUTE_HELP_STRING,
                   args=struct_pb2.Struct(),
               ),
               metadata=metadata,
           )
           print("Documentation:", value_to_python(doc_resp.value))

           # 3) Execute a command
           cmd_resp = stub.ExecuteCommand(
               datamodel_tui_pb2.ExecuteCommandRequest(
                   path="/mesh",
                   command="check-verbosity",
               ),
               metadata=metadata,
           )
           print("Command result:", value_to_python(cmd_resp.result))

           # 4) Execute a query
           query_resp = stub.ExecuteQuery(
               datamodel_tui_pb2.ExecuteQueryRequest(
                   path="/mesh/check",
               ),
               metadata=metadata,
           )
           print("Query result:", value_to_python(query_resp.result))

           # 5) Retrieve static metadata
           static_resp = stub.GetStaticInfo(
               datamodel_tui_pb2.GetStaticInfoRequest(path="/mesh"),
               metadata=metadata,
           )
           print("Available menus:", list(static_resp.info.menus.keys()))
           print("Available commands:", list(static_resp.info.commands.keys()))

       finally:
           channel.close()

   if __name__ == "__main__":
       run_tui_datamodel_workflow()

See also
~~~~~~~~

- :doc:`../gettingstarted` — basic client setup and connection pattern
- :doc:`../services/datamodel_se` — DataModel service (Solver Engine)
- :doc:`../services/settings` — Settings service for hierarchical configuration
