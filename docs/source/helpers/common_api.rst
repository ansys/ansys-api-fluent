Common API
==========

The Common API defines shared data structures used by multiple Fluent service protos.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``CommonAPI`` module defines common data types including:

- Point: 3D Cartesian coordinates
- Vector: 3D vector data
- Other shared structures

This is a helper module (not a standalone service) and is primarily referenced by
other service proto definitions.

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.common_api``

Used By Proto Files
~~~~~~~~~~~~~~~~~~~

The ``common_api.proto`` helper types are used by:

- ``meshing_queries.proto`` (for point-based query locations)
- ``reduction.proto`` (for vector-like point values such as centroid, force, and moment)

Common Message Types
~~~~~~~~~~~~~~~~~~~~

Point
-----

Represents a 3D Cartesian coordinate.

.. code-block:: python

   point = common_api_pb2.Point(x=0.0, y=0.0, z=0.0)

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`../services/meshing_queries` - Meshing queries service
- :doc:`../services/reduction` - Reduction service
