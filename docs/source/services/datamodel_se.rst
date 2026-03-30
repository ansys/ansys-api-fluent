Data Model (Solver Engine)
============================

The Data Model Solver Engine service provides access to Fluent's data model in solver engine mode.

Overview
~~~~~~~~

The ``DataModel`` service (SE) provides:

- Access to solver engine data model
- Data model queries and modifications
- Object lifecycle management
- Solver-specific operations

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.datamodel_se``

**Main Classes:**

- ``DataModelStub``: Client stub for data model operations

Core RPC Operations
~~~~~~~~~~~~~~~~~~~

getAttributeValue
------------------

Retrieve attribute values from the data model.

.. code-block:: python

   request = datamodel_pb2.GetAttributeValueRequest(
       path="/path/to/attribute"
   )
   
   response = stub.getAttributeValue(
       request,
       metadata=metadata,
       timeout=10.0
   )

setAttributeValue
------------------

Set attribute values in the data model.

.. code-block:: python

   request = datamodel_pb2.SetAttributeValueRequest(
       path="/path/to/attribute",
       value=variant_pb2.Variant()  # Set appropriate value
   )
   
   response = stub.setState(
       request,
       metadata=metadata,
       timeout=10.0
   )

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`datamodel_tui` - Data Model TUI service
