Variant types
=============

The Variant helper module provides polymorphic value containers used across Fluent service protos.

Overview
~~~~~~~~

.. include:: ../../shared_example_assumptions.rst

The ``Variant`` helper types allow you to:

- Handle polymorphic data
- Convert between types
- Manage variant values

``variant.proto`` is not a standalone gRPC service. It is a shared type module
used by other service protos.

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.variant``

**Main Classes:**

- ``Variant``: Message type for polymorphic values

Used by proto files
~~~~~~~~~~~~~~~~~~~

The ``variant.proto`` helper types are used by:

- ``datamodel_se.proto`` (state, args, attrs, and command/query payloads)
- ``reduction.proto`` (typed reduction results)

Variant types
~~~~~~~~~~~~~

The Variant message supports:

- Numeric types (int, float, double)
- String values
- Boolean values
- Lists and nested variants
- Custom objects

Example usage
~~~~~~~~~~~~~

.. code-block:: python
   :caption: Python

   # Creating numeric variant
   int_var = variant_pb2.Variant(int_value=42)
   
   # Creating string variant
   str_var = variant_pb2.Variant(string_value="hello")
   
   # Creating list variant
   list_var = variant_pb2.Variant(
       list_value=variant_pb2.VariantList(
           items=[int_var, str_var]
       )
   )

See also
~~~~~~~~

- :doc:`../../getting_started/gettingstarted` - Basic client setup
- :doc:`../services/datamodel_se` - Data model (state engine) service
- :doc:`../services/reduction` - Reduction service
