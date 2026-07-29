Reading and writing simulation data
====================================

Python client examples for the ``FieldData``, ``Reduction``, and
``SolutionVariable`` gRPC services.

See :doc:`../../api/services/field_data`, :doc:`../../api/services/reduction`,
and :doc:`../../api/services/solution_variable`
for these services' complete reference material.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import (
       field_data_pb2, field_data_pb2_grpc,
       reduction_pb2, reduction_pb2_grpc,
       solution_variable_pb2, solution_variable_pb2_grpc,
   )

   channel = grpc.insecure_channel("<server-address>")
   metadata = [("password", "<password>")]

   field_data_stub = field_data_pb2_grpc.FieldDataStub(channel)
   reduction_stub = reduction_pb2_grpc.ReductionStub(channel)
    solution_variable_stub = solution_variable_pb2_grpc.SolutionVariableStub(channel)

Checking data availability
---------------------------

``IsDataAvailable`` confirms that solution data is loaded; ``IsBoundaryValuesEnabled``
checks whether boundary face values are exposed.

.. code-block:: python
   :caption: Python

   data_availability_response = field_data_stub.IsDataAvailable(
       field_data_pb2.IsDataAvailableRequest(),
       metadata=metadata,
   )
   print(data_availability_response.is_data_available)  # -> True

   boundary_values_response = field_data_stub.IsBoundaryValuesEnabled(
       field_data_pb2.IsBoundaryValuesEnabledRequest(),
       metadata=metadata,
   )
   print(boundary_values_response.is_boundary_values_enabled)  # -> True

Enumerating surfaces
---------------------

``GetSurfacesInfo`` lists every surface the solver exposes together with its
numeric IDs.

.. code-block:: python
   :caption: Python

   surfaces_info_response = field_data_stub.GetSurfacesInfo(
       field_data_pb2.GetSurfacesInfoRequest(),
       metadata=metadata,
   )
   for info in surfaces_info_response.surface_info:
       ids = [sid.id for sid in info.surface_ids]
       print(f"{info.surface_name}: surface_ids={ids}")
   # -> cold-inlet: surface_ids=[1]
   # -> hot-inlet:  surface_ids=[2]
   # -> outlet:     surface_ids=[3]
   # -> wall:       surface_ids=[4]

Enumerating scalar and vector fields
--------------------------------------

``GetFieldsInfo`` and ``GetVectorFieldsInfo`` return the information of all
available scalar and vector quantities.

.. code-block:: python
   :caption: Python

   scalar_fields = [
       f.solver_name
       for f in field_data_stub.GetFieldsInfo(
           field_data_pb2.GetFieldsInfoRequest(), metadata=metadata
       ).field_info
   ]
   print(scalar_fields[:4])  # -> ['pressure', 'temperature', 'velocity-magnitude', ...]

   vector_fields = [
       vf.display_name
       for vf in field_data_stub.GetVectorFieldsInfo(
           field_data_pb2.GetVectorFieldsInfoRequest(), metadata=metadata
       ).vector_field_info
   ]
   print(vector_fields[:2])  # -> ['Velocity', 'Relative Velocity']

Querying field range
---------------------

``GetRange`` returns the minimum and maximum of a scalar field on a surface.

.. code-block:: python
   :caption: Python

   # Use the first surface and the first scalar field discovered above.
   surface_id = surfaces_info_response.surface_info[0].surface_ids[0].id
   field_name = scalar_fields[0]

   range_response = field_data_stub.GetRange(
       field_data_pb2.GetRangeRequest(
           field_name=field_name,
           surface_ids=[field_data_pb2.SurfaceId(id=surface_id)],
           node_value=True,
       ),
       metadata=metadata,
   )
   print(range_response.minimum)  # -> 101325.0
   print(range_response.maximum)  # -> 103521.4

Streaming a scalar field
-------------------------

``GetScalarField`` streams nodal or cell-centre scalar values off one or more
surfaces; each chunk contains the surface ID and the value array.

.. code-block:: python
   :caption: Python

   for scalar_field_chunk in field_data_stub.GetScalarField(
       field_data_pb2.GetScalarFieldRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=surface_id)],
           scalar_field="pressure",
           node_value=True,
           boundary_values=False,
       ),
       metadata=metadata,
   ):
       scalar_data = scalar_field_chunk.scalar_field_data
       print(f"surface {scalar_data.surface_id.id}: {len(scalar_data.scalar_field.data)} values")
   # -> surface 1: 2048 values

