Meshing Queries Service
========================

The Meshing Queries service provides a broad set of mesh topology, region,
object, adjacency, and diagnostics queries.

Overview
~~~~~~~~

The ``MeshingQueries`` service allows you to:

- Query zones and objects by type, group, name pattern, or filter
- Look up the zone at a spatial location
- Resolve topology relationships (adjacent face/cell zones by edge or node connectivity)
- Retrieve object and region information, including region volumes
- Identify unreferenced, overlapping, free-face, multi-face, and marked-face zones
- Find candidate join pairs for boundary stitching workflows
- Retrieve all cell IDs and numeric cell-quality values

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.meshing_queries``

**Main Classes:**

- ``MeshingQueriesStub``: Client stub for mesh queries
- ``Empty``: Request message for parameterless RPCs
- ``CustomDoubleAndString``: Helper message returned by ``SortRegionsByVolume``
  (fields: ``volume: double``, ``region: string``)
- ``OverlappingBoundingBox``: Helper message returned by ``FindJoinPairs``
  (fields: ``zone_id_1``, ``zone_id_2``, ``bounding_box_mins``, ``bounding_box_maxes``)
- Per-RPC request/response pairs — for example,
  ``GetZonesTypeRequest`` / ``GetZonesTypeResponse``

Core RPC Operations
~~~~~~~~~~~~~~~~~~~

Because this service is extensive, the RPCs are grouped below by workflow type.

Zone Discovery
--------------

Filter or classify zones by type, group, or name pattern.

- ``GetZonesOfType(GetZonesTypeRequest)`` → ``zone_ids``
  Request field: ``type: string``
- ``GetZonesOfGroup(GetZonesGroupRequest)`` → ``zone_ids``
  Request field: ``group: string``
- ``GetFaceZonesOfFilter(GetFaceZonesFilterRequest)`` → ``face_zone_ids``
  Request field: ``filter: string``
- ``GetCellZonesOfFilter(GetCellZonesFilterRequest)`` → ``cell_zone_ids``
  Request field: ``filter: string``
- ``GetEdgeZonesOfFilter(GetEdgeZonesFilterRequest)`` → ``edge_zone_ids``
  Request field: ``filter: string``
- ``GetNodeZonesOfFilter(GetNodeZonesFilterRequest)`` → ``node_zone_ids``
  Request field: ``filter: string``

Example: discover face zones matching a wildcard filter

.. code-block:: python

   response = mesh_stub.GetFaceZonesOfFilter(
      meshing_queries_pb2.GetFaceZonesFilterRequest(filter="*wall*"),
      metadata=metadata,
      timeout=10.0,
   )
   print(f"Found {len(response.face_zone_ids)} face zones")

Spatial Lookup
--------------

Return the zone that contains a given 3-D point.

- ``GetFaceZoneAtLocation(GetFaceZoneLocationRequest)`` → ``face_zone_id``
  Request field: ``location: Point``
- ``GetCellZoneAtLocation(GetCellZoneLocationRequest)`` → ``cell_zone_id``
  Request field: ``location: Point``

Example: identify the face zone at the mesh origin

.. code-block:: python

   response = mesh_stub.GetFaceZoneAtLocation(
      meshing_queries_pb2.GetFaceZoneLocationRequest(
         location=common_api_pb2.Point(x=0.0, y=0.0, z=0.0)
      ),
      metadata=metadata,
      timeout=10.0,
   )
   print(f"Face zone at location: {response.face_zone_id}")

Object Discovery
----------------

Enumerate mesh objects by type, pattern, or filter.

- ``GetObjectsOfType(GetObjectsTypeRequest)`` → ``objects``
  Request field: ``type: string``
- ``GetAllObjectNameList(Empty)`` → ``objects``
- ``GetObjectNameListOfType(GetObjectNameListTypeRequest)`` → ``objects``
  Request field: ``type: string``
- ``GetObjectsOfFilter(GetObjectsFilterRequest)`` → ``objects``
  Request field: ``filter: string``

Object Zone Access
------------------

