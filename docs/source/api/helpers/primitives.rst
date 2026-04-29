Primitives
==========

The Primitives module defines shared data structures used by multiple Fluent service protos.

Overview
~~~~~~~~

.. include:: ../../shared_example_assumptions.rst

The ``Primitives`` module defines common data types including:

- Point: 3D Cartesian coordinates
- Vector: 3D vector data
- Other shared structures

This is a helper module (not a standalone service) and is primarily referenced by
other service proto definitions.

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.primitives``

Used by proto files
~~~~~~~~~~~~~~~~~~~

The ``primitives.proto`` helper types are used by:

- ``reduction.proto`` (for vector-like point values such as centroid, force, and moment)

Common message types
~~~~~~~~~~~~~~~~~~~~

Point
-----

Represents a 3D Cartesian coordinate.

.. code-block:: python

   point = primitives_pb2.Point(x=0.0, y=0.0, z=0.0)

See also
~~~~~~~~

- :doc:`../../getting_started/gettingstarted` - Basic client setup
- :doc:`../services/reduction` - Reduction service
