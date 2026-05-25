DataModel service
==================

Python client examples for the ``DataModel`` gRPC service.

See :doc:`../../api/services/datamodel_se`
for this service's complete reference material.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc
   from ansys.api.fluent.v1 import variant_pb2

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = datamodel_se_pb2_grpc.DataModelStub(channel)

The **rules** string selects the application context. All examples on this
page use ``"meshing"``.

Discovering the schema
-----------------------

``GetSchema`` returns the static tree of objects, commands, queries, and
parameters — walk it to discover valid paths before making runtime calls.

.. code-block:: python
   :caption: Python

   schema_resp = stub.GetSchema(
       datamodel_se_pb2.GetSchemaRequest(rules="meshing"),
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

   walk(schema_resp.info)

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


Initialising the datamodel
---------------------------

.. code-block:: python
   :caption: Python

   resp = stub.InitDatamodel(
       datamodel_se_pb2.InitDatamodelRequest(
           rules="meshing",
           return_state_changes=False,
       ),
       metadata=metadata,
   )

Reading and writing state
--------------------------

``GetState`` returns a :doc:`Variant <../../api/helpers/variant>`; ``SetState``
writes one back.

.. code-block:: python
   :caption: Python

   # Read a boolean parameter.
   resp = stub.GetState(
       datamodel_se_pb2.GetStateRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
       ),
       metadata=metadata,
   )
   current = resp.state.bool_state
   print(current)  # -> False  (or True, depending on server state)

   # Write the opposite value.
   stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=not current),
       ),
       metadata=metadata,
   )

   # Restore the original.
   stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=current),
       ),
       metadata=metadata,
   )

Reading parameter attributes
-----------------------------

``GetAttributeValue`` returns metadata about a parameter such as its default,
allowed values, or whether it is read-only or active.

.. code-block:: python
   :caption: Python

   resp = stub.GetAttributeValue(
       datamodel_se_pb2.GetAttributeValueRequest(
           rules="meshing",
           path="/GlobalSettings/EnableCleanCAD",
           attribute="default",
       ),
       metadata=metadata,
   )
   print(resp.result.bool_state)  # -> False

Executing commands
-------------------

``ExecuteCommand`` runs a command on the server; pass arguments as a
``Variant`` map.

.. code-block:: python
   :caption: Python

   stub.ExecuteCommand(
       datamodel_se_pb2.ExecuteCommandRequest(
           rules="meshing",
           path="",
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
   create_resp = stub.CreateCommandArguments(
       datamodel_se_pb2.CreateCommandArgumentsRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
       ),
       metadata=metadata,
   )
   command_id = create_resp.command_id
   print(command_id)  # -> '3f2a1b...'  (a non-empty server-assigned string)

   # ... populate fields via SetState using the command_id path ...

   # Clean up without executing.
   stub.DeleteCommandArguments(
       datamodel_se_pb2.DeleteCommandArgumentsRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
           command_id=command_id,
       ),
       metadata=metadata,
   )

Subscribing to and streaming events
-------------------------------------

``SubscribeEvents`` registers interest in specific datamodel changes;
``StreamEvents`` delivers them as a server-streaming call. Unsubscribe when done.

.. code-block:: python
   :caption: Python

   # Subscribe to modifications on a specific path.
   sub_resp = stub.SubscribeEvents(
       datamodel_se_pb2.SubscribeEventsRequest(
           event_requests=[
               datamodel_se_pb2.DataModelEventRequest(
                   rules="meshing",
                   modified_event_request=datamodel_se_pb2.ModifiedEventRequest(
                       path="/GlobalSettings/EnableCleanCAD"
                   ),
               )
           ]
       ),
       metadata=metadata,
   )
   tags = [r.tag for r in sub_resp.responses]
   print(tags)  # -> ['<uuid>']  (one non-empty tag per subscription)

   # Open the event stream and read a few events.
   stream = stub.StreamEvents(
       datamodel_se_pb2.StreamEventsRequest(),
       metadata=metadata,
   )
   count = 0
   for event in stream:
       print(event.tag)  # -> '<uuid>' matching one of the subscribed tags
       count += 1
       if count >= 3:
           break
   stream.cancel()

   # Unsubscribe.
   unsub_resp = stub.UnsubscribeEvents(
       datamodel_se_pb2.UnsubscribeEventsRequest(tags=tags),
       metadata=metadata,
   )
   for r in unsub_resp.responses:
       print(r.status)  # -> SUBSCRIPTION_STATUS_UNSUBSCRIBED

Streaming state changes
------------------------

``StreamStateChanges`` delivers a snapshot or diff of the datamodel whenever
it changes. Use ``DIFF_STATE_FULL`` for a complete snapshot or
``DIFF_STATE_NOCOMMANDS`` for a lighter diff without command metadata.

.. code-block:: python
   :caption: Python

   # Full snapshot on every change.
   stream = stub.StreamStateChanges(
       datamodel_se_pb2.StreamStateChangesRequest(
           rules="meshing",
           return_state_changes=True,
           diff_state=datamodel_se_pb2.DIFF_STATE_FULL,
       ),
       metadata=metadata,
   )
   first = next(iter(stream))
   stream.cancel()
   print(list(first.deleted_paths))  # -> []  (empty list when nothing has been deleted)
   print(list(first.events))         # -> []  (empty list when no events fired)

   # Lighter diff without command metadata.
   stream = stub.StreamStateChanges(
       datamodel_se_pb2.StreamStateChangesRequest(
           rules="meshing",
           return_state_changes=True,
           diff_state=datamodel_se_pb2.DIFF_STATE_NOCOMMANDS,
       ),
       metadata=metadata,
   )
   first = next(iter(stream))
   stream.cancel()
   assert hasattr(first, "state")

For the complete message and field reference — request/response types,
``Variant`` encoding, and the ``DiffState`` enum — see
:doc:`../../api/services/datamodel_se`.