Retrieve face, edge, or cell zone IDs bound to a named object or a set of objects.

- ``GetFaceZoneIdListOfObject(GetFaceZoneIdListObjectRequest)`` → ``face_zone_ids``
  Request field: ``object: string``
- ``GetEdgeZoneIdListOfObject(GetEdgeZoneIdListObjectRequest)`` → ``edge_zone_ids``
  Request field: ``object: string``
- ``GetCellZoneIdListOfObject(GetCellZoneIdListObjectRequest)`` → ``cell_zone_ids``
  Request field: ``object: string``
- ``GetFaceZonesOfObjects(GetFaceZonesObjectsRequest)`` → ``face_zone_ids``
  Request field: ``object_lists: repeated string``
- ``GetEdgeZonesOfObjects(GetEdgeZonesObjectsRequest)`` → ``edge_zone_ids``
  Request field: ``object_lists: repeated string``

Region and Label Access
-----------------------

Query face zones and region names that are scoped to objects, regions, or labels.

- ``GetFaceZonesSharedByRegionsOfType(GetFaceZonesSharedRegionsTypeRequest)`` → ``shared_face_zone_ids``
  Request fields: ``mesh_object: string``, ``region_type: string``
- ``GetFaceZonesOfRegions(GetFaceZonesRegionsRequest)`` → ``zone_ids``
  Request fields: ``object: string``, ``regions: repeated string``
- ``GetFaceZonesOfLabels(GetFaceZonesLabelsRequest)`` → ``zone_ids``
  Request fields: ``object: string``, ``labels: repeated string``
- ``GetFaceZoneIdListOfLabels(GetFaceZoneIdListLabelsRequest)`` → ``zone_ids``
  Request fields: ``object: string``, ``labels: repeated string``
- ``GetFaceZoneIdListOfRegions(GetFaceZoneIdListRegionsRequest)`` → ``zone_ids``
  Request fields: ``object: string``, ``labels: repeated string``
- ``GetRegionsOfObject(GetRegionsObjectRequest)`` → ``regions``
  Request field: ``object: string``
- ``GetRegionNameListOfObject(GetRegionNameListObjectRequest)`` → ``regions``
  Request field: ``object: string``
- ``GetRegionsOfFilter(GetRegionsFilterRequest)`` → ``regions``
  Request fields: ``object: string``, ``filter: string``
- ``GetRegionNameListOfPattern(GetRegionNameListPatternRequest)`` → ``regions``
  Request fields: ``object: string``, ``region_name_or_pattern: string``
- ``GetRegionsOfFaceZones(GetRegionsFaceZonesRequest)`` → ``regions``
  Request field: ``face_zone_ids: repeated sint64``
- ``GetRegionNameListOfFaceZones(GetRegionNameListFaceZonesRequest)`` → ``regions``
  Request fields: ``face_zone_name_or_pattern: string``, ``face_zone_ids: repeated sint64``
- ``SortRegionsByVolume(SortRegionsVolumeRequest)`` → ``regions: repeated CustomDoubleAndString``
  Request fields: ``object_name: string``, ``order: string`` (``"asc"`` or ``"desc"``)
- ``GetRegionVolume(GetRegionVolumeRequest)`` → ``region_volume``
  Request fields: ``object_name: string``, ``region_name: string``

Example: look up the volume of a named region

.. code-block:: python

   response = mesh_stub.GetRegionVolume(
      meshing_queries_pb2.GetRegionVolumeRequest(
         object_name="fluid",
         region_name="fluid-region-1",
      ),
      metadata=metadata,
      timeout=10.0,
   )
   print(f"Region volume: {response.region_volume}")

Example: list face zones shared by regions of a given type

.. code-block:: python

   response = mesh_stub.GetFaceZonesSharedByRegionsOfType(
      meshing_queries_pb2.GetFaceZonesSharedRegionsTypeRequest(
         mesh_object="fluid",
         region_type="fluid",
      ),
      metadata=metadata,
      timeout=10.0,
   )
   print(f"Shared face zone IDs: {list(response.shared_face_zone_ids)}")

