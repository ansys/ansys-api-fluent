FieldData
=========

Overview
--------

The ``FieldData`` service streams simulation results — scalar fields, vector
fields, surface geometry, mesh nodes and elements, pathlines, and particle
tracks — out of a running Fluent session. It also provides discovery RPCs so
you can enumerate available surfaces and fields before requesting data.

Most data-retrieval RPCs are **server-streaming**: they return one or more
typed payload chunks that you iterate over. The ``SetSolutionVariableData``
RPC for writing solution variable values is on the Solution Variables service
(:doc:`svar`).

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import field_data_pb2, field_data_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = field_data_pb2_grpc.FieldDataStub(channel)

Runtime API
-----------

Availability checks
~~~~~~~~~~~~~~~~~~~

Before requesting field data, check whether solution data and boundary values
are currently available. These calls are cheap and save you from issuing
streaming RPCs against an empty or uninitialised solver.

- ``IsDataAvailable(IsDataAvailableRequest)`` → ``IsDataAvailableResponse``
  Response field: ``is_data_available: bool``
- ``IsBoundaryValuesEnabled(IsBoundaryValuesEnabledRequest)`` → ``IsBoundaryValuesEnabledResponse``
  Response field: ``is_boundary_values_enabled: bool``

.. code-block:: python
   :caption: Python

   avail = stub.IsDataAvailable(
       field_data_pb2.IsDataAvailableRequest(), metadata=metadata,
   )
   bv_enabled = stub.IsBoundaryValuesEnabled(
       field_data_pb2.IsBoundaryValuesEnabledRequest(), metadata=metadata,
   )
   print(f"Data available: {avail.is_data_available}")
   print(f"Boundary values enabled: {bv_enabled.is_boundary_values_enabled}")

Discovery: surfaces and fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enumerate the surfaces and fields in the current session before requesting
data. Use the IDs and names returned here in subsequent streaming calls.

- ``GetSurfacesInfo(GetSurfacesInfoRequest)`` → ``GetSurfacesInfoResponse``
- ``GetFieldsInfo(GetFieldsInfoRequest)`` → ``GetFieldsInfoResponse``
- ``GetVectorFieldsInfo(GetVectorFieldsInfoRequest)`` → ``GetVectorFieldsInfoResponse``
- ``GetRange(GetRangeRequest)`` → ``GetRangeResponse``
  Request fields: ``field_name: string``, ``surface_ids: repeated SurfaceId``, ``node_value: bool``
  Response fields: ``minimum: double``, ``maximum: double``

.. code-block:: python
   :caption: Python

   # Surfaces
   surf_resp = stub.GetSurfacesInfo(
       field_data_pb2.GetSurfacesInfoRequest(), metadata=metadata,
   )
   surface_ids = {}
   for info in surf_resp.surface_info:
       for sid in info.surface_ids:
           surface_ids[sid.id] = info.surface_name
           print(f"  Surface id={sid.id}  name={info.surface_name}")

   # Scalar fields
   field_resp = stub.GetFieldsInfo(
       field_data_pb2.GetFieldsInfoRequest(), metadata=metadata,
   )
   for f in field_resp.field_info:
       print(f"  Scalar: {f.solver_name!r}  ({f.display_name})")

   # Vector fields
   vec_resp = stub.GetVectorFieldsInfo(
       field_data_pb2.GetVectorFieldsInfoRequest(), metadata=metadata,
   )
   for v in vec_resp.vector_field_info:
       print(f"  Vector: {v.solver_name!r}  ({v.display_name})")

   # Range of a scalar field on the first surface
   first_id = next(iter(surface_ids))
   rng = stub.GetRange(
       field_data_pb2.GetRangeRequest(
           field_name="temperature",
           surface_ids=[field_data_pb2.SurfaceId(id=first_id)],
           node_value=True,
       ),
       metadata=metadata,
   )
   print(f"Temperature range: {rng.minimum:.4f} — {rng.maximum:.4f}")