Streaming a vector field
-------------------------

``GetVectorField`` streams velocity or any other vector quantity; each chunk
contains a list of ``VectorComponent`` objects.

.. code-block:: python
   :caption: Python

   vector_name = vector_fields[0]  # e.g. 'Velocity'

   for vector_field_chunk in field_data_stub.GetVectorField(
       field_data_pb2.GetVectorFieldRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=surface_id)],
           scalar_field=scalar_fields[0],
           vector_field=vector_name,
           node_value=True,
       ),
       metadata=metadata,
   ):
       vector_data = vector_field_chunk.vector_field_data
       print(f"surface {vector_data.surface_id.id}: {len(vector_data.vector.vector_components)} vectors")
   # -> surface 1: 2048 vectors

Streaming surface geometry
---------------------------

``GetSurfaces`` streams vertex coordinates and face connectivity for a surface.

.. code-block:: python
   :caption: Python

   stream = field_data_stub.GetSurfaces(
       field_data_pb2.GetSurfacesRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=surface_id)],
           overset_mesh=False,
       ),
       metadata=metadata,
   )
   for chunk in stream:
       print(hasattr(chunk, "surface_data"))  # -> True

Bulk streaming with ``GetFields``
-----------------------------------

``GetFields`` combines surface geometry, scalar, and vector requests into a
single server-streaming call; each chunk carries a ``WhichOneof("chunk")`` tag.

.. code-block:: python
   :caption: Python

   stream = field_data_stub.GetFields(
       field_data_pb2.GetFieldsRequest(
           provide_bytes_stream=False,
           surface_requests=[
               field_data_pb2.SurfaceRequest(
                   surface_id=surface_id,
                   provide_vertices=True,
                   provide_faces=True,
               )
           ],
           scalar_field_requests=[
               field_data_pb2.ScalarFieldRequest(
                   surface_id=surface_id,
                   scalar_field_name="pressure",
                   data_location=field_data_pb2.DATA_LOCATION_NODES,
                   provide_boundary_values=False,
               )
           ],
       ),
       metadata=metadata,
   )
   valid_chunks = {"byte_payload", "double_payload", "float_payload",
                   "long_payload", "int_payload", "payload_info"}
   for chunk in stream:
       chunk_type = chunk.WhichOneof("chunk")
       if chunk_type is not None:
           print(chunk_type in valid_chunks)  # -> True

Opening a persistent field stream
-----------------------------------

``BeginFieldsStreaming`` opens a long-lived server-streaming channel; pass
``provide_bytes_stream=True`` to receive raw bytes instead of typed messages.

.. code-block:: python
   :caption: Python

   stream = field_data_stub.BeginFieldsStreaming(
       field_data_pb2.BeginFieldsStreamingRequest(
           chunk_size=262144,
           provide_bytes_stream=False,
       ),
       metadata=metadata,
   )
   print(stream is not None)  # -> True
   stream.cancel()

   # Raw-bytes variant.
   byte_stream = field_data_stub.BeginFieldsStreaming(
       field_data_pb2.BeginFieldsStreamingRequest(
           chunk_size=262144,
           provide_bytes_stream=True,
       ),
       metadata=metadata,
   )
   print(byte_stream is not None)  # -> True
   byte_stream.cancel()

Streaming pathlines
--------------------

``GetPathlinesField`` integrates particle tracks forward or backward from
release surfaces and streams the result.

.. code-block:: python
   :caption: Python

   stream = field_data_stub.GetPathlinesField(
       field_data_pb2.GetPathlinesFieldRequest(
           release_froms=[field_data_pb2.SurfaceId(id=surface_id)],
           field1="pressure",
           node_value=True,
           steps=100,
           step_size=1.0,
           skip=0,
           reverse=False,
       ),
       metadata=metadata,
   )
   print(stream is not None)  # -> True
   stream.cancel()

Geometric reductions
---------------------

``Area``, ``Centroid``, and ``Volume`` return surface area, the area-weighted
centroid, and volume of named zones.