Adjacency and Connectivity
--------------------------

Resolve topological neighbours between zones.

- ``GetAdjacentCellZones(GetAdjacentCellZonesRequest)`` → ``adjacent_cell_zones``
  Request fields: ``zone_name_or_pattern: string``, ``face_zone_ids: repeated sint64``
- ``GetAdjacentFaceZones(GetAdjacentFaceZonesRequest)`` → ``adjacent_boundary_face_zones``
  Request fields: ``zone_name_or_pattern: string``, ``cell_zone_ids: repeated sint64``
- ``GetAdjacentInteriorAndBoundaryFaceZones(GetAdjacentInteriorAndBoundaryFaceZonesRequest)`` → ``adjacent_interior_and_boundary_face_zones``
  Request fields: ``zone_name_or_pattern: string``, ``cell_zone_ids: repeated sint64``
- ``GetAdjacentZonesByEdgeConnectivity(GetAdjacentZonesEdgeConnectivityRequest)`` → ``adjacent_zone_ids``
  Request fields: ``zone_name_or_pattern: string``, ``zone_ids: repeated sint64``
- ``GetAdjacentZonesByNodeConnectivity(GetAdjacentZonesNodeConnectivityRequest)`` → ``adjacent_zone_ids``
  Request fields: ``zone_name_or_pattern: string``, ``zone_ids: repeated sint64``
- ``GetSharedBoundaryZones(GetSharedBoundaryZonesRequest)`` → ``shared_boundary_zone_ids``
  Request fields: ``cell_zone_name_or_pattern: string``, ``cell_zone_ids: repeated sint64``
- ``GetInteriorZonesConnectedToCellZones(GetInteriorZonesConnectedCellZonesRequest)`` → ``interior_zone_ids``
  Request fields: ``cell_zone_name_or_pattern: string``, ``face_zone_ids: repeated sint64``

Example: find cell zones adjacent to a face zone

.. code-block:: python

   response = mesh_stub.GetAdjacentCellZones(
      meshing_queries_pb2.GetAdjacentCellZonesRequest(
         zone_name_or_pattern="*",
         face_zone_ids=[1001],
      ),
      metadata=metadata,
      timeout=10.0,
   )
   print(f"Adjacent cell zones: {list(response.adjacent_cell_zones)}")

Prism, Tet, Baffle, and Wrap Queries
-------------------------------------

Inspect specialised zone categories.

- ``GetPrismCellZones(GetPrismCellZonesRequest)`` → ``prism_cell_zones``
  Request fields: ``zone_name_or_pattern: string``, ``zones: repeated string``
- ``GetTetCellZones(GetTetCellZonesRequest)`` → ``tet_cell_zones``
  Request fields: ``zone_name_or_pattern: string``, ``zones: repeated string``
- ``GetFaceZonesWithZoneSpecificPrismsApplied(Empty)`` → ``face_zone_ids``
- ``GetFaceZonesOfPrismControls(GetFaceZonesPrismControlsRequest)`` → ``face_zone_ids``
  Request field: ``control_name: string``
- ``GetBaffles(GetBafflesRequest)`` → ``baffle_zone_ids``
  Request field: ``face_zone_ids: repeated sint64``
- ``GetEmbeddedBaffles(Empty)`` → ``embedded_baffles_zone_ids``
- ``GetWrappedZones(Empty)`` → ``wrapped_face_zone_ids``

Unreferenced Zone Detection
---------------------------

Identify zones that are not associated with any object or topology reference.

- ``GetUnreferencedEdgeZones(Empty)`` → ``unreferenced_edge_zone_ids``
- ``GetUnreferencedFaceZones(Empty)`` → ``unreferenced_face_zone_ids``
- ``GetUnreferencedCellZones(Empty)`` → ``unreferenced_cell_zone_ids``
- ``GetUnreferencedEdgeZonesOfFilter(GetUnreferencedEdgeZonesFilterRequest)`` → ``unreferenced_edge_zone_ids``
  Request field: ``filter: string``
