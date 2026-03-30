Common API
==========

The Common API provides shared message types and data structures used across services.

Overview
~~~~~~~~

The ``CommonAPI`` module defines common data types including:

- Point: 3D Cartesian coordinates
- Vector: 3D vector data
- Other shared structures

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.common_api``

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