.. code-block:: python
   :caption: Python

   area = reduction_stub.Area(
       reduction_pb2.AreaRequest(locations=["cold-inlet", "outlet"]),
       metadata=metadata,
   )
   print(area.value.double_state > 0)  # -> True

   centroid = reduction_stub.Centroid(
       reduction_pb2.CentroidRequest(locations=["cold-inlet", "outlet"]),
       metadata=metadata,
   )
   centroid_coords = centroid.value
   print(isinstance(centroid_coords.x, float))  # -> True
   print(f"centroid: ({centroid_coords.x:.4g}, {centroid_coords.y:.4g}, {centroid_coords.z:.4g})")
   # -> centroid: (0.2208, 0.0, 0.1016)

   vol = reduction_stub.Volume(
       reduction_pb2.VolumeRequest(locations=["elbow-fluid"]),
       metadata=metadata,
   )
   print(vol.value.double_state > 0)  # -> True

Statistical reductions
-----------------------

``Count``, ``CountIf``, ``Minimum``, and ``Maximum`` aggregate element counts
and field extrema; ``CountIf`` accepts a Boolean expression to filter elements.

.. code-block:: python
   :caption: Python

   count = reduction_stub.Count(
       reduction_pb2.CountRequest(locations=["cold-inlet", "outlet"]),
       metadata=metadata,
   )
   print(count.value.int64_state > 0)  # -> True

   count_if = reduction_stub.CountIf(
       reduction_pb2.CountIfRequest(
           expression="AbsolutePressure > 0[Pa]",
           locations=["cold-inlet", "outlet"],
       ),
       metadata=metadata,
   )
   print(count_if.value.int64_state >= 0)             # -> True
   print(count_if.value.int64_state <=
         count.value.int64_state)                     # -> True

   min_result = reduction_stub.Minimum(
       reduction_pb2.MinimumRequest(
           expression="AbsolutePressure", locations=["elbow-fluid"]
       ),
       metadata=metadata,
   )
   max_result = reduction_stub.Maximum(
       reduction_pb2.MaximumRequest(
           expression="AbsolutePressure", locations=["elbow-fluid"]
       ),
       metadata=metadata,
   )
   print(min_result.value.double_state <= max_result.value.double_state)  # -> True

Surface-weighted averages and integrals
----------------------------------------

``AreaAve`` and ``AreaInt`` compute area-weighted statistics; ``AreaInt``
equals ``AreaAve`` × ``Area`` to within rounding.

.. code-block:: python
   :caption: Python

   area_ave = reduction_stub.AreaAve(
       reduction_pb2.AreaAveRequest(
           expression="AbsolutePressure",
           locations=["cold-inlet", "outlet"],
       ),
       metadata=metadata,
   )
   print(area_ave.value.double_state)  # -> 101534.7

   area_int = reduction_stub.AreaInt(
       reduction_pb2.AreaIntRequest(
           expression="AbsolutePressure",
           locations=["cold-inlet", "outlet"],
       ),
       metadata=metadata,
   )
   print(area_int.value.double_state)  # -> 0.8712  (Pa·m²)

Mass-flow averages and integrals
---------------------------------

``MassFlowAve``, ``MassFlowAveAbs``, and ``MassFlowInt`` weight values by the
local mass flux instead of area.

.. code-block:: python
   :caption: Python

   mf_ave = reduction_stub.MassFlowAve(
       reduction_pb2.MassFlowAveRequest(
           expression="AbsolutePressure",
           locations=["cold-inlet", "outlet"],
       ),
       metadata=metadata,
   )
   print(mf_ave.value.double_state)  # -> 101472.3

   mf_ave_abs = reduction_stub.MassFlowAveAbs(
       reduction_pb2.MassFlowAveAbsRequest(
           expression="AbsolutePressure",
           locations=["cold-inlet", "outlet"],
       ),
       metadata=metadata,
   )
   print(mf_ave_abs.value.double_state)  # -> 101472.3

   mf_int = reduction_stub.MassFlowInt(
       reduction_pb2.MassFlowIntRequest(
           expression="AbsolutePressure",
           locations=["cold-inlet", "outlet"],
       ),
       metadata=metadata,
   )
   print(mf_int.value.double_state)  # -> 0.0423  (Pa·kg/s)

Volume-weighted averages and integrals
---------------------------------------

``VolumeAve`` and ``VolumeInt`` aggregate field quantities over cell-zone
volumes; the average always lies between ``Minimum`` and ``Maximum``.

