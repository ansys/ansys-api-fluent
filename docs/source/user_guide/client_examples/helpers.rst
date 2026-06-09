Helper types
============

The ``ansys.api.fluent.v1`` package includes two shared protobuf message
types that appear as value types in request and response messages across
multiple services.

See :doc:`../../api/helpers/variant` and :doc:`../../api/helpers/primitives`
for the complete reference material.

.. include:: ../../shared_example_assumptions.rst

Variant
-------

``Variant`` is the polymorphic value container used by the
:doc:`DataModel <datamodel_se>` service for all state, argument, and
result payloads, and by the :doc:`Reduction <../../api/services/reduction>` service for
typed results. It holds exactly one value at a time, selected by a ``oneof``
field. Always call ``WhichOneof("as")`` on a ``Variant`` returned by the
server before reading its value.

.. code-block:: python

   from ansys.api.fluent.v1 import variant_pb2

   # Scalar values
   bool_variant   = variant_pb2.Variant(bool_state=True)
   int_variant    = variant_pb2.Variant(int64_state=42)
   double_variant = variant_pb2.Variant(double_state=3.14)
   string_variant = variant_pb2.Variant(string_state="hello")

   # Vector values
   double_vector = variant_pb2.Variant(
       double_vector_state=variant_pb2.DoubleVector(items=[1.0, 2.0, 3.0])
   )
   string_vector = variant_pb2.Variant(
       string_vector_state=variant_pb2.StringVector(items=["a", "b", "c"])
   )

   # Dictionary (VariantMap) — used for command arguments
   mapping = variant_pb2.Variant(
       variant_map_state=variant_pb2.VariantMap(
           item={
               "count": variant_pb2.Variant(int64_state=10),
               "label": variant_pb2.Variant(string_state="wall"),
           }
       )
   )

   # Reading a Variant returned by the server
   def read_variant(v: variant_pb2.Variant):
       field = v.WhichOneof("as")
       return field, getattr(v, field)

Point
-----

``Point`` is a 3D Cartesian coordinate (``x``, ``y``, ``z`` as ``double``)
used by the :doc:`Reduction <../../api/services/reduction>` service in geometric results
such as centroid, force, and moment. See
:doc:`../../api/helpers/primitives` for the full message definition.

.. code-block:: python

   from ansys.api.fluent.v1 import primitives_pb2

   origin = primitives_pb2.Point(x=0.0, y=0.0, z=0.0)
   corner = primitives_pb2.Point(x=1.5, y=2.0, z=-0.5)
