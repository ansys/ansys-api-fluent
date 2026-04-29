DataModel
=========

The Datamodel service provides structured access to Fluent's
state-engine datamodel. You can use this service to read and update state,
inspect metadata, execute commands and queries, and subscribe to datamodel events.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``DataModelService`` (SE) allows you to:

- Initialize and stream datamodel state
- Read, set, and patch state values at any datamodel path
- Query object attributes and static metadata
- Execute commands and queries with typed arguments
- Rename and delete objects, including selective child deletion
- Subscribe to creation/modification/deletion and command-related events

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.datamodel_se``

**Main Classes:**

- ``DataModelServiceStub``: gRPC client stub for solver-engine datamodel operations
- ``Variant``: Generic typed value container used in most state/argument/result payloads
- ``StaticInfo`` and ``MemberSpecs``: Structural and specification metadata objects

Key concepts
~~~~~~~~~~~~

- ``rules``: Datamodel rules context. Use the rules string associated with your active
    solver-engine datamodel context. The examples in this page use both ``meshing``
    and ``flserver`` rules to illustrate different object families.
- ``path``: Datamodel object path (for example, ``GlobalSettings/EnableCleanCAD``).
- ``Variant``: Flexible value message supporting scalars, vectors, nested vectors,
  and dictionaries.

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Initialization and state streaming
----------------------------------

Initialize and consume datamodel state deltas or snapshots.

- ``InitDatamodel(InitDatamodelRequest)`` -> ``InitDatamodelResponse``
  Request fields: ``rules: string``, ``return_state_changes: bool``
- ``StreamStateChanges(StreamStateChangesRequest)`` -> ``stream StreamStateChangesResponse``
  Request fields: ``rules: string``, ``return_state_changes: bool``, ``diff_state: DiffState``

Example: initialize and consume a few state streaming updates

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = datamodel_se_pb2_grpc.DataModelServiceStub(channel)

   init_resp = stub.InitDatamodel(
       datamodel_se_pb2.InitDatamodelRequest(
           rules="meshing",
           return_state_changes=False,
       ),
       metadata=metadata,
   )
   print("Datamodel initialized")

   stream = stub.StreamStateChanges(
       datamodel_se_pb2.StreamStateChangesRequest(
           rules="meshing",
           return_state_changes=True,
           diff_state=datamodel_se_pb2.DIFF_STATE_FULL,
       ),
       metadata=metadata,
   )

   for i, update in enumerate(stream):
       print(f"Update {i}: deleted={list(update.deleted_paths)} events={list(update.events)}")
       if i >= 2:
           break

State read and write
--------------------

Read and modify state at a given datamodel path.

- ``GetState(GetStateRequest)`` -> ``GetStateResponse``
  Request fields: ``rules: string``, ``path: string``
- ``SetState(SetStateRequest)`` -> ``SetStateResponse``
  Request fields: ``rules: string``, ``path: string``, ``state: Variant``, ``wait: bool``
- ``UpdateDict(UpdateDictRequest)`` -> ``UpdateDictResponse``
  Request fields: ``rules: string``, ``path: string``, ``merge_dict: Variant``,
  ``wait: bool``, ``recursive: bool``
- ``FixState(FixStateRequest)`` -> ``FixStateResponse``
  Request fields: ``rules: string``, ``path: string``

Example: get a value, then update Struct-backed paths with ``SetState``

.. code-block:: python

   from ansys.api.fluent.v1 import datamodel_se_pb2, variant_pb2

   get_resp = stub.GetState(
       datamodel_se_pb2.GetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
       ),
       metadata=metadata,
   )
   print("Current value kind:", get_resp.state.WhichOneof("as"))

   set_resp = stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=True),
           wait=True,
       ),
       metadata=metadata,
   )

   # Access and update values under Graphics/Bounds from the same tree
   selection_resp = stub.GetState(
       datamodel_se_pb2.GetStateRequest(
           rules="meshing",
           path="Graphics/Bounds/Selection",
       ),
       metadata=metadata,
   )
   print("Bounds selection:", selection_resp.state)

   _ = stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="Graphics/Bounds/DeltaValue",
           state=variant_pb2.Variant(double_state=0.25),
           wait=True,
       ),
       metadata=metadata,
   )

   _ = stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/LengthUnit",
           state=variant_pb2.Variant(string_state="m"),
           wait=True,
       ),
       metadata=metadata,
   )

   _ = stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/VolumeUnit",
           state=variant_pb2.Variant(string_state="m^3"),
           wait=True,
       ),
       metadata=metadata,
   )

   _ = stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/UseAllowedValues",
           state=variant_pb2.Variant(bool_state=False),
           wait=True,
       ),
       metadata=metadata,
   )