.. code-block:: python
   :caption: Python

   vol_ave = reduction_stub.VolumeAve(
       reduction_pb2.VolumeAveRequest(
           expression="AbsolutePressure",
           locations=["elbow-fluid"],
       ),
       metadata=metadata,
   )
   print(min_result.value.double_state
         <= vol_ave.value.double_state
         <= max_result.value.double_state)   # -> True

   vol_int = reduction_stub.VolumeInt(
       reduction_pb2.VolumeIntRequest(
           expression="AbsolutePressure",
           locations=["elbow-fluid"],
       ),
       metadata=metadata,
   )
   print(vol_int.value.double_state > 0)  # -> True

Mass averages and integrals
-----------------------------

``MassAve`` and ``MassInt`` weight values by the local cell mass.

.. code-block:: python
   :caption: Python

   mass_ave = reduction_stub.MassAve(
       reduction_pb2.MassAveRequest(
           expression="AbsolutePressure",
           locations=["elbow-fluid"],
       ),
       metadata=metadata,
   )
   print(mass_ave.value.double_state > 0)  # -> True

   mass_int = reduction_stub.MassInt(
       reduction_pb2.MassIntRequest(
           expression="AbsolutePressure",
           locations=["elbow-fluid"],
       ),
       metadata=metadata,
   )
   print(mass_int.value.double_state > 0)  # -> True

Force decomposition
--------------------

``Force`` equals the sum of ``PressureForce`` and ``ViscousForce`` on any
boundary zone; ``Moment`` returns the moment vector.

.. code-block:: python
   :caption: Python

   pressure_force = reduction_stub.PressureForce(
       reduction_pb2.PressureForceRequest(locations=["cold-inlet", "outlet"]),
       metadata=metadata,
   ).value
   viscous_force = reduction_stub.ViscousForce(
       reduction_pb2.ViscousForceRequest(locations=["cold-inlet", "outlet"]),
       metadata=metadata,
   ).value
   total_force = reduction_stub.Force(
       reduction_pb2.ForceRequest(locations=["cold-inlet", "outlet"]),
       metadata=metadata,
   ).value
   print(f"pressure force: ({pressure_force.x:.4g}, {pressure_force.y:.4g}, {pressure_force.z:.4g})")
   # -> pressure force: (-0.0231, 0.0, 1.452)
   print(f"viscous  force: ({viscous_force.x:.4g}, {viscous_force.y:.4g}, {viscous_force.z:.4g})")
   # -> viscous  force: (-0.0012, 0.0, 0.0034)
   print(f"total    force: ({total_force.x:.4g}, {total_force.y:.4g}, {total_force.z:.4g})")
   # -> total    force: (-0.0243, 0.0, 1.455)

   moment = reduction_stub.Moment(
       reduction_pb2.MomentRequest(
           expression="AbsolutePressure",
           locations=["cold-inlet", "outlet"],
       ),
       metadata=metadata,
   )
   moment_coords = moment.value
   print(f"moment: ({moment_coords.x:.4g}, {moment_coords.y:.4g}, {moment_coords.z:.4g})")
   # -> moment: (0.0, -0.2341, 0.0)

Conditional sums
-----------------

``Sum`` integrates an expression weighted by a field; ``SumIf`` restricts
integration to elements matching a Boolean condition.

.. code-block:: python
   :caption: Python

   total = reduction_stub.Sum(
       reduction_pb2.SumRequest(
           expression="AbsolutePressure",
           locations=["cold-inlet", "outlet"],
           weight="Area",
       ),
       metadata=metadata,
   )
   print(total.value.double_state > 0)  # -> True

   conditional = reduction_stub.SumIf(
       reduction_pb2.SumIfRequest(
           expression="AbsolutePressure",
           condition="AbsolutePressure > 0[Pa]",
           locations=["cold-inlet", "outlet"],
           weight="Area",
       ),
       metadata=metadata,
   )
   print(conditional.value.double_state >= 0)                         # -> True
   print(conditional.value.double_state <= total.value.double_state)  # -> True

Discovering zones and solution variables
-----------------------------------------

``GetZonesInfo`` enumerates every domain and zone; ``GetSolutionVariableInfo``
lists the solution variables (and their field types) available on a given zone.