Scalar field streaming
~~~~~~~~~~~~~~~~~~~~~~

``GetFields`` is the primary way to stream one or more scalar fields in a
single request. Each response chunk contains either metadata (``payload_info``)
or a typed numeric payload. Accumulate chunks by field and surface.

``GetScalarField`` is the simpler single-field alternative.

- ``GetFields(GetFieldsRequest)`` → ``stream GetFieldsResponse``
- ``GetScalarField(GetScalarFieldRequest)`` → ``stream GetScalarFieldResponse``

.. code-block:: python
   :caption: Python

   # --- GetFields (multi-field batch) ---
   request = field_data_pb2.GetFieldsRequest(
       provide_bytes_stream=False,
       chunk_size=256 * 1024,
       scalar_field_requests=[
           field_data_pb2.ScalarFieldRequest(
               surface_id=first_id,
               scalar_field_name="temperature",
               data_location=field_data_pb2.DataLocation.DATA_LOCATION_NODES,
               provide_boundary_values=False,
           )
       ],
   )
   all_values = []
   for chunk in stub.GetFields(request, metadata=metadata):
       kind = chunk.WhichOneof("chunk")
       if kind == "double_payload":
           all_values.extend(chunk.double_payload.payloads)
       elif kind == "float_payload":
           all_values.extend(chunk.float_payload.payloads)
   print(f"Received {len(all_values)} temperature values")

   # --- GetScalarField (single-field, simpler) ---
   # GetScalarFieldRequest fields: surface_ids (repeated SurfaceId), scalar_field (string),
   # node_value (bool), boundary_values (bool).
   # GetScalarFieldResponse has scalar_field_data: ScalarFieldData with scalar_field.data.
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
       print(f"  Pressure: surface {sfd.surface_id.id}  values={len(sfd.scalar_field.data)}")

Vector field streaming
~~~~~~~~~~~~~~~~~~~~~~

Retrieve vector field data (velocity, flux, etc.) on selected surfaces.

- ``GetVectorField(GetVectorFieldRequest)`` → ``stream GetVectorFieldResponse``

.. code-block:: python
   :caption: Python

   # GetVectorFieldRequest fields: surface_ids (repeated SurfaceId), vector_field (string),
   # node_value (bool). scalar_field (string) is optional — used for scalar colouring.
   # GetVectorFieldResponse has vector_field_data: VectorFieldData with
   # vector.vector_components (repeated VectorComponents with x, y, z doubles).
   for resp in stub.GetVectorField(
       field_data_pb2.GetVectorFieldRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=first_id)],
           vector_field="velocity",
           node_value=True,
       ),
       metadata=metadata,
   ):
       vfd = resp.vector_field_data
       print(f"  Velocity: surface {vfd.surface_id.id}  vectors={len(vfd.vector.vector_components)}")

Surface geometry
~~~~~~~~~~~~~~~~

Stream the vertex coordinates and connectivity of a surface. Use
``GetSurfaces`` for surfaces and the mesh-node/element RPCs below for
the solver volume mesh.

- ``GetSurfaces(GetSurfacesRequest)`` → ``stream GetSurfacesResponse``

.. code-block:: python
   :caption: Python

   # GetSurfacesRequest fields: surface_ids (repeated SurfaceId), overset_mesh (bool).
   # GetSurfacesResponse streams SurfaceData messages with points (Coordinate list)
   # and facets (Facet list with node indices).
   for resp in stub.GetSurfaces(
       field_data_pb2.GetSurfacesRequest(
           surface_ids=[field_data_pb2.SurfaceId(id=first_id)],
           overset_mesh=False,
       ),
       metadata=metadata,
   ):
       sd = resp.surface_data
       print(f"  Surface id={sd.surface_id.id}  "
             f"points={len(sd.points)}  facets={len(sd.facets)}")

Solver mesh (nodes and elements)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieve the raw solver mesh — node coordinates at float or double precision,
and element connectivity. These RPCs stream the volumetric mesh, not surfaces.

