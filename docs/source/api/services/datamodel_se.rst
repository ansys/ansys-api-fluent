DataModel
=========

Overview
--------

The ``DataModel`` service provides structured read/write access to Fluent's
internal object model. It organises Fluent objects as a tree of singletons,
named-object collections, parameters, commands, and queries — all addressed by
a **rules** string and a slash-separated **path**.

The **rules** string selects which part of the DataModel API you are working
with. Common values are ``meshing`` (the meshing workflow object model) and
``flserver`` (the solver results and post-processing model).

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = datamodel_se_pb2_grpc.DataModelStub(channel)

Runtime API
-----------

Initialization and state streaming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initialize the DataModel API for a rules context, then stream incremental or
full-snapshot state updates as the server-side object model changes.

- ``InitDatamodel(InitDatamodelRequest)`` → ``InitDatamodelResponse``
  Request fields: ``rules: string``, ``return_state_changes: bool``
- ``StreamStateChanges(StreamStateChangesRequest)`` → ``stream StreamStateChangesResponse``
  Request fields: ``rules: string``, ``return_state_changes: bool``, ``diff_state: DiffState``

.. code-block:: python

   stub.InitDatamodel(
       datamodel_se_pb2.InitDatamodelRequest(rules="meshing", return_state_changes=False),
       metadata=metadata,
   )

   stream = stub.StreamStateChanges(
       datamodel_se_pb2.StreamStateChangesRequest(
           rules="meshing",
           return_state_changes=True,
           diff_state=datamodel_se_pb2.DIFF_STATE_FULL,
       ),
       metadata=metadata,
   )
   for i, update in enumerate(stream):
       print(f"Update {i}: deleted={list(update.deleted_paths)}")
       if i >= 2:
           break

State read and write
~~~~~~~~~~~~~~~~~~~~

Read and modify state at any path. ``GetState`` and ``SetState`` work for all
node types. ``UpdateDict`` applies a partial update to a Dict-typed parameter;
``FixState`` lets the server correct invalid state at a path.

``Variant`` is the typed value container used in all state, argument, and
result payloads. Always call ``WhichOneof("as")`` on a returned ``Variant`` to
identify which field is set before accessing it.

- ``GetState(GetStateRequest)`` → ``GetStateResponse``
  Request fields: ``rules: string``, ``path: string``
- ``SetState(SetStateRequest)`` → ``SetStateResponse``
  Request fields: ``rules: string``, ``path: string``, ``state: Variant``, ``wait: bool``
- ``UpdateDict(UpdateDictRequest)`` → ``UpdateDictResponse``
  Request fields: ``rules: string``, ``path: string``, ``merge_dict: Variant``, ``wait: bool``, ``recursive: bool``
- ``FixState(FixStateRequest)`` → ``FixStateResponse``
  Request fields: ``rules: string``, ``path: string``

.. code-block:: python

   from ansys.api.fluent.v1 import variant_pb2

   get_resp = stub.GetState(
       datamodel_se_pb2.GetStateRequest(rules="meshing", path="GlobalSettings/EnableCleanCAD"),
       metadata=metadata,
   )
   print("Current kind:", get_resp.state.WhichOneof("as"))

   stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=True),
           wait=True,
       ),
       metadata=metadata,
   )

Object lifecycle
~~~~~~~~~~~~~~~~

Enumerate, rename, and delete named objects in the DataModel API tree.

- ``GetObjectNames(GetObjectNamesRequest)`` → ``GetObjectNamesResponse``
  Request fields: ``rules: string``, ``path: string``
- ``Rename(RenameRequest)`` → ``RenameResponse``
  Request fields: ``rules: string``, ``path: string``, ``new_name: string``, ``wait: bool``
- ``DeleteObject(DeleteObjectRequest)`` → ``DeleteObjectResponse``
  Request fields: ``rules: string``, ``path: string``, ``wait: bool``
- ``DeleteChildObjects(DeleteChildObjectsRequest)`` → ``DeleteChildObjectsResponse``
  Request fields: ``rules: string``, ``path: string``, oneof ``child_names`` or ``delete_all``, ``wait: bool``

.. code-block:: python

   names_resp = stub.GetObjectNames(
       datamodel_se_pb2.GetObjectNamesRequest(rules="flserver", path="Case/Results/Graphics/Contour"),
       metadata=metadata,
   )
   print("Contour names:", list(names_resp.names))

   if names_resp.names:
       old_name = names_resp.names[0]
       stub.Rename(
           datamodel_se_pb2.RenameRequest(
               rules="flserver",
               path=f"Case/Results/Graphics/Contour:{old_name}",
               new_name=f"{old_name}-renamed",
               wait=True,
           ),
           metadata=metadata,
       )
       stub.DeleteChildObjects(
           datamodel_se_pb2.DeleteChildObjectsRequest(
               rules="flserver",
               path="Case/Results/Graphics/Contour",
               child_names=datamodel_se_pb2.ChildNames(names=[f"{old_name}-renamed"]),
               wait=True,
           ),
           metadata=metadata,
       )

