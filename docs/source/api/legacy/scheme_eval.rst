SchemeInterpreter
=================

The ``SchemeInterpreter`` service provides access to Fluent's Scheme execution and
evaluation capabilities.

Overview
~~~~~~~~

.. include:: ../../shared_example_assumptions.rst

The ``SchemeInterpreter`` service allows you to:

- Execute Scheme commands through ``Exec``
- Evaluate Scheme expressions as strings through ``StringEval``
- Evaluate typed Scheme values through ``SchemeEval``
- Exchange typed Scheme values using ``SchemePointer`` messages

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.scheme_eval``

**Main Classes:**

- ``SchemeInterpreterStub``: Client stub for Scheme evaluation
- ``ExecRequest`` / ``ExecResponse``: Execute one or more Scheme commands
- ``StringEvalRequest`` / ``StringEvalResponse``: Evaluate a Scheme expression from a string
- ``SchemeEvalRequest`` / ``SchemeEvalResponse``: Evaluate a typed ``SchemePointer`` expression
- ``SchemePointer``: Typed Scheme value container used by ``SchemeEval`` and deprecated ``Eval``

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Exec
----

Execute one or more Scheme commands and return the console output.

.. code-block:: python
   :caption: Python

   response = stub.Exec(
       scheme_eval_pb2.ExecRequest(
           commands=[
               '(display "Scheme execution started")',
               '(newline)',
           ],
           wait=True,
           silent=True,
       ),
       metadata=metadata,
   )

   print(response.output)

StringEval
----------

Evaluate a Scheme expression provided as a string and return the result as a string.

.. code-block:: python
   :caption: Python

   response = stub.StringEval(
       scheme_eval_pb2.StringEvalRequest(input="(+ 1 2)"),
       metadata=metadata,
   )

   print(f"Result: {response.output}")

SchemeEval
----------

Evaluate a typed Scheme expression represented as a ``SchemePointer``.

.. code-block:: python
   :caption: Python

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

Eval (deprecated)
-----------------

The ``Eval`` RPC accepts and returns a ``SchemePointer`` directly, but it is
deprecated in favor of ``SchemeEval``.

.. code-block:: python
   :caption: Python

   response = stub.Eval(
       scheme_pointer_pb2.SchemePointer(fixednum=5),
       metadata=metadata,
   )

   print(response.fixednum)

Working with SchemePointer results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``SchemeEval`` and deprecated ``Eval`` return a ``SchemePointer`` value. Use
``WhichOneof("val")`` to detect the active Scheme type.

.. code-block:: python
   :caption: Python

   def scheme_pointer_to_python(ptr):
       kind = ptr.WhichOneof("val")
       if kind == "fixednum":
           return ptr.fixednum
       if kind == "flonum":
           return ptr.flonum
       if kind == "str":
           return ptr.str
       if kind == "sym":
           return ptr.sym
       if kind == "b":
           return ptr.b
       if kind == "c":
           return ptr.c
       if kind == "empty":
           return None
       if kind == "list":
           return [scheme_pointer_to_python(item) for item in ptr.list.items]
       if kind == "pair":
           return (
               scheme_pointer_to_python(ptr.pair.car),
               scheme_pointer_to_python(ptr.pair.cdr),
           )
       return None

Complete example
~~~~~~~~~~~~~~~~

An end-to-end workflow that executes Scheme commands, evaluates a string
expression, and evaluates a typed ``SchemePointer`` expression.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import scheme_eval_pb2, scheme_eval_pb2_grpc, scheme_pointer_pb2

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"


   def scheme_pointer_to_python(ptr):
       kind = ptr.WhichOneof("val")
       if kind == "fixednum":
           return ptr.fixednum
       if kind == "flonum":
           return ptr.flonum
       if kind == "str":
           return ptr.str
       if kind == "sym":
           return ptr.sym
       if kind == "b":
           return ptr.b
       if kind == "c":
           return ptr.c
       if kind == "empty":
           return None
       if kind == "list":
           return [scheme_pointer_to_python(item) for item in ptr.list.items]
       if kind == "pair":
           return (
               scheme_pointer_to_python(ptr.pair.car),
               scheme_pointer_to_python(ptr.pair.cdr),
           )
       return None


   def run_scheme_examples():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = scheme_eval_pb2_grpc.SchemeInterpreterStub(channel)

       try:
           # Step 1: Execute a few Scheme commands.
           exec_response = stub.Exec(
               scheme_eval_pb2.ExecRequest(
                   commands=[
                       '(define answer 42)',
                       '(display "Defined answer")',
                       '(newline)',
                   ],
                   wait=True,
                   silent=True,
               ),
               metadata=metadata,
           )
           print("=== Exec Output ===")
           print(exec_response.output)

           # Step 2: Evaluate a Scheme expression from a string.
           string_eval_response = stub.StringEval(
               scheme_eval_pb2.StringEvalRequest(input="(+ answer 8)"),
               metadata=metadata,
           )
           print("=== StringEval Result ===")
           print(string_eval_response.output)

           # Step 3: Evaluate the same kind of expression using a typed SchemePointer.
           typed_expression = scheme_pointer_pb2.SchemePointer(
               list=scheme_pointer_pb2.SchemePointer.SchemeList(
                   items=[
                       scheme_pointer_pb2.SchemePointer(sym="+"),
                       scheme_pointer_pb2.SchemePointer(fixednum=10),
                       scheme_pointer_pb2.SchemePointer(fixednum=32),
                   ]
               )
           )

           typed_response = stub.SchemeEval(
               scheme_eval_pb2.SchemeEvalRequest(input=typed_expression),
               metadata=metadata,
           )
           print("=== SchemeEval Result ===")
           print(scheme_pointer_to_python(typed_response.output))

       except grpc.RpcError as err:
           print(f"Error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()


   if __name__ == "__main__":
       run_scheme_examples()

Best practices
~~~~~~~~~~~~~~

1. **Prefer ``StringEval`` for simple expressions** - It is easier to author and inspect than a typed ``SchemePointer`` tree.
2. **Use ``SchemeEval`` when type fidelity matters** - It preserves numeric, boolean, list, pair, and symbol structure.
3. **Treat ``Eval`` as legacy** - Prefer ``SchemeEval`` for new client code.
4. **Set ``wait=True`` for synchronous command execution** - This makes ``Exec`` easier to use in request-response workflows.
5. **Decode ``SchemePointer`` defensively** - Always check ``WhichOneof("val")`` before reading a field.

See also
~~~~~~~~

- :doc:`../../getting_started/gettingstarted` - Basic client setup
- :doc:`../helpers/scheme_pointer` - Scheme pointer helper types