- ``GetSolverMeshNodesFloat(GetSolverMeshNodesRequest)`` → ``stream GetSolverMeshNodesFloatResponse``
- ``GetSolverMeshNodesDouble(GetSolverMeshNodesRequest)`` → ``stream GetSolverMeshNodesDoubleResponse``
- ``GetSolverMeshElements(GetSolverMeshElementsRequest)`` → ``stream GetSolverMeshElementsResponse``

.. code-block:: python
   :caption: Python

   # GetSolverMeshNodesRequest uses domain_id + thread_id, not zone IDs.
   # The response streams repeated NodeFloat messages, each with id, x, y, z fields.
   node_count = 0
   for resp in stub.GetSolverMeshNodesFloat(
       field_data_pb2.GetSolverMeshNodesRequest(domain_id=1, thread_id=12),
       metadata=metadata,
   ):
       node_count += len(resp.nodes)  # resp.nodes is repeated NodeFloat
   print(f"Total nodes: {node_count}")

   # GetSolverMeshElementsResponse streams repeated Element messages
   # (each with id, element_type, node_ids, and facets for polyhedra).
   element_count = 0
   for resp in stub.GetSolverMeshElements(
       field_data_pb2.GetSolverMeshElementsRequest(domain_id=1, thread_id=12),
       metadata=metadata,
   ):
       element_count += len(resp.elements)
   print(f"Total elements: {element_count}")

Pathlines and particle tracks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stream pathline or particle-track field data for flow visualisation. Both RPCs
follow the same payload-chunk pattern as scalar and vector fields.

- ``GetPathlinesField(GetPathlinesFieldRequest)`` → ``stream GetPathlinesFieldResponse``
- ``GetParticleTracksField(GetParticleTracksFieldRequest)`` → ``stream GetParticleTracksFieldResponse``

.. code-block:: python
   :caption: Python

   # GetPathlinesFieldRequest fields: release_froms (repeated SurfaceId),
   # field1 (string primary scalar), field2 (string secondary scalar), node_value (bool).
   # GetPathlinesFieldResponse has pathline_data: PathlineData with oneof as:
   # pathline_field_data or pathline_metadata.
   for resp in stub.GetPathlinesField(
       field_data_pb2.GetPathlinesFieldRequest(
           release_froms=[field_data_pb2.SurfaceId(id=first_id)],
           field1="velocity-magnitude",
       ),
       metadata=metadata,
   ):
       kind = resp.pathline_data.WhichOneof("as")
       if kind is not None:
           print(f"  Pathlines response: {kind}")

Legacy streaming (BeginFieldsStreaming)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``BeginFieldsStreaming`` is an older, lower-level streaming RPC. Prefer
``GetFields``, ``GetScalarField``, or ``GetVectorField`` for new clients.

- ``BeginFieldsStreaming(BeginFieldsStreamingRequest)`` → ``stream BeginFieldsStreamingResponse``

Payload types
-------------

All numeric payloads are typed. Each chunk response uses a ``oneof`` to carry
exactly one payload type.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - ``oneof`` field
     - Content
   * - ``double_payload``
     - ``DoublePayload`` — ``repeated double payloads``
   * - ``float_payload``
     - ``FloatPayload`` — ``repeated float payloads``
   * - ``int_payload``
     - ``IntPayload`` — ``repeated sint32 payloads``
   * - ``long_payload``
     - ``LongPayload`` — ``repeated sint64 payloads``

A ``payload_info`` chunk precedes the data chunks and contains metadata such
as field type, zone, and size.

See also
--------

- :doc:`svar` — read and write solution variable data by zone
- :doc:`reduction` — compute scalar reductions (area averages, forces, extrema)
- :doc:`monitor` — stream live monitor data as the solver iterates

.. ----------------------------------------------------------------------------
.. The block below is generated by docs/_ext/proto_docgen.py from the matching
.. .proto file in ansys/api/fluent/v1. Edit the proto comments to update it.
.. ----------------------------------------------------------------------------

.. include:: ../../api/_generated/field_data.rst