Reading and writing simulation data
====================================

Three services give you access to the numbers inside a running Fluent session:
stream field values off surfaces, compute aggregated reductions, and read or
write raw per-zone solver arrays.

For the full message and field reference see :doc:`../../api/services/field_data`,
:doc:`../../api/services/reduction`, and :doc:`../../api/services/svar`.

.. include:: ../../shared_example_assumptions.rst

Discovering available data
--------------------------

Before streaming anything, confirm that solution data exists and enumerate the
surfaces and fields the solver currently exposes.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import field_data_pb2, field_data_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = field_data_pb2_grpc.FieldDataStub(channel)

   # Guard: only proceed if the solver has data loaded.
   if not stub.IsDataAvailable(
       field_data_pb2.IsDataAvailableRequest(), metadata=metadata
   ).is_data_available:
       raise RuntimeError("No solution data available — load a case/data first")

   # Enumerate surfaces and remember their IDs.
   surfaces = {
       sid.id: info.surface_name
       for info in stub.GetSurfacesInfo(
           field_data_pb2.GetSurfacesInfoRequest(), metadata=metadata
       ).surface_info
       for sid in info.surface_ids
   }
   print("Surfaces:", surfaces)

   # Enumerate available scalar fields.
   fields = [
       f.solver_name
       for f in stub.GetFieldsInfo(
           field_data_pb2.GetFieldsInfoRequest(), metadata=metadata
       ).field_info
   ]
   print("Scalar fields:", fields)

Streaming field data
--------------------

``GetScalarField`` streams pressure or any other scalar on one or more
surfaces. Each response chunk carries the surface ID and the array of
nodal or cell-centre values. Use ``GetVectorField`` for velocity and
similar vector quantities.

.. code-block:: python
   :caption: Python

   first_id = next(iter(surfaces))

   # Scalar field — nodal values.
   for resp in stub.GetScalarField(
       field_data_pb2.GetScalarFieldRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=first_id)],
           scalar_field="pressure",
           node_value=True,
           boundary_values=False,
       ),
       metadata=metadata,
   ):
       sfd = resp.scalar_field_data
       print(f"surface {sfd.surface_id.id}: {len(sfd.scalar_field.data)} pressure values")

   # Vector field — velocity on the same surface.
   for resp in stub.GetVectorField(
       field_data_pb2.GetVectorFieldRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=first_id)],
           vector_field="velocity",
           node_value=True,
       ),
       metadata=metadata,
   ):
       vfd = resp.vector_field_data
       print(f"surface {vfd.surface_id.id}: {len(vfd.vector.vector_components)} velocity vectors")

Computing reductions
--------------------

The ``Reduction`` service aggregates field quantities without streaming raw
arrays. Pass surface or zone names in ``locations`` and an expression string
for field-based operations. Scalar results come back inside a ``Variant``
value — inspect ``WhichOneof("as")`` to get the concrete type.

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import reduction_pb2, reduction_pb2_grpc

   rstub = reduction_pb2_grpc.ReductionStub(channel)

   # Geometric queries.
   area = rstub.Area(
       reduction_pb2.AreaRequest(locations=["wall-inlet"]), metadata=metadata
   )
   print("Wall area:", area.value.double_state)

   centroid = rstub.Centroid(
       reduction_pb2.CentroidRequest(locations=["wall-inlet"]), metadata=metadata
   )
   c = centroid.value
   print(f"Centroid: ({c.x:.4g}, {c.y:.4g}, {c.z:.4g})")

   # Weighted average and range.
   avg_p = rstub.AreaAve(
       reduction_pb2.AreaAveRequest(
           expression="AbsolutePressure", locations=["wall-inlet"]
       ),
       metadata=metadata,
   )
   print("Area-average pressure:", avg_p.value.double_state)

   max_p = rstub.Maximum(
       reduction_pb2.MaximumRequest(
           expression="AbsolutePressure", locations=["fluid"]
       ),
       metadata=metadata,
   )
   min_p = rstub.Minimum(
       reduction_pb2.MinimumRequest(
           expression="AbsolutePressure", locations=["fluid"]
       ),
       metadata=metadata,
   )
   print(f"Pressure range: {min_p.value.double_state:.4e} – {max_p.value.double_state:.4e}")

   # Force decomposition on a boundary.
   fp = rstub.PressureForce(
       reduction_pb2.PressureForceRequest(locations=["car-body"]), metadata=metadata
   ).value
   fv = rstub.ViscousForce(
       reduction_pb2.ViscousForceRequest(locations=["car-body"]), metadata=metadata
   ).value
   print(f"Pressure force: ({fp.x:.4g}, {fp.y:.4g}, {fp.z:.4g})")
   print(f"Viscous  force: ({fv.x:.4g}, {fv.y:.4g}, {fv.z:.4g})")

Reading and writing solution variables
---------------------------------------

The ``SolutionVariable`` service works at zone level rather than surface level.
Call ``GetZonesInfo`` to discover domain and zone IDs, stream raw arrays with
``GetSolutionVariableData``, and push modified values back with
``SetSolutionVariableData``.

