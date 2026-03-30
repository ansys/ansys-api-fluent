Variant Service
===============

The Variant service provides support for variant data types and polymorphic values.

Overview
~~~~~~~~

The ``Variant`` service allows you to:

- Handle polymorphic data
- Convert between types
- Manage variant values

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.variant``

**Main Classes:**

- ``VariantStub``: Client stub for variant operations
- ``Variant``: Message type for polymorphic values

Variant Types
~~~~~~~~~~~~~

The Variant message supports:

- Numeric types (int, float, double)
- String values
- Boolean values
- Lists and nested variants
- Custom objects

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

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

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