Example: use ``UpdateDict`` only on Dict parameters

.. code-block:: python

   # IMPORTANT:
   # UpdateDict works only when `path` points to a Dict parameter.
   # If `path` points to a Struct node (for example, GlobalSettings),
   # Fluent returns: "updateDict must be called for a Dict parameter; received Struct".

   dict_patch = variant_pb2.Variant(
       variant_map_state=variant_pb2.VariantMap(
           item={
               "key-a": variant_pb2.Variant(string_state="value-a"),
               "key-b": variant_pb2.Variant(bool_state=True),
           }
       )
   )

   _ = stub.UpdateDict(
       datamodel_se_pb2.UpdateDictRequest(
           rules="meshing",
           path="<dict-parameter-path>",
           merge_dict=dict_patch,
           wait=True,
           recursive=True,
       ),
       metadata=metadata,
   )

Object lifecycle operations
---------------------------

Manage named objects and child objects in the datamodel tree.
The examples in this section use ``flserver`` contour object paths.

- ``GetObjectNames(GetObjectNamesRequest)`` -> ``GetObjectNamesResponse``
  Request fields: ``rules: string``, ``path: string``
- ``Rename(RenameRequest)`` -> ``RenameResponse``
  Request fields: ``rules: string``, ``path: string``, ``new_name: string``, ``wait: bool``
- ``DeleteObject(DeleteObjectRequest)`` -> ``DeleteObjectResponse``
  Request fields: ``rules: string``, ``path: string``, ``wait: bool``
- ``DeleteChildObjects(DeleteChildObjectsRequest)`` -> ``DeleteChildObjectsResponse``
  Request fields: ``rules: string``, ``path: string``, oneof ``child_names`` or ``delete_all``, ``wait: bool``

Example: enumerate object names and rename one object

.. code-block:: python

   from ansys.api.fluent.v1 import datamodel_se_pb2

   names_resp = stub.GetObjectNames(
       datamodel_se_pb2.GetObjectNamesRequest(
           rules="flserver",
           path="Case/Results/Graphics/Contour",
       ),
       metadata=metadata,
   )
   print("FTM region entries:", list(names_resp.names))

   if names_resp.names:
       old_name = names_resp.names[0]
       rename_resp = stub.Rename(
           datamodel_se_pb2.RenameRequest(
               rules="flserver",
               path=f"Case/Results/Graphics/Contour:{old_name}",
               new_name=f"{old_name}-renamed",
               wait=True,
           ),
           metadata=metadata,
       )
       print("Renamed object:", old_name)

Example: delete selected child objects

.. code-block:: python

   delete_children_resp = stub.DeleteChildObjects(
       datamodel_se_pb2.DeleteChildObjectsRequest(
           rules="flserver",
           path="Case/Results/Graphics/Contour",
           child_names=datamodel_se_pb2.ChildNames(
               names=[f"{old_name}-renamed"],
           ),
           wait=True,
       ),
       metadata=metadata,
   )

Attribute and metadata retrieval
--------------------------------

Get attributes and structural metadata for dynamic clients and tooling.

- ``GetAttributeValue(GetAttributeValueRequest)`` -> ``GetAttributeValueResponse``
  Request fields: ``rules: string``, ``path: string``, ``attribute: string``
- ``GetSpecs(GetSpecsRequest)`` -> ``GetSpecsResponse``
  Request fields: ``rules: string``, ``path: string``, ``include_children: bool``
- ``GetSchema(GetSchemaRequest)`` -> ``GetSchemaResponse``
  Request field: ``rules: string``

Example: retrieve a single attribute value

.. code-block:: python

   attr_resp = stub.GetAttributeValue(
       datamodel_se_pb2.GetAttributeValueRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
           attribute="default",
       ),
       metadata=metadata,
   )
   print("Default value kind:", attr_resp.result.WhichOneof("as"))

Example: inspect schema

.. code-block:: python

   schema_resp = stub.GetSchema(
       datamodel_se_pb2.GetSchemaRequest(rules="meshing"),
       metadata=metadata,
   )
   print("Top-level named object count:", len(schema_resp.info.singletons))

Command and query execution
---------------------------

Execute actions and ask computed questions at a target path.
The example below demonstrates command execution; query usage follows the same
request pattern with ``ExecuteQuery``.

- ``ExecuteCommand(ExecuteCommandRequest)`` -> ``ExecuteCommandResponse``
  Request fields: ``rules: string``, ``path: string``, ``command: string``, ``wait: bool``, ``args: Variant``
