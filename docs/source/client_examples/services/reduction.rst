Reduction
=========

The ``Reduction`` service provides scalar and vector reduction operations over
surfaces and cell zones.

Overview
~~~~~~~~

.. include:: ../../shared_example_assumptions.rst

The ``Reduction`` service allows you to:

- Compute geometric reductions (area, volume, centroid)
- Compute weighted averages and integrals over selected locations
- Compute force and moment vectors on surfaces
- Compute extrema and conditional counts/sums from expressions
- Work with dynamically typed scalar results using ``Variant``

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.reduction``

**Main Classes:**

- ``ReductionStub``: Client stub for reduction operations
- Request/response message pairs for each operation
- ``Variant``-based scalar responses (``response.value``)
- ``Point``-based vector responses for geometric/force outputs

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Geometry and basic totals
-------------------------

- ``Area``
- ``Volume``
- ``Centroid``
- ``Count``

Example: area and centroid on selected surfaces

.. code-block:: python
   :caption: Python

   area_resp = reduction_stub.Area(
      reduction_pb2.AreaRequest(locations=["wall-inlet", "wall-outlet"]),
      metadata=metadata,
   )

   centroid_resp = reduction_stub.Centroid(
      reduction_pb2.CentroidRequest(locations=["wall-inlet", "wall-outlet"]),
      metadata=metadata,
   )

   c = centroid_resp.value
   print(f"Centroid: ({c.x}, {c.y}, {c.z})")

Weighted averages and integrals
-------------------------------

- ``AreaAve``
- ``AreaInt``
- ``MassAve``
- ``MassFlowAve``
- ``MassFlowAveAbs``
- ``MassFlowInt``
- ``MassInt``
- ``VolumeAve``
- ``VolumeInt``

Example: volume-weighted average absolute pressure

.. code-block:: python
   :caption: Python

   response = reduction_stub.VolumeAve(
      reduction_pb2.VolumeAveRequest(
         expression="AbsolutePressure",
         locations=["fluid"],
      ),
      metadata=metadata,
   )

Force and moment
----------------

- ``Force``
- ``PressureForce``
- ``ViscousForce``
- ``Moment``

Example: pressure and viscous force decomposition

.. code-block:: python
   :caption: Python

   pressure = reduction_stub.PressureForce(
      reduction_pb2.PressureForceRequest(locations=["car-body"]),
      metadata=metadata,
   )
   viscous = reduction_stub.ViscousForce(
      reduction_pb2.ViscousForceRequest(locations=["car-body"]),
      metadata=metadata,
   )

   fp = pressure.value
   fv = viscous.value
   print(f"Pressure force: ({fp.x}, {fp.y}, {fp.z})")
   print(f"Viscous force: ({fv.x}, {fv.y}, {fv.z})")

Extrema and conditional reductions
----------------------------------

- ``Maximum``
- ``Minimum``
- ``CountIf``
- ``Sum``
- ``SumIf``

Example: conditional count and weighted sum

.. code-block:: python
   :caption: Python

   count_if_resp = reduction_stub.CountIf(
      reduction_pb2.CountIfRequest(
         expression="AbsolutePressure > 0[Pa]",
         locations=["inlet1"],
      ),
      metadata=metadata,
   )

   sum_if_resp = reduction_stub.SumIf(
      reduction_pb2.SumIfRequest(
         expression="AbsolutePressure",
         condition="AbsolutePressure > 0[Pa]",
         locations=["inlet1"],
         weight="Area",
      ),
      metadata=metadata,
   )

Working with variant results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many Reduction responses use ``ansys.api.fluent.v1.variant.Variant`` in
``response.value``. Use ``WhichOneof('as')`` to identify the active value type.

.. code-block:: python
   :caption: Python

   def variant_to_python(v):
      kind = v.WhichOneof("as")
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
         return {
            key: variant_to_python(val)
            for key, val in v.variant_map_state.item.items()
         }
      return None

Complete example
~~~~~~~~~~~~~~~~