- ``GetUnreferencedFaceZonesOfFilter(GetUnreferencedFaceZonesFilterRequest)`` → ``unreferenced_face_zone_ids``
  Request field: ``filter: string``
- ``GetUnreferencedCellZonesOfFilter(GetUnreferencedCellZonesFilterRequest)`` → ``unreferenced_cell_zone_ids``
  Request field: ``filter: string``
- ``GetUnreferencedEdgeZoneIdListOfPattern(GetUnreferencedEdgeZoneIdListPatternRequest)`` → ``unreferenced_edge_zone_ids``
  Request field: ``pattern: string``
- ``GetUnreferencedFaceZoneIdListOfPattern(GetUnreferencedFaceZoneIdListPatternRequest)`` → ``unreferenced_face_zone_ids``
  Request field: ``pattern: string``
- ``GetUnreferencedCellZoneIdListOfPattern(GetUnreferencedCellZoneIdListPatternRequest)`` → ``unreferenced_cell_zone_ids``
  Request field: ``pattern: string``

Zone Sizing, Quality, and Diagnostics
--------------------------------------

Rank zones by size, detect mesh defects, find join candidates, and retrieve cell data.

- ``GetMaxsizeCellZoneByVolume(GetMaxsizeCellZoneVolumeRequest)`` → ``cell_zone_id``
  Request fields: ``cell_zone_pattern: string``, ``cell_zone_ids: repeated sint64``, ``cell_zone_names: repeated string``
- ``GetMaxsizeCellZoneByCount(GetMaxsizeCellZoneCountRequest)`` → ``cell_zone_id``
  Request fields: ``cell_zone_pattern: string``, ``cell_zone_ids: repeated sint64``, ``cell_zone_names: repeated string``
- ``GetMinsizeFaceZoneByArea(GetMinsizeFaceZoneAreaRequest)`` → ``face_zone_id``
  Request fields: ``face_zone_pattern: string``, ``face_zone_ids: repeated sint64``, ``face_zone_names: repeated string``
- ``GetMinsizeFaceZoneByCount(GetMinsizeFaceZoneCountRequest)`` → ``face_zone_id``
  Request fields: ``face_zone_pattern: string``, ``face_zone_ids: repeated sint64``, ``face_zone_names: repeated string``
- ``GetFaceZoneListByMaximumEntityCount(GetFaceZoneListMaximumEntityCountRequest)`` → ``face_zone_ids``
  Request fields: ``maximum_entity_count: sint64``, ``only_boundary: bool``
- ``GetEdgeZoneListByMaximumEntityCount(GetEdgeZoneListMaximumEntityCountRequest)`` → ``edge_zone_ids``
  Request fields: ``maximum_entity_count: sint64``, ``only_boundary: bool``
- ``GetCellZoneListByMaximumEntityCount(GetCellZoneListMaximumEntityCountRequest)`` → ``cell_zone_ids``
  Request field: ``maximum_entity_count: sint64``
- ``GetFaceZoneListByMaximumZoneArea(GetFaceZoneListMaximumZoneAreaRequest)`` → ``face_zone_ids``
  Request field: ``maximum_zone_area: sint64``
- ``GetFaceZoneListByMinimumZoneArea(GetFaceZoneListMinimumZoneAreaRequest)`` → ``face_zone_ids``
  Request field: ``minimum_zone_area: sint64``
- ``GetZonesWithFreeFaces(GetZonesFreeFacesRequest)`` → ``free_face_zone_ids``
  Request fields: ``face_zone_pattern: string``, ``face_zone_ids: repeated sint64``, ``face_zone_names: repeated string``
- ``GetZonesWithMultiFaces(GetZonesMultiFacesRequest)`` → ``multi_connected_face_zone_ids``
  Request fields: ``face_zone_pattern: string``, ``face_zone_ids: repeated sint64``, ``face_zone_names: repeated string``
