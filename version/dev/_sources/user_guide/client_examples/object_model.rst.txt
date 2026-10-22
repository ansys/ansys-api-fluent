ObjectModel service
====================

Python client examples for the ``ObjectModel`` gRPC service.

See :doc:`../../api/services/object_model`
for this service's complete reference material.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import object_model_pb2, object_model_pb2_grpc
   from ansys.api.fluent.v1 import variant_pb2

   channel = grpc.insecure_channel("<server-address>")
   metadata = [("password", "<password>")]
   stub = object_model_pb2_grpc.ObjectModelStub(channel)

The **rules** string selects the application context. All examples on this
page use ``"meshing"``.

Discovering the schema
-----------------------

``GetSchema`` returns the static tree of objects, commands, queries, and
parameters — walk it to discover valid paths before making runtime calls.

.. code-block:: python
   :caption: Python

   schema_response = stub.GetSchema(
       object_model_pb2.GetSchemaRequest(rules="meshing"),
       metadata=metadata,
   )

   def walk(node, indent=0):
       prefix = "  " * indent
       for name, child in node.singletons.items():
           print(f"{prefix}{name}/")
           walk(child, indent + 1)
       for name, child in node.named_objects.items():
           print(f"{prefix}{name}:<name>/")
           walk(child, indent + 1)
       for name in node.parameters:
           print(f"{prefix}{name}")
       for name in node.commands:
           print(f"{prefix}{name}()")

   walk(schema_response.info)

.. raw:: html

   <details>
   <summary style="cursor:pointer;user-select:none;font-weight:bold;padding:4px 0">
    Schema output (click to expand)
   </summary>
   <pre style="background:#2b2b2b;color:#f8f8f2;border:1px solid #444;border-radius:4px;padding:12px;margin-top:6px;overflow:auto;font-size:0.85em;line-height:1.5">
   File/
     StartJournal()
     StopJournal()
     WriteCase()
     ReadCase()
     ReadMesh()
     ... (2 more commands)
   Graphics/
     Bounds/
       BoundZ
       BoundX
       BoundY
       Selection
       DeltaValue
       ResetBounds()
       SetBounds()
     Regions/
       DrawDead()
       DrawAll()
       DrawFluid()
       DrawSolid()
     MarkGaps()
     ClippingPlane()
     DrawThinVolumeRegions()
     GetClippingZoneIDs()
     GetVisibleDomainBounds()
   GlobalSettings/
     FTMRegionData/
       AllRegionTypeList
       AllRegionMeshMethodList
       AllRegionOversetComponenList
       AllOversetVolumeFillList
       AllRegionSizeList
       ... (9 more parameters)
     LengthUnit
     EnableCleanCAD
     EnableOversetMeshing
     UseAllowedValues
     EnablePrimeMeshing
     ... (9 more parameters)
   Diagnostics/
     Draw()
     List()
     Previous()
     Next()
     Ignore()
     ... (9 more commands)
   AddShellBoundaryLayerControls()
   SizeControlsTable()
   IdentifyDeviatedFaces()
   IdentifyConstructionSurfaces()
   CreateBackgroundMesh()
   ... (78 more commands)
   </pre>
   </details>


Reading and writing state
--------------------------

.. code-block:: python
   :caption: Python

   # Fetch a current boolean value.
   state_response = stub.GetState(
       object_model_pb2.GetStateRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
       ),
       metadata=metadata,
   )
   current = state_response.state.bool_state  # use .string_state, .int_state, etc. for other types
   print(current)  # prints the current value as a bool

   # Modify the value at the same path.
   stub.SetState(
       object_model_pb2.SetStateRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=not current),
       ),
       metadata=metadata,
   )

   # Restore the original value.
   stub.SetState(
       object_model_pb2.SetStateRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=current),
       ),
       metadata=metadata,
   )

Querying attributes
--------------------

``GetAttributeValue`` provides access to metadata, including constraints
(range/min‑max, allowed/enumerated values), mutability (read-only/writable),
availability (active/disabled), and default values.

.. code-block:: python
   :caption: Python

   attribute_response = stub.GetAttributeValue(
       object_model_pb2.GetAttributeValueRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
           attribute="default",
       ),
       metadata=metadata,
   )
   print(attribute_response.result.bool_state)  # -> False

Executing commands
-------------------

You can pass command arguments as a ``Variant`` map.
``ExecuteCommand`` executes the specified server-side command.

