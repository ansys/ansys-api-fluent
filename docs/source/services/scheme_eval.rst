Scheme Evaluation Service
=========================

The Scheme Evaluation service provides access to Scheme scripting and evaluation capabilities.

Overview
~~~~~~~~

The ``SchemeEval`` service allows you to:

- Execute Scheme commands
- Evaluate Scheme expressions
- Access Fluent's scripting interface

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.scheme_eval``

**Main Classes:**

- ``SchemeEvalStub``: Client stub for Scheme evaluation

Core RPC Operations
~~~~~~~~~~~~~~~~~~~

Eval
-----

Evaluate a Scheme expression.

.. code-block:: python

   request = scheme_eval_pb2.EvalRequest(
       expression="(+ 1 2)"  # Scheme expression
   )
   
   response = stub.Eval(
       request,
       metadata=metadata,
       timeout=10.0
   )
   
   result = response.result

See Also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`scheme_pointer` - Scheme pointer service