- ``GetOverlappingFaceZones(GetOverlappingFaceZonesRequest)`` → ``overlapping_face_zone_ids``
  Request fields: ``face_zone_name_or_pattern: string``, ``area_tolerance: double``, ``distance_tolerance: double``
- ``GetZonesWithMarkedFaces(GetZonesMarkedFacesRequest)`` → ``marked_face_zone_ids``
  Request fields: ``face_zone_pattern: string``, ``face_zone_ids: repeated sint64``, ``face_zone_names: repeated string``
- ``FindJoinPairs(FindJoinPairsRequest)`` → ``pairs: repeated OverlappingBoundingBox``
  Request fields: ``face_zone_name_or_pattern: string``, ``face_zone_ids: repeated sint64``, ``face_zone_names: repeated string``, ``join_tolerance: double``, ``absolute_tolerance: bool``, ``join_angle: double``
- ``GetAllCellsIds(GetAllCellsIdsRequest)`` → ``cell_ids``
- ``GetAllCellsQuality(GetAllCellsQualityRequest)`` → ``cells_and_quality: string``, ``cell_values: repeated double``
  Request field: ``as_string: bool`` — set to ``True`` to also populate the human-readable ``cells_and_quality`` string

Example: detect overlapping face zones with tolerances

.. code-block:: python

   response = mesh_stub.GetOverlappingFaceZones(
      meshing_queries_pb2.GetOverlappingFaceZonesRequest(
         face_zone_name_or_pattern="*interface*",
         area_tolerance=1.0e-8,
         distance_tolerance=1.0e-5,
      ),
      metadata=metadata,
      timeout=20.0,
   )
   print(f"Overlapping face zones: {list(response.overlapping_face_zone_ids)}")

Complete Example
~~~~~~~~~~~~~~~~

An end-to-end workflow that resolves a face zone by location, walks adjacency,
inspects object regions, checks for overlap, and retrieves numeric cell quality values.

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import common_api_pb2
   from ansys.api.fluent.v1 import meshing_queries_pb2, meshing_queries_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"


   def query_mesh_workflow():
      channel = grpc.insecure_channel(f"{HOST}:{PORT}")
      metadata = [("password", PASSWORD)]
      stub = meshing_queries_pb2_grpc.MeshingQueriesStub(channel)

      try:
         # Step 1: Identify the face zone at a spatial location.
         face_loc_resp = stub.GetFaceZoneAtLocation(
            meshing_queries_pb2.GetFaceZoneLocationRequest(
               location=common_api_pb2.Point(x=0.0, y=0.0, z=0.0)
            ),
            metadata=metadata,
            timeout=10.0,
         )
         face_zone_id = face_loc_resp.face_zone_id
         print(f"Face zone at origin: {face_zone_id}")

         # Step 2: Find cell zones adjacent to that face zone.
         adjacent_cell_resp = stub.GetAdjacentCellZones(
            meshing_queries_pb2.GetAdjacentCellZonesRequest(
               zone_name_or_pattern="*",
               face_zone_ids=[face_zone_id],
            ),
            metadata=metadata,
            timeout=10.0,
         )
         adjacent_cell_ids = list(adjacent_cell_resp.adjacent_cell_zones)
         print(f"Adjacent cell zones: {adjacent_cell_ids}")

         # Step 3: Find boundary face zones adjacent to those cell zones.
         if adjacent_cell_ids:
            adjacent_face_resp = stub.GetAdjacentFaceZones(
               meshing_queries_pb2.GetAdjacentFaceZonesRequest(
                  zone_name_or_pattern="*",
                  cell_zone_ids=adjacent_cell_ids,
               ),
               metadata=metadata,
               timeout=10.0,
            )
            print(
               "Adjacent boundary face zones: "
               f"{list(adjacent_face_resp.adjacent_boundary_face_zones)}"
            )

         # Step 4: List all objects and inspect one object's region names.
         objects_resp = stub.GetAllObjectNameList(
            meshing_queries_pb2.Empty(),
            metadata=metadata,
            timeout=10.0,
         )
         objects = list(objects_resp.objects)
         print(f"Objects ({len(objects)}): {objects[:10]}")

         if objects:
            obj = objects[0]
            regions_resp = stub.GetRegionNameListOfObject(
               meshing_queries_pb2.GetRegionNameListObjectRequest(object=obj),
               metadata=metadata,
               timeout=10.0,
            )
            print(f"Regions in '{obj}': {list(regions_resp.regions)[:10]}")

         # Step 5: Check for overlapping face zones.
         overlap_resp = stub.GetOverlappingFaceZones(
            meshing_queries_pb2.GetOverlappingFaceZonesRequest(
               face_zone_name_or_pattern="*",
               area_tolerance=1.0e-8,
               distance_tolerance=1.0e-5,
            ),
            metadata=metadata,
            timeout=30.0,
         )
         print(
            "Overlapping face zones found: "
            f"{len(overlap_resp.overlapping_face_zone_ids)}"
         )

         # Step 6: Retrieve numeric cell quality values for all cells.
         quality_resp = stub.GetAllCellsQuality(
            meshing_queries_pb2.GetAllCellsQualityRequest(as_string=False),
            metadata=metadata,
            timeout=60.0,
         )
         values = list(quality_resp.cell_values)
         if values:
            print(f"Cell quality count: {len(values)}")
            print(f"Cell quality min/max: {min(values):.6g}/{max(values):.6g}")
         else:
            print("No cell quality values returned")

      except grpc.RpcError as err:
         print(f"Meshing query error: {err.code()} - {err.details()}")
         raise
      finally:
         channel.close()


   if __name__ == "__main__":
      query_mesh_workflow()