An end-to-end reduction workflow that computes geometric, statistical, and
force-related metrics using proto-accurate request/response types.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import reduction_pb2, reduction_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"


   def variant_to_python(v):
      kind = v.WhichOneof("as")
      if kind == "double_state":
         return v.double_state
      if kind == "int64_state":
         return v.int64_state
      if kind == "bool_state":
         return v.bool_state
      if kind == "string_state":
         return v.string_state
      if kind == "double_vector_state":
         return list(v.double_vector_state.items)
      if kind == "int64_vector_state":
         return list(v.int64_vector_state.items)
      if kind == "bool_vector_state":
         return list(v.bool_vector_state.items)
      if kind == "string_vector_state":
         return list(v.string_vector_state.items)
      return None


   def run_reductions():
      channel = grpc.insecure_channel(f"{HOST}:{PORT}")
      metadata = [("password", PASSWORD)]
      stub = reduction_pb2_grpc.ReductionStub(channel)

      try:
         # Step 1: Basic geometry reductions.
         area_resp = stub.Area(
            reduction_pb2.AreaRequest(locations=["wall-inlet", "wall-outlet"]),
            metadata=metadata,
         )
         volume_resp = stub.Volume(
            reduction_pb2.VolumeRequest(locations=["fluid"]),
            metadata=metadata,
         )
         centroid_resp = stub.Centroid(
            reduction_pb2.CentroidRequest(locations=["wall-inlet", "wall-outlet"]),
            metadata=metadata,
         )

         print(f"Area: {variant_to_python(area_resp.value)}")
         print(f"Volume: {variant_to_python(volume_resp.value)}")
         c = centroid_resp.value
         print(f"Centroid: ({c.x:.6g}, {c.y:.6g}, {c.z:.6g})")

         # Step 2: Statistical reductions.
         max_t_resp = stub.Maximum(
            reduction_pb2.MaximumRequest(
               expression="AbsolutePressure",
               locations=["fluid"],
            ),
            metadata=metadata,
         )
         min_t_resp = stub.Minimum(
            reduction_pb2.MinimumRequest(
               expression="AbsolutePressure",
               locations=["fluid"],
            ),
            metadata=metadata,
         )
         vol_ave_resp = stub.VolumeAve(
            reduction_pb2.VolumeAveRequest(
               expression="AbsolutePressure",
               locations=["fluid"],
            ),
            metadata=metadata,
         )

         print(f"Pressure min: {variant_to_python(min_t_resp.value)}")
         print(f"Pressure max: {variant_to_python(max_t_resp.value)}")
         print(f"Pressure volume average: {variant_to_python(vol_ave_resp.value)}")

         # Step 3: Force decomposition on a surface.
         pressure_force_resp = stub.PressureForce(
            reduction_pb2.PressureForceRequest(locations=["car-body"]),
            metadata=metadata,
         )
         viscous_force_resp = stub.ViscousForce(
            reduction_pb2.ViscousForceRequest(locations=["car-body"]),
            metadata=metadata,
         )
         total_force_resp = stub.Force(
            reduction_pb2.ForceRequest(locations=["car-body"]),
            metadata=metadata,
         )

         fp = pressure_force_resp.value
         fv = viscous_force_resp.value
         ft = total_force_resp.value
         print(f"Pressure force: ({fp.x:.6g}, {fp.y:.6g}, {fp.z:.6g})")
         print(f"Viscous force: ({fv.x:.6g}, {fv.y:.6g}, {fv.z:.6g})")
         print(f"Total force: ({ft.x:.6g}, {ft.y:.6g}, {ft.z:.6g})")

         # Step 4: Conditional reductions.
         hot_count_resp = stub.CountIf(
            reduction_pb2.CountIfRequest(
               expression="AbsolutePressure > 0[Pa]",
               locations=["inlet1"],
            ),
            metadata=metadata,
         )
         weighted_sum_resp = stub.SumIf(
            reduction_pb2.SumIfRequest(
               expression="AbsolutePressure",
               condition="AbsolutePressure > 0[Pa]",
               locations=["inlet1"],
               weight="Area",
            ),
            metadata=metadata,
         )

         print(f"Hot cells/faces count: {variant_to_python(hot_count_resp.value)}")
         print(f"Conditional weighted sum: {variant_to_python(weighted_sum_resp.value)}")

      except grpc.RpcError as err:
         print(f"Reduction error: {err.code()} - {err.details()}")
         raise
      finally:
         channel.close()


   if __name__ == "__main__":
      run_reductions()

Reduction request patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Pattern
     - Typical request fields
     - Notes
   * - Location-only geometric query
     - ``locations``
     - Used by ``Area``, ``Volume``, ``Centroid``, ``Force``.
   * - Expression-based reduction
     - ``expression``, ``locations``
     - Used by averages, integrals, extrema, and ``CountIf``.
   * - Weighted sum reduction
     - ``expression``, ``locations``, ``weight``
     - Used by ``Sum``.
   * - Conditional weighted sum
     - ``expression``, ``condition``, ``locations``, ``weight``
     - Used by ``SumIf``.

Best practices
~~~~~~~~~~~~~~

1. **Use explicit locations** - Restrict reductions to relevant surfaces/zones for predictable results.
2. **Validate expression syntax early** - Test expressions with simple queries before large batch runs.
3. **Handle Variant types defensively** - Always inspect ``WhichOneof('as')`` before using values.
4. **Separate pressure and viscous force** - Use ``PressureForce`` and ``ViscousForce`` for diagnostics, ``Force`` for total.
5. **Keep condition expressions clear** - Prefer simple threshold logic for ``CountIf`` and ``SumIf``.

See also
--------

- :doc:`../../getting_started/gettingstarted` — basic client setup
- :doc:`field_data` — raw field data (scalar, vector, mesh)
- :doc:`svar` — per-zone solution variable data

.. ----------------------------------------------------------------------------
.. The block below is generated by docs/_ext/proto_docgen.py from the matching
.. .proto file in ansys/api/fluent/v1. Edit the proto comments to update it.
.. ----------------------------------------------------------------------------

.. include:: ../../api/_generated/reduction.rst