Scheme pointer types
====================

The Scheme Pointer definitions provide the typed value container used to
exchange Scheme data with Fluent.

Overview
~~~~~~~~

.. include:: ../../shared_example_assumptions.rst

``SchemePointer`` is a protobuf message, not a standalone gRPC service. It is
used primarily by the Scheme evaluation API to represent Scheme values such as:

- Empty values
- Symbols and strings
- Integers and floating-point numbers
- Booleans and characters
- Pairs and lists

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.scheme_pointer``

**Main Types:**

- ``SchemePointer``: Typed container for a single Scheme value
- ``SchemePointer.SchemePair``: Pair structure with ``car`` and ``cdr``
- ``SchemePointer.SchemeList``: Repeated ``SchemePointer`` items
- ``Empty``: Represents a null or empty Scheme value

Used by proto files
~~~~~~~~~~~~~~~~~~~

The ``scheme_pointer.proto`` helper types are used by:

- ``scheme_eval.proto`` (typed Scheme request/response payloads)
- ``events.proto`` (event callback argument payloads)

Common value shapes
~~~~~~~~~~~~~~~~~~~

``SchemePointer`` uses the ``val`` oneof to hold exactly one active value.

- ``empty``: Empty or null-like value
- ``sym``: Scheme symbol
- ``str``: Scheme string
- ``fixednum``: Integer value
- ``flonum``: Floating-point value
- ``b``: Boolean value
- ``c``: Character value
- ``pair``: Two-part cons cell
- ``list``: Ordered list of Scheme values

Example: create simple scalar values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import scheme_pointer_pb2

   symbol_ptr = scheme_pointer_pb2.SchemePointer(sym="rp-var-define")
   integer_ptr = scheme_pointer_pb2.SchemePointer(fixednum=42)
   float_ptr = scheme_pointer_pb2.SchemePointer(flonum=3.14)
   string_ptr = scheme_pointer_pb2.SchemePointer(str="hello")
   bool_ptr = scheme_pointer_pb2.SchemePointer(b=True)

Example: build a scheme list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example builds the Scheme expression ``(+ 1 2)`` as a typed list.

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import scheme_pointer_pb2

   expression = scheme_pointer_pb2.SchemePointer(
       list=scheme_pointer_pb2.SchemePointer.SchemeList(
           items=[
               scheme_pointer_pb2.SchemePointer(sym="+"),
               scheme_pointer_pb2.SchemePointer(fixednum=1),
               scheme_pointer_pb2.SchemePointer(fixednum=2),
           ]
       )
   )

Example: inspect a returned SchemePointer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``WhichOneof("val")`` to determine which field is populated.

.. code-block:: python
   :caption: Python

   def scheme_pointer_to_python(ptr):
       kind = ptr.WhichOneof("val")
       if kind == "empty":
           return None
       if kind == "sym":
           return ptr.sym
       if kind == "str":
           return ptr.str
       if kind == "fixednum":
           return ptr.fixednum
       if kind == "flonum":
           return ptr.flonum
       if kind == "b":
           return ptr.b
       if kind == "c":
           return ptr.c
       if kind == "list":
           return [scheme_pointer_to_python(item) for item in ptr.list.items]
       if kind == "pair":
           return (
               scheme_pointer_to_python(ptr.pair.car),
               scheme_pointer_to_python(ptr.pair.cdr),
           )
       return None

Usage with scheme evaluation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``SchemePointer`` values are commonly passed to and returned from the Scheme
evaluation API.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import (
       scheme_eval_pb2,
       scheme_eval_pb2_grpc,
       scheme_pointer_pb2,
   )

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   # Service name is SchemeInterpreter; the generated stub is SchemeInterpreterStub.
   stub = scheme_eval_pb2_grpc.SchemeInterpreterStub(channel)

   expression = scheme_pointer_pb2.SchemePointer(
       list=scheme_pointer_pb2.SchemePointer.SchemeList(
           items=[
               scheme_pointer_pb2.SchemePointer(sym="+"),
               scheme_pointer_pb2.SchemePointer(fixednum=10),
               scheme_pointer_pb2.SchemePointer(fixednum=32),
           ]
       )
   )

   response = stub.SchemeEval(
       scheme_eval_pb2.SchemeEvalRequest(input=expression),
       metadata=metadata,
   )

   print(response.output.fixednum)

Best practices
~~~~~~~~~~~~~~

1. **Check the active oneof field** before reading a value.
2. **Use typed lists for structured expressions** when interacting with ``SchemeEval``.
3. **Prefer strings for simple expressions** and typed pointers when preserving structure matters.
4. **Treat ``pair`` and ``list`` separately** because they represent different Scheme constructs.

See also
~~~~~~~~

- :doc:`../../getting_started/gettingstarted` - Basic client setup
- :doc:`../legacy/scheme_eval` - Scheme evaluation service
- :doc:`../services/events` - Events service