Frequently Used Request Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Query style
     - Common request fields
     - Notes
   * - Pattern-based zone query
     - ``filter``, ``zone_name_or_pattern``, ``face_zone_pattern``, ``cell_zone_pattern``
     - Supports ``*`` wildcards to target groups of zones.
   * - ID-driven topology query
     - ``face_zone_ids``, ``cell_zone_ids``, ``zone_ids``
     - Prefer IDs when entities are already resolved.
   * - Object / region query
     - ``object``, ``object_name``, ``region_name``, ``region_name_or_pattern``
     - Use object-scoped calls for deterministic scoping.
   * - Multi-object or multi-region query
     - ``object_lists: repeated string``, ``regions: repeated string``, ``labels: repeated string``
     - Pass all names in a single call rather than looping.
   * - Shared-region type query
     - ``mesh_object``, ``region_type``
     - Use ``GetFaceZonesSharedByRegionsOfType`` to scope by region topology class.
   * - Tolerance-based geometry query
     - ``area_tolerance``, ``distance_tolerance``, ``join_tolerance``, ``join_angle``, ``absolute_tolerance``
     - Tune to mesh scale and units; start conservative.
   * - Sizing / count filter
     - ``maximum_entity_count``, ``minimum_zone_area``, ``maximum_zone_area``, ``only_boundary``
     - Useful for quickly isolating large or small zones.

Best Practices
~~~~~~~~~~~~~~

1. **Start with discovery RPCs** — Resolve object and zone identifiers first, then run adjacency or diagnostics queries.
2. **Prefer IDs after lookup** — ID-based calls are more deterministic than text patterns for downstream queries.
3. **Use ``GetFaceZonesSharedByRegionsOfType`` for region-type scoping** — More targeted than broad object queries when region topology class is known.
4. **Use conservative tolerances initially** — Expand ``area_tolerance`` and ``distance_tolerance`` only when overlap or join results are unexpectedly empty.
5. **Set longer timeouts for heavy queries** — ``GetAllCellsQuality``, ``GetAllCellsIds``, and ``FindJoinPairs`` can take significantly longer on large meshes.
6. **Handle empty results as valid outcomes** — Many diagnostics calls can legitimately return no matches.
7. **Restrict scope where possible** — Use object or region constraints in calls such as ``GetRegionsOfFilter`` to avoid large responses.

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`field_data` - Field data service
- :doc:`health` - Health service for connectivity checks
