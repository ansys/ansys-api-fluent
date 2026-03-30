Data Model (TUI)
================

The Data Model TUI service provides access to Fluent's data model in TUI (Text User Interface) mode.

Overview
~~~~~~~~

The ``DataModel`` service (TUI) provides:

- Access to TUI-mode data model
- TUI command execution
- Data model queries for TUI mode
- Object management in TUI context

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.datamodel_tui``

**Main Classes:**

- ``DataModelStub``: Client stub for TUI data model operations

Core RPC Operations
~~~~~~~~~~~~~~~~~~~

GetAttributeValue
------------------

Retrieve attribute values from the TUI data model.

.. code-block:: python

   request = datamodel_pb2.GetAttributeValueRequest(
       path="/settings/path"  # TUI path
   )
   
   response = stub.GetAttributeValue(
       request,
       metadata=metadata,
       timeout=10.0
   )

ExecuteCommand
---------------

Execute a TUI command.

.. code-block:: python

   request = datamodel_pb2.ExecuteCommandRequest(
       command="/command/path",
       arguments=["arg1", "arg2"]
   )
   
   response = stub.ExecuteCommand(
       request,
       metadata=metadata,
       timeout=30.0
   )

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`datamodel_se` - Data Model Solver Engine service