.. code-block:: python
   :caption: Python

   zones_info_response = solution_variable_stub.GetZonesInfo(
       solution_variable_pb2.GetZonesInfoRequest(),
       metadata=metadata,
   )
   # Inspect domains.
   for d in zones_info_response.domains_info:
       print(f"domain {d.domain_id}: {d.name}")
   # -> domain 1: mixture

   # Inspect zones.
   for z in zones_info_response.zones_info:
       print(f"zone {z.zone_id}: {z.name}  type={z.thread_type}")
   # -> zone 2: elbow-fluid  type=THREAD_TYPE_CELL
   # -> zone 3: cold-inlet   type=THREAD_TYPE_FACE
   # -> zone 4: outlet       type=THREAD_TYPE_FACE

   # Find the first cell zone.
   cell_zone = next(
       z for z in zones_info_response.zones_info
       if z.thread_type == solution_variable_pb2.THREAD_TYPE_CELL
   )
   print(cell_zone.zone_id)  # -> 2

   # List solution variables on that zone.
   svar_info_response = solution_variable_stub.GetSolutionVariableInfo(
       solution_variable_pb2.GetSolutionVariableInfoRequest(
           domain_id=1,
           zone_id=cell_zone.zone_id,
       ),
       metadata=metadata,
   )
   names = [sv.name for sv in svar_info_response.svars_info]
   print("SV_P" in names)   # -> True
   print(names[:4])          # -> ['SV_P', 'SV_T', 'SV_U', 'SV_V']

Reading solution variable data
--------------------------------

``GetSolutionVariableData`` streams raw per-cell arrays; the first response
chunk is always a ``payload_info`` frame describing size and type, followed by
``payload`` frames.

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import field_data_pb2 as fd_pb2

   stream = solution_variable_stub.GetSolutionVariableData(
       solution_variable_pb2.GetSolutionVariableDataRequest(
           chunk_size=256 * 1024,
           provide_bytes_stream=False,
           name="SV_P",
           domain_id=1,
           zones=[cell_zone.zone_id],
       ),
       metadata=metadata,
   )

   values = []
   for chunk in stream:
       part = chunk.WhichOneof("array")
       if part == "payload_info":
           print(f"zone {chunk.payload_info.zone}: "
                 f"{chunk.payload_info.field_size} cells")
           # -> zone 2: 14756 cells
       elif part == "payload":
           payload_type = chunk.payload.WhichOneof("chunk")
           if payload_type == "double_payload":
               values.extend(chunk.payload.double_payload.payloads)
           elif payload_type == "float_payload":
               values.extend(chunk.payload.float_payload.payloads)

   print(len(values))  # -> 14756

Writing solution variable data
--------------------------------

``SetSolutionVariableData`` accepts a client-streaming call; yield a header
frame, then a ``payload_info`` frame, then one or more payload frames.

.. code-block:: python
   :caption: Python

   def _set_stream(name, domain_id, zone_id, data, chunk_size=256 * 1024):
       """Yield the header, info, and payload messages for a write call."""
       yield solution_variable_pb2.SetSolutionVariableDataRequest(
           header=solution_variable_pb2.SolutionVariableHeader(name=name, domain_id=domain_id)
       )
       yield solution_variable_pb2.SetSolutionVariableDataRequest(
           payload_info=solution_variable_pb2.Info(
               field_type=fd_pb2.FIELD_TYPE_DOUBLE_ARRAY,
               field_size=len(data),
               zone=zone_id,
           )
       )
       item_size = 8  # float64
       max_per_chunk = max(1, chunk_size // item_size)
       for start in range(0, len(data), max_per_chunk):
           chunk = data[start : start + max_per_chunk]
           yield solution_variable_pb2.SetSolutionVariableDataRequest(
               payload=solution_variable_pb2.Payload(
                   double_payload=fd_pb2.DoublePayload(payloads=chunk)
               )
           )

   # Write the values read above back unchanged.
   set_svar_response = solution_variable_stub.SetSolutionVariableData(
       _set_stream("SV_P", domain_id=1, zone_id=cell_zone.zone_id, data=values),
       metadata=metadata,
   )
   print(isinstance(set_svar_response, solution_variable_pb2.SetSolutionVariableDataResponse))  # -> True

See :doc:`../../api/services/field_data`, :doc:`../../api/services/reduction`,
and :doc:`../../api/services/solution_variable` for the complete reference material.