.. code-block:: python
   :caption: Python

   import math
   import numpy as np
   from ansys.api.fluent.v1 import svar_pb2, svar_pb2_grpc

   svstub = svar_pb2_grpc.SolutionVariableStub(channel)

   # Discover zones.
   zones_resp = svstub.GetZonesInfo(
       svar_pb2.GetZonesInfoRequest(), metadata=metadata
   )
   for z in zones_resp.zones_info:
       print(f"zone {z.zone_id}: {z.name} ({z.zone_type})")

   # Read pressure (SV_P) on zone 12.
   values = []
   for msg in svstub.GetSolutionVariableData(
       svar_pb2.GetSolutionVariableDataRequest(
           name="SV_P", domain_id=1, zones=[12],
           chunk_size=256 * 1024, provide_bytes_stream=False,
       ),
       metadata=metadata,
   ):
       part = msg.WhichOneof("array")
       if part == "payload":
           kind = msg.payload.WhichOneof("chunk")
           if kind == "double_payload":
               values.extend(msg.payload.double_payload.payloads)
           elif kind == "float_payload":
               values.extend(msg.payload.float_payload.payloads)
   print(f"Read {len(values)} SV_P values from zone 12")

   # Write a uniform pressure field back.
   def _set_stream(name, domain_id, zone_id, data):
       """Generator that yields the header, info, and payload messages."""
       yield svar_pb2.SetSolutionVariableDataRequest(
           header=svar_pb2.SolutionVariableHeader(name=name, domain_id=domain_id)
       )
       arr = np.asarray(data, dtype=np.float64)
       yield svar_pb2.SetSolutionVariableDataRequest(
           payload_info=svar_pb2.Info(
               field_type=4,  # FIELD_TYPE_DOUBLE_ARRAY
               field_size=arr.size,
               zone=zone_id,
           )
       )
       chunk_size = 256 * 1024 // arr.dtype.itemsize
       for chunk in np.array_split(arr, max(1, math.ceil(arr.size / chunk_size))):
           if chunk.size:
               from ansys.api.fluent.v1 import field_data_pb2
               yield svar_pb2.SetSolutionVariableDataRequest(
                   payload=svar_pb2.Payload(
                       double_payload=field_data_pb2.DoublePayload(payloads=chunk)
                   )
               )

   svstub.SetSolutionVariableData(
       _set_stream("SV_P", domain_id=1, zone_id=12,
                   data=np.full(len(values), 101325.0)),
       metadata=metadata,
   )
   print("SV_P written back to zone 12")

End-to-end example
------------------

The workflow below ties the three services together: check readiness, stream a
scalar field off a surface, compute a force reduction, and read back the
corresponding zone-level variable.

.. code-block:: python
   :caption: Python

   import grpc
   import numpy as np
   from ansys.api.fluent.v1 import (
       field_data_pb2, field_data_pb2_grpc,
       reduction_pb2, reduction_pb2_grpc,
       svar_pb2, svar_pb2_grpc,
   )

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]

   fd = field_data_pb2_grpc.FieldDataStub(channel)
   rd = reduction_pb2_grpc.ReductionStub(channel)
   sv = svar_pb2_grpc.SolutionVariableStub(channel)

   # 1. Confirm data is ready.
   assert fd.IsDataAvailable(
       field_data_pb2.IsDataAvailableRequest(), metadata=metadata
   ).is_data_available, "No data loaded"

   # 2. Pick the first available surface.
   info = fd.GetSurfacesInfo(
       field_data_pb2.GetSurfacesInfoRequest(), metadata=metadata
   ).surface_info[0]
   sid = info.surface_ids[0].id
   print(f"Using surface '{info.surface_name}' (id={sid})")

   # 3. Stream pressure values off that surface.
   pressure_values = []
   for resp in fd.GetScalarField(
       field_data_pb2.GetScalarFieldRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=sid)],
           scalar_field="pressure",
           node_value=True,
           boundary_values=False,
       ),
       metadata=metadata,
   ):
       pressure_values.extend(resp.scalar_field_data.scalar_field.data)
   arr = np.array(pressure_values)
   print(f"Surface pressure — min: {arr.min():.4e}  max: {arr.max():.4e}  "
         f"mean: {arr.mean():.4e}")

   # 4. Cross-check with a server-side reduction.
   avg = rd.AreaAve(
       reduction_pb2.AreaAveRequest(
           expression="AbsolutePressure",
           locations=[info.surface_name],
       ),
       metadata=metadata,
   )
   print(f"Server area-average pressure: {avg.value.double_state:.4e}")

   # 5. Read the same quantity at zone level.
   zone_id = sv.GetZonesInfo(
       svar_pb2.GetZonesInfoRequest(), metadata=metadata
   ).zones_info[0].zone_id

   zone_vals = []
   for msg in sv.GetSolutionVariableData(
       svar_pb2.GetSolutionVariableDataRequest(
           name="SV_P", domain_id=1, zones=[zone_id],
           chunk_size=256 * 1024, provide_bytes_stream=False,
       ),
       metadata=metadata,
   ):
       if msg.WhichOneof("array") == "payload":
           kind = msg.payload.WhichOneof("chunk")
           if kind == "double_payload":
               zone_vals.extend(msg.payload.double_payload.payloads)
           elif kind == "float_payload":
               zone_vals.extend(msg.payload.float_payload.payloads)

   za = np.array(zone_vals)
   print(f"Zone SV_P — {len(za)} cells  mean: {za.mean():.4e}")

   channel.close()