- ``ExecuteQuery(ExecuteQueryRequest)`` -> ``ExecuteQueryResponse``
  Request fields: ``rules: string``, ``path: string``, ``query: string``, ``args: Variant``

Example: execute a command with argument map

.. code-block:: python

   from ansys.api.fluent.v1 import variant_pb2

   cmd_args = variant_pb2.Variant(
       variant_map_state=variant_pb2.VariantMap(
           item={
               "FileName": variant_pb2.Variant(string_state=r"<file path>"),
           }
       )
   )

   cmd_resp = stub.ExecuteCommand(
       datamodel_se_pb2.ExecuteCommandRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
           wait=True,
           args=cmd_args,
       ),
       metadata=metadata,
   )
   print("Command result kind:", cmd_resp.result.WhichOneof("as"))

Command argument lifecycle
--------------------------

Some command workflows support explicit command-argument instance lifecycle.

- ``CreateCommandArguments(CreateCommandArgumentsRequest)`` -> ``CreateCommandArgumentsResponse``
  Request fields: ``rules: string``, ``path: string``, ``command: string``
- ``DeleteCommandArguments(DeleteCommandArgumentsRequest)`` -> ``DeleteCommandArgumentsResponse``
  Request fields: ``rules: string``, ``path: string``, ``command: string``, ``command_id: string``

Example: create and clean up command argument instance

.. code-block:: python

   create_args_resp = stub.CreateCommandArguments(
       datamodel_se_pb2.CreateCommandArgumentsRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
       ),
       metadata=metadata,
   )
   command_id = create_args_resp.command_id
   print("Created command_id:", command_id)

   _ = stub.DeleteCommandArguments(
       datamodel_se_pb2.DeleteCommandArgumentsRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
           command_id=command_id,
       ),
       metadata=metadata,
   )

Event subscription and event streaming
--------------------------------------

Subscribe to specific event types, then consume event stream updates.

- ``SubscribeEvents(SubscribeEventsRequest)`` -> ``SubscribeEventsResponse``
- ``UnsubscribeEvents(UnsubscribeEventsRequest)`` -> ``UnsubscribeEventsResponse``
- ``StreamEvents(StreamEventsRequest)`` -> ``stream StreamEventsResponse``

Example: subscribe to modification events and read event stream

.. code-block:: python

   sub_resp = stub.SubscribeEvents(
       datamodel_se_pb2.SubscribeEventsRequest(
           event_requests=[
               datamodel_se_pb2.DataModelEventRequest(
                   rules="meshing",
                   modified_event_request=datamodel_se_pb2.ModifiedEventRequest(
                       path="GlobalSettings/EnableCleanCAD"
                   ),
               )
           ]
       ),
       metadata=metadata,
   )

   tags = [r.tag for r in sub_resp.responses]
   print("Subscription tags:", tags)

   event_stream = stub.StreamEvents(
       datamodel_se_pb2.StreamEventsRequest(),
       metadata=metadata,
   )

   for i, event in enumerate(event_stream):
       kind = event.WhichOneof("event_response")
       print(f"Event {i}: tag={event.tag}, rules={event.rules}, kind={kind}")
       if i >= 2:
           break

   _ = stub.UnsubscribeEvents(
       datamodel_se_pb2.UnsubscribeEventsRequest(tags=tags),
       metadata=metadata,
   )

Working with variant values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most datamodel request and response payloads rely on ``Variant``. The helper functions
below convert between Python objects and ``Variant`` messages.

.. code-block:: python

   from ansys.api.fluent.v1 import variant_pb2

   def python_to_variant(value):
       if value is None:
           return variant_pb2.Variant(empty_state=variant_pb2.Empty())
       if isinstance(value, bool):
           return variant_pb2.Variant(bool_state=value)
       if isinstance(value, int):
           return variant_pb2.Variant(int64_state=value)
       if isinstance(value, float):
           return variant_pb2.Variant(double_state=value)
       if isinstance(value, str):
           return variant_pb2.Variant(string_state=value)
       if isinstance(value, list):
           return variant_pb2.Variant(
               variant_vector_state=variant_pb2.VariantVector(
                   items=[python_to_variant(v) for v in value]
               )
           )
       if isinstance(value, dict):
           return variant_pb2.Variant(
               variant_map_state=variant_pb2.VariantMap(
                   item={k: python_to_variant(v) for k, v in value.items()}
               )
           )
       raise TypeError(f"Unsupported type: {type(value)}")

   def variant_to_python(v):
       kind = v.WhichOneof("as")
       if kind == "empty_state":
           return None
       if kind == "bool_state":
           return v.bool_state
       if kind == "int64_state":
           return v.int64_state
       if kind == "double_state":
           return v.double_state
       if kind == "string_state":
           return v.string_state
       if kind == "bool_vector_state":
           return list(v.bool_vector_state.items)
       if kind == "int64_vector_state":
           return list(v.int64_vector_state.items)
       if kind == "double_vector_state":
           return list(v.double_vector_state.items)
       if kind == "string_vector_state":
           return list(v.string_vector_state.items)
       if kind == "variant_vector_state":
           return [variant_to_python(item) for item in v.variant_vector_state.items]
       if kind == "variant_map_state":
           return {k: variant_to_python(val) for k, val in v.variant_map_state.item.items()}
       return None