.. code-block:: python
   :caption: Python

   stub.ExecuteCommand(
       object_model_pb2.ExecuteCommandRequest(
           rules="meshing",
           path="/",
           command="ImportGeometry",
           args=variant_pb2.Variant(
               variant_map_state=variant_pb2.VariantMap(
                   item={"FileName": variant_pb2.Variant(string_state="mixing_elbow.pmdb")}
               )
           ),
       ),
       metadata=metadata,
   )

Building command arguments incrementally
-----------------------------------------

``CreateCommandArguments`` creates a server-side argument object so you can
set individual fields before calling ``ExecuteCommand``.

.. code-block:: python
   :caption: Python

   # Allocate an argument object on the server.
   create_response = stub.CreateCommandArguments(
       object_model_pb2.CreateCommandArgumentsRequest(
           rules="meshing",
           path="/",
           command="ImportGeometry",
       ),
       metadata=metadata,
   )
   command_id = create_response.command_id

   # ... populate fields via SetState using the command_id path ...

   # Clean up without executing.
   stub.DeleteCommandArguments(
       object_model_pb2.DeleteCommandArgumentsRequest(
           rules="meshing",
           path="/",
           command="ImportGeometry",
           command_id=command_id,
       ),
       metadata=metadata,
   )

Subscribing to, streaming, and unsubscribing from events
----------------------------------------------------------

``SubscribeEvents`` registers interest in specific object model changes;
``StreamEvents`` delivers them as a server-streaming call;
``UnsubscribeEvents`` cancels the subscriptions when done.

.. code-block:: python
   :caption: Python

   # Subscribe to modifications on a specific path.
   subscribe_response = stub.SubscribeEvents(
       object_model_pb2.SubscribeEventsRequest(
           event_requests=[
               object_model_pb2.ObjectModelEventRequest(
                   rules="meshing",
                   modified_event_request=object_model_pb2.ModifiedEventRequest(
                       path="/GlobalSettings/EnableCleanCAD"
                   ),
               )
           ]
       ),
       metadata=metadata,
   )
   tags = [r.tag for r in subscribe_response.responses]
   # tags is a list of UUIDs — hold on to them; they are needed to unsubscribe.

   # Stream events — events arrive only when something else modifies the
   # subscribed path on the server (e.g. another client or a running solver).
   stream = stub.StreamEvents(
       object_model_pb2.StreamEventsRequest(),
       metadata=metadata,
   )
   count = 0
   for event in stream:
       mod = event.modified_event_response
       print(mod.path)   # -> '/GlobalSettings/EnableCleanCAD'
       print(mod.value)  # -> Variant carrying the updated value
       count += 1
       if count >= 3:
           break
   stream.cancel()

   # Unsubscribe.
   unsubscribe_response = stub.UnsubscribeEvents(
       object_model_pb2.UnsubscribeEventsRequest(tags=tags),
       metadata=metadata,
   )
   for r in unsubscribe_response.responses:
       print(r.status)  # -> SUBSCRIPTION_STATUS_UNSUBSCRIBED

Streaming state changes
------------------------

``StreamStateChanges`` delivers a snapshot or diff of the object model whenever
it changes. Use ``DIFF_STATE_FULL`` for a complete snapshot or
``DIFF_STATE_NOCOMMANDS`` for a lighter diff without command metadata.

.. code-block:: python
   :caption: Python

   # Full snapshot on every change.
   stream = stub.StreamStateChanges(
       object_model_pb2.StreamStateChangesRequest(
           rules="meshing",
           return_state_changes=True,
           diff_state=object_model_pb2.DIFF_STATE_FULL,
       ),
       metadata=metadata,
   )
   first_response = next(iter(stream))
   stream.cancel()
   print(list(first_response.deleted_paths))  # -> []  (empty list when nothing has been deleted)
   print(list(first_response.events))         # -> []  (empty list when no events fired)

   # Lighter diff without command metadata.
   stream = stub.StreamStateChanges(
       object_model_pb2.StreamStateChangesRequest(
           rules="meshing",
           return_state_changes=True,
           diff_state=object_model_pb2.DIFF_STATE_NOCOMMANDS,
       ),
       metadata=metadata,
   )
   first_response = next(iter(stream))
   stream.cancel()
   assert hasattr(first_response, "state")

See :doc:`../../api/services/object_model` for the complete reference material.
