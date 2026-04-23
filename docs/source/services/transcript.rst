Transcript
==========

The Transcript service provides access to Fluent's command transcript and logging.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``Transcript`` service allows you to:

- Retrieve command history
- Access solver output/logs
- Monitor transcript stream
- Query execution results

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.transcript``

**Main Classes:**

- ``TranscriptStub``: Client stub for transcript operations

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Get transcript (stream)
-----------------------

Stream transcript messages and solver output.

.. code-block:: python

   request = transcript_pb2.GetTranscriptRequest()
   
   for transcript_msg in stub.GetTranscript(
       request,
       metadata=metadata,
   ):
       if transcript_msg.type == transcript_pb2.TranscriptMessage.STDOUT:
           print(f"Output: {transcript_msg.message}")
       elif transcript_msg.type == transcript_pb2.TranscriptMessage.STDERR:
           print(f"Error: {transcript_msg.message}")

Complete example
~~~~~~~~~~~~~~~~

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import transcript_pb2, transcript_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def stream_transcript():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = transcript_pb2_grpc.TranscriptStub(channel)
       
       try:
           request = transcript_pb2.GetTranscriptRequest()
           
           line_count = 0
           for transcript_msg in stub.GetTranscript(
               request,
               metadata=metadata,
           ):
               message = transcript_msg.message
               if message:
                   print(message, end='')
                   line_count += 1
           
           print(f"\nReceived {line_count} transcript lines")
           
       except grpc.RpcError as err:
           print(f"Error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       stream_transcript()

Message types
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Type
     - Description
   * - STDOUT
     - Standard output/solver messages
   * - STDERR
     - Standard error/warning messages
   * - INFO
     - Informational messages

See also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`monitor` - Monitor service