Complete end-to-end example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates an end-to-end solver-engine datamodel workflow:

1. Initialize datamodel
2. Read and update state
3. Retrieve an attribute value
4. Execute a command
5. Subscribe and stream events
6. List, rename, and delete objects
7. Cleanly unsubscribe and close channel

.. code-block:: python

   from __future__ import annotations
   import grpc
   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc, variant_pb2

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"
   RULES = "meshing"

   def python_to_variant(value):
       if value is None:
           return variant_pb2.Variant(empty_state=variant_pb2.Empty())
       if isinstance(value, bool):
           return variant_pb2.Variant(bool_state=value)
       if isinstance(value, int):
           return variant_pb2.Variant(int64_state=value)
       if isinstance(value, float):
           return variant_pb2.Variant(double_state=value)
       if isinstance(value, str):
           return variant_pb2.Variant(string_state=value)
       if isinstance(value, list):
           return variant_pb2.Variant(
               variant_vector_state=variant_pb2.VariantVector(
                   items=[python_to_variant(v) for v in value]
               )
           )
       if isinstance(value, dict):
           return variant_pb2.Variant(
               variant_map_state=variant_pb2.VariantMap(
                   item={k: python_to_variant(v) for k, v in value.items()}
               )
           )
       raise TypeError(f"Unsupported type: {type(value)}")

   def variant_to_python(v):
       kind = v.WhichOneof("as")
       if kind == "empty_state":
           return None
       if kind == "bool_state":
           return v.bool_state
       if kind == "int64_state":
           return v.int64_state
       if kind == "double_state":
           return v.double_state
       if kind == "string_state":
           return v.string_state
       if kind == "bool_vector_state":
           return list(v.bool_vector_state.items)
       if kind == "int64_vector_state":
           return list(v.int64_vector_state.items)
       if kind == "double_vector_state":
           return list(v.double_vector_state.items)
       if kind == "string_vector_state":
           return list(v.string_vector_state.items)
       if kind == "variant_vector_state":
           return [variant_to_python(item) for item in v.variant_vector_state.items]
       if kind == "variant_map_state":
           return {k: variant_to_python(val) for k, val in v.variant_map_state.item.items()}
       return None

   def run_datamodel_workflow() -> None:
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = datamodel_se_pb2_grpc.DataModelServiceStub(channel)

       try:
           # 1) Initialize datamodel
           _ = stub.InitDatamodel(
               datamodel_se_pb2.InitDatamodelRequest(
                   rules=RULES,
                   return_state_changes=False,
               ),
               metadata=metadata,
           )
           print("Datamodel initialized")

           # 2) Read and update state
           get_state_resp = stub.GetState(
               datamodel_se_pb2.GetStateRequest(
                   rules=RULES,
                   path="GlobalSettings/EnableCleanCAD",
               ),
               metadata=metadata,
           )
           print("EnableCleanCAD (before):", variant_to_python(get_state_resp.state))

           _ = stub.SetState(
               datamodel_se_pb2.SetStateRequest(
                   rules=RULES,
                   path="GlobalSettings/EnableCleanCAD",
                   state=python_to_variant(True),
                   wait=True,
               ),
               metadata=metadata,
           )

           # Also read and update Graphics/Bounds values from the provided state tree
           selection_resp = stub.GetState(
               datamodel_se_pb2.GetStateRequest(
                   rules=RULES,
                   path="Graphics/Bounds/Selection",
               ),
               metadata=metadata,
           )
           print("Bounds selection:", variant_to_python(selection_resp.state))

           _ = stub.SetState(
               datamodel_se_pb2.SetStateRequest(
                   rules=RULES,
                   path="Graphics/Bounds/Selection",
                   state=python_to_variant(""),
                   wait=True,
               ),
               metadata=metadata,
           )

           _ = stub.SetState(
               datamodel_se_pb2.SetStateRequest(
                   rules=RULES,
                   path="Graphics/Bounds/DeltaValue",
                   state=python_to_variant(0.25),
                   wait=True,
               ),
               metadata=metadata,
           )

           _ = stub.SetState(
               datamodel_se_pb2.SetStateRequest(
                   rules=RULES,
                   path="GlobalSettings/LengthUnit",
                   state=python_to_variant("m"),
                   wait=True,
               ),
               metadata=metadata,
           )

           _ = stub.SetState(
               datamodel_se_pb2.SetStateRequest(
                   rules=RULES,
                   path="GlobalSettings/VolumeUnit",
                   state=python_to_variant("m^3"),
                   wait=True,
               ),
               metadata=metadata,
           )

           _ = stub.SetState(
               datamodel_se_pb2.SetStateRequest(
                   rules=RULES,
                   path="GlobalSettings/UseAllowedValues",
                   state=python_to_variant(False),
                   wait=True,
               ),
               metadata=metadata,
           )

           # 3) Attribute retrieval
           attr_resp = stub.GetAttributeValue(
               datamodel_se_pb2.GetAttributeValueRequest(
                   rules=RULES,
                   path="GlobalSettings/EnableCleanCAD",
                   attribute="default",
               ),
               metadata=metadata,
           )
           print("EnableCleanCAD default:", variant_to_python(attr_resp.result))

           # 4) Command execution
           from ansys.api.fluent.v1 import variant_pb2

            cmd_args = variant_pb2.Variant(
                variant_map_state=variant_pb2.VariantMap(
                    item={
                        "FileName": variant_pb2.Variant(string_state=r"<file-name>"),
                    }
                )
            )

           _ = stub.ExecuteCommand(
               datamodel_se_pb2.ExecuteCommandRequest(
                   rules=RULES,
                   path="",
                   command="ImportGeometry",
                   wait=True,
                   args=cmd_args,
               ),
               metadata=metadata,
           )

           # 5) Subscribe and stream events
           sub_resp = stub.SubscribeEvents(
               datamodel_se_pb2.SubscribeEventsRequest(
                   event_requests=[
                       datamodel_se_pb2.DataModelEventRequest(
                           rules=RULES,
                           modified_event_request=datamodel_se_pb2.ModifiedEventRequest(
                               path="GlobalSettings/EnableCleanCAD"
                           ),
                       )
                   ]
               ),
               metadata=metadata,
           )
           tags = [r.tag for r in sub_resp.responses]

           # Trigger a change that can produce a modified event
           _ = stub.SetState(
               datamodel_se_pb2.SetStateRequest(
                   rules=RULES,
                   path="GlobalSettings/EnableCleanCAD",
                   state=python_to_variant(False),
                   wait=True,
               ),
               metadata=metadata,
           )

           events = stub.StreamEvents(
               datamodel_se_pb2.StreamEventsRequest(),
               metadata=metadata,
           )
           for i, event in enumerate(events):
               event_kind = event.WhichOneof("event_response")
               print(f"Event {i}: {event_kind}, tag={event.tag}")
               if i >= 0:
                   break

           _ = stub.UnsubscribeEvents(
               datamodel_se_pb2.UnsubscribeEventsRequest(tags=tags),
               metadata=metadata,
           )

           # 6) List, rename, and delete objects
           names_resp = stub.GetObjectNames(
               datamodel_se_pb2.GetObjectNamesRequest(
                   rules="flserver",
                   path="Case/Results/Graphics/Contour",
               ),
               metadata=metadata,
           )
           names = list(names_resp.names)
           print("Contour entries:", names)

           if names:
               first_name = names[0]
               _ = stub.Rename(
                   datamodel_se_pb2.RenameRequest(
                       rules="flserver",
                       path=f"Case/Results/Graphics/Contour:{first_name}",
                       new_name=f"{first_name}-tmp",
                       wait=True,
                   ),
                   metadata=metadata,
               )

               _ = stub.DeleteChildObjects(
                   datamodel_se_pb2.DeleteChildObjectsRequest(
                       rules="flserver",
                       path="Case/Results/Graphics/Contour",
                       child_names=datamodel_se_pb2.ChildNames(
                           names=[f"{first_name}-tmp"],
                       ),
                       wait=True,
                   ),
                   metadata=metadata,
               )

       finally:
           channel.close()

   if __name__ == "__main__":
       run_datamodel_workflow()

See also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup and connection pattern
- :doc:`settings` - Hierarchical settings service and value model examples
- :doc:`datamodel_tui` - Datamodel service in TUI mode