Commands and queries
~~~~~~~~~~~~~~~~~~~~

Execute actions and ask computed questions at a target path. ``ExecuteCommand``
performs a state-mutating action; ``ExecuteQuery`` returns a computed result
without side effects.

- ``ExecuteCommand(ExecuteCommandRequest)`` → ``ExecuteCommandResponse``
  Request fields: ``rules: string``, ``path: string``, ``command: string``, ``wait: bool``, ``args: Variant``
- ``ExecuteQuery(ExecuteQueryRequest)`` → ``ExecuteQueryResponse``
  Request fields: ``rules: string``, ``path: string``, ``query: string``, ``args: Variant``

.. code-block:: python

   cmd_resp = stub.ExecuteCommand(
       datamodel_se_pb2.ExecuteCommandRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
           wait=True,
           args=variant_pb2.Variant(
               variant_map_state=variant_pb2.VariantMap(
                   item={"FileName": variant_pb2.Variant(string_state=r"<file path>")}
               )
           ),
       ),
       metadata=metadata,
   )
   print("Result kind:", cmd_resp.result.WhichOneof("as"))

Command argument lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~

Some multi-step workflows require an explicit command-argument instance that
persists between calls. Create one, populate its state via ``SetState``, then
delete it when you are done.

- ``CreateCommandArguments(CreateCommandArgumentsRequest)`` → ``CreateCommandArgumentsResponse``
  Request fields: ``rules: string``, ``path: string``, ``command: string``
- ``DeleteCommandArguments(DeleteCommandArgumentsRequest)`` → ``DeleteCommandArgumentsResponse``
  Request fields: ``rules: string``, ``path: string``, ``command: string``, ``command_id: string``

.. code-block:: python

   create_args_resp = stub.CreateCommandArguments(
       datamodel_se_pb2.CreateCommandArgumentsRequest(
           rules="meshing", path="", command="ImportGeometry",
       ),
       metadata=metadata,
   )
   command_id = create_args_resp.command_id

   # ... populate argument state via SetState using command_id in the path ...

   stub.DeleteCommandArguments(
       datamodel_se_pb2.DeleteCommandArgumentsRequest(
           rules="meshing", path="", command="ImportGeometry", command_id=command_id,
       ),
       metadata=metadata,
   )

Attribute access
~~~~~~~~~~~~~~~~

Retrieve a named attribute value — for example, the default value, allowed
values, or read-only status — at a specific path. ``GetSpecs`` returns the
full member specification for a path.

- ``GetAttributeValue(GetAttributeValueRequest)`` → ``GetAttributeValueResponse``
  Request fields: ``rules: string``, ``path: string``, ``attribute: string``
- ``GetSpecs(GetSpecsRequest)`` → ``GetSpecsResponse``
  Request fields: ``rules: string``, ``path: string``, ``include_children: bool``

.. code-block:: python

   attr_resp = stub.GetAttributeValue(
       datamodel_se_pb2.GetAttributeValueRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
           attribute="default",
       ),
       metadata=metadata,
   )
   print("Default kind:", attr_resp.result.WhichOneof("as"))

Event subscription
~~~~~~~~~~~~~~~~~~

Subscribe to object-level events — creation, modification, deletion, and
command execution — then consume them as a continuous stream. Call
``UnsubscribeEvents`` to stop receiving events for a given subscription.

- ``SubscribeEvents(SubscribeEventsRequest)`` → ``SubscribeEventsResponse``
- ``UnsubscribeEvents(UnsubscribeEventsRequest)`` → ``UnsubscribeEventsResponse``
- ``StreamEvents(StreamEventsRequest)`` → ``stream StreamEventsResponse``

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

   event_stream = stub.StreamEvents(
       datamodel_se_pb2.StreamEventsRequest(), metadata=metadata,
   )
   for i, event in enumerate(event_stream):
       print(f"Event {i}: tag={event.tag}, kind={event.WhichOneof('event_response')}")
       if i >= 2:
           break

   stub.UnsubscribeEvents(
       datamodel_se_pb2.UnsubscribeEventsRequest(tags=tags), metadata=metadata,
   )

API schema
----------

``GetSchema`` returns the API schema for the DataModel service — a complete,
recursive description of all paths, object types, parameter types, commands,
queries, and argument signatures that exist for a given rules context,
independent of any running simulation.

Use it when you need to enumerate what is available programmatically — for
example, to discover command names before calling ``ExecuteCommand``, or to
build a higher-level client abstraction. See :doc:`../../user_guide/build_a_client` for a
step-by-step walkthrough of schema discovery.

- ``GetSchema(GetSchemaRequest)`` → ``GetSchemaResponse``
  Request field: ``rules: string``

.. code-block:: python

   schema_resp = stub.GetSchema(
       datamodel_se_pb2.GetSchemaRequest(rules="meshing"),
       metadata=metadata,
   )
   root = schema_resp.info
   print("Top-level singletons:", list(root.singletons.keys()))
   print("Top-level named-object types:", list(root.namedobjects.keys()))
