Settings service — Python examples
====================================

This page shows how to build a Python client for the ``Settings`` gRPC
service — from connecting to the server and exploring the schema, through
reading and writing solver configuration, to a complete end-to-end example.

For the full message and field reference see
:doc:`../../api/services/settings`.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = settings_pb2_grpc.SettingsStub(channel)

Every RPC addresses a settings node with a ``PathInfo`` message carrying a
**root** string and a slash-separated **path**; for the Fluent solver, pass
``"fluent"`` as the root.

It is generally best to walk the schema first so you can confirm valid paths,
commands, and object names before making runtime calls. However, the Settings
service also allows direct runtime queries/commands when you already know the
exact path to target.

Discovering the schema
-----------------------

Call ``GetSchema`` once at startup and cache the result. It returns the
complete tree of paths, object types, commands, and queries available for a
given root. The schema is stable for a given Fluent version and does not
reflect runtime state.

.. code-block:: python
   :caption: Python

   schema_resp = stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent"),
       metadata=metadata,
   )

   def walk(node, indent=0):
       prefix = "  " * indent
       for child in node.children:
           print(f"{prefix}{child.name}/")
           walk(child.value, indent + 1)
       for cmd in node.commands:
           print(f"{prefix}{cmd.name}()")
       for qry in node.queries:
           print(f"{prefix}{qry.name}?")

   walk(schema_resp.info)

.. raw:: html

   <details>
   <summary style="cursor:pointer;user-select:none;font-weight:bold;padding:4px 0">
    Schema output (click to expand)
   </summary>
   <pre style="background:#2b2b2b;color:#f8f8f2;border:1px solid #444;border-radius:4px;padding:12px;margin-top:6px;overflow:auto;font-size:0.85em;line-height:1.5">
    file/
    single-precision-coordinates?/
    binary-legacy-files?/
    cff-files?/
    auto-merge-zones?/
    convert-hanging-nodes-during-read?/
    ... (9 more children)
    define-macro()
    execute-macro()
    read-macros()
    read()
    read-case()
    ... (26 more commands)
    get-cleanup-filename?
    mesh/
    adapt/
        refinement-criteria/
        coarsening-criteria/
        manual-refinement-criteria/
        manual-coarsening-criteria/
        set/
        adaption-method/
        prismatic-boundary-zones/
        cell-zones/
        dynamic-adaption-frequency/
        verbosity/
        ... (9 more children)
        dynamic-adaption?()
        ... (6 more children)
        adapt-mesh()
        display-adaption-cells()
        list-adaption-cells()
    geometry/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
    anisotropic-adaption/
        operations/
        coarsen?/
        refine?/
        swap?/
        move?/
        iterations/
        fixed-zones/
        indicator/
        indicator-type/
        single-scalar-fn/
        multi-scalar-fn/
        target/
        target-type/
        number-of-cells/
        factor-of-cells/
        ... (3 more children)
        adapt-mesh()
    check-before-solve?/
    check-verbosity/
    ... (9 more children)
    adjacency()
    check()
    memory-usage()
    mesh-info()
    quality()
    ... (8 more commands)
    server/
    web-server/
        start()
        stop()
        print-server-info()
        get-server-info?
    grpc/
        start()
        stop()
        print-address()
        print-connected-clients()
        write-or-reset-info()
    setup/
    general/
        solver/
        type/
        two-dim-space/
        velocity-formulation/
        time/
        adjust-solver-defaults-based-on-setup/
        operating-conditions/
        gravity/
            enable?/
            components/
            gravity-mrf-behavior/
        real-gas-state/
        floating-operating-pressure?/
        operating-pressure/
        reference-pressure-location/
        ... (4 more children)
        used-ref-pressure-location()
        units-settings/
        units/
            create()
            delete()
            rename()
            list()
            list-properties()
            ... (1 more commands)
        new-unit()
        set-unit-system()
    models/
        multiphase/
        model/
        hybrid-models/
            coupled-level-set/
            level-set/
            weighting/
            multi-fluid-vof/
        number-of-phases/
            number-of-eulerian-phases/
        number-of-eulerian-discrete-phases/
        model-options/
            open-channel-flow/
            open-channel-flow-wave-bc/
            slip-velocity-on/
            flow-regime-modeling/
            flow-regime-parameters/
            critical-vf/
            delta-vf/
            ncells-fs/
            delta-grad/
            ... (4 more children)
        ... (10 more children)
        energy/
        enabled/
        viscous-dissipation/
        pressure-work/
        kinetic-energy/
        inlet-diffusion/
        ... (1 more children)
        viscous/
        model/
        spalart-allmaras-production/
        reynolds-stress/
        rans/
        reynolds-stress-options/
            solve-tke/
            wall-echo/
            coefficients/
            c1-ps/
            c2-ps/
            c1prime-ps/
            c2prime-ps/
            c1-ssg-ps/
            ... (6 more children)
        ... (22 more children)
        acoustics/
        model/
        export-source-data/
            export-asd/
            export-cgns/
            write-frequency/
            timesteps-per-asd-file/
            sources-fft/
            export-cgns-volumetric()
        fwh-options/
            on-the-fly/
            far-field-density/
            far-field-sound-speed/
            reference-acoustic-pressure/
            timesteps-per-revolution/
            ... (4 more children)
        sources()
        radiation/
        model/
        discrete-ordinates/
            angular-discretization/
            n-theta-divisions/
            n-phi-divisions/
            n-theta-pixels/
            n-phi-pixels/
            do-acceleration?/
            partially-specular-wall-treatment-method/
            fast-second-order-discrete-ordinate?/
            blending-factor/
            ... (1 more children)
        monte-carlo/
            under-relaxation/
            mesh-options/
            target-cells-per-volume-cluster/
        s2s/
            clustering-settings/
            enable-mesh-interface-clustering/
            split-angle/
            clustering-algorithm/
            enable-clustering/
            faces-per-cluster/
                option/
                global-faces-per-surface-cluster/
                maximum-faces-per-surface-cluster/
            print-thread-clusters()
            viewfactor-settings/
            basis/
            method/
            surfaces/
            smoothing/
            parameters/
                resolution/
                subdivide/
                separation/
            ... (3 more children)
            ambient-radiation-modeling/
            enable-ambient-radiation/
            ambient-temperature/
            compute-write-vf()
            compute-vf-accelerated()
            compute-vf-only()
            read-vf-file()
        multiband/
            create()
            delete()
            rename()
            list()
            list-properties()
            ... (1 more commands)
        ... (4 more children)
        ... (12 more children)
    materials/
        database/
        database-type/
        user-db-name/
        list-by-type/
        copy-materials()
        list-materials()
        list-properties()
        copy-by-name()
        copy-by-formula()
        get-database-material-names?
        get-database-material-properties?
        fluid/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        solid/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        mixture/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        inert-particle/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        ... (3 more children)
        list-materials()
        list-properties()
    cell-zone-conditions/
        fluid/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        solid/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        composite-solid/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        copy()
        set-zone-type()
        activate-cell-zone()
        mrf-to-sliding-mesh()
        convert-all-solid-mrf-to-solid-motion()
        ... (4 more commands)
    model-topology/
        parts/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        groups/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        list-topology()
        reset-utl()
    ... (10 more children)
    solution/
    methods/
        axisymmetric/
        alternative-axisymmetric-formulation?/
        axis-stabilization?/
        p-v-coupling/
        flow-scheme/
        skewness-correction-itr-count/
        neighbor-correction-itr-count/
        skewness-neighbor-coupling/
        coupled-form/
        ... (3 more children)
        spatial-discretization/
        gradient-scheme/
        discretization-scheme/
            create()
            delete()
            rename()
            list()
            list-properties()
            ... (1 more commands)
        spatial-discretization-parameters/
        low-diffusion-central/
            diffusion-coefficient/
            shield-bl-distance/
        bcd-boundedness/
        pseudo-time-method/
        formulation/
            coupled-solver/
            segregated-solver/
            density-based-solver/
        relaxation-method/
        convergence-acceleration-for-stretched-meshes/
            convergence-acceleration-type/
            casm-cutoff-multiplier/
        relaxation-bounds()
        ... (28 more children)
        set-solution-methods-to-default()
        set-optimized-les-numerics()
    controls/
        courant-number/
        p-v-controls/
        skewness-correction-itr-count/
        neighbor-correction-itr-count/
        skewness-neighbor-coupling/
        vof-correction-itr-count/
        flow-courant-number/
        ... (4 more children)
        residual-smoothing/
        residual-smoothing-factor/
        residual-smoothing-iter-count/
        gradient-options/
        pressure-reconstruction-generic?/
        least-squares/
            weighting-factor/
        green-gauss-node-based/
            alternative-default-settings?/
            boundary-treatment-location/
            least-squares-node-weights?/
            alternative-weights-at-boundary?/
            weight-treatment-at-sliding-boundary?/
            ... (1 more children)
        disable-reconstruction?/
        ... (14 more children)
        reset-solution-controls()
        reset-amg-controls()
        reset-multi-stage-parameters()
        reset-limits()
        reset-pseudo-time-method-generic()
        ... (3 more commands)
    report-definitions/
        mesh/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        surface/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        volume/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        force/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        lift/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
        ... (12 more children)
        delete()
        compute()
        copy()
        delete-all()
    monitor/
        residual/
        equations/
            create()
            delete()
            rename()
            list()
            list-properties()
            ... (1 more commands)
        options/
            criterion-type/
            n-save/
            normalize?/
            n-maximize-norms/
            enhanced-continuity-residual?/
            ... (4 more children)
        axes/
            x/
            label/
            log-scale?/
            number-format/
                format-type/
                precision/
            auto-range/
                min-auto?/
                min/
                max-auto?/
                max/
            show-major-gridlines?/
            ... (3 more children)
            y/
            label/
            log-scale?/
            number-format/
                format-type/
                precision/
            auto-range/
                min-auto?/
                min/
                max-auto?/
                max/
            show-major-gridlines?/
            ... (3 more children)
        curves/
            create()
            delete()
            rename()
            list()
            list-properties()
            ... (1 more commands)
        reset()
        renormalize()
        plot()
        write()
        report-files/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (3 more commands)
        report-plots/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (2 more commands)
        convergence-conditions/
        convergence-reports/
            create()
            delete()
            rename()
            list()
            list-properties()
            ... (1 more commands)
        frequency/
        condition/
        check-for/
    cell-registers/
        create()
        delete()
        rename()
        list()
        list-properties()
        ... (1 more commands)
    ... (3 more children)
    ... (7 more children)
    list()
    list-properties()
    exit()
    switch-to-meshing-mode()
    get-modified-state?
   </pre>
   </details>

The tree structure directly mirrors the slash-separated paths used in every
other RPC call.

Runtime API overview
---------------------

Once you know the schema, the runtime RPCs follow a small, consistent set of
patterns.

**Read and write state** with ``GetState`` and ``SetState``. Values are
carried in ``Value`` messages, which use a ``oneof`` to hold one active type.
Call ``WhichOneof("value")`` on a returned ``Value`` to identify the active
field before accessing it.

.. code-block:: python
   :caption: Python

   resp = stub.GetState(
       settings_pb2.GetStateRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/general/solver-type"),
       ),
       metadata=metadata,
   )
   kind = resp.value.WhichOneof("value")
   print(f"solver-type is {kind} = {getattr(resp.value, kind)}")

   stub.SetState(
       settings_pb2.SetStateRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/general/solver-type"),
           value=settings_pb2.Value(string="pressure-based"),
       ),
       metadata=metadata,
   )

**Manage named objects** (boundary conditions, graphics objects, etc.) with
``CreateObject``, ``Rename``, ``DeleteObject``, and ``GetObjectNames``.
The Settings service also provides ``GetListSize`` and ``ResizeListObject``
for fixed-size list settings.

.. code-block:: python
   :caption: Python

   stub.CreateObject(
       settings_pb2.CreateObjectRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/boundary-conditions/wall"),
           name="wall-1",
       ),
       metadata=metadata,
   )
   names = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/boundary-conditions/wall"),
       ),
       metadata=metadata,
   ).names
   print(list(names))

**Execute commands and queries** with ``ExecuteCommand`` and ``ExecuteQuery``.
Pass arguments as a ``Value`` message. ``ExecuteCommand`` performs a
state-mutating action; ``ExecuteQuery`` returns a computed result without side
effects.

.. code-block:: python
   :caption: Python

   stub.ExecuteCommand(
       settings_pb2.ExecuteCommandRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="solution/run-calculation"),
           command="iterate",
           args=settings_pb2.Value(integer=10),
       ),
       metadata=metadata,
   )

**Retrieve metadata** with ``GetAttrs`` to read type, active status, or
read-only flag at any path without a prior ``GetSchema`` call. Use
``IsWildcard`` to check whether a string will be treated as a wildcard by the
solver before passing it to other RPCs.

End-to-end example
-------------------

The example below walks through a complete solver configuration session:
connect, discover the schema, set a solver parameter, create a boundary
condition, run a calculation, and close.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = settings_pb2_grpc.SettingsStub(channel)

   # Discover what is available at the top level.
   schema_resp = stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent"),
       metadata=metadata,
   )
   print("Top-level children:", [c.name for c in schema_resp.info.children])

   # Set the solver type.
   stub.SetState(
       settings_pb2.SetStateRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/general/solver-type"),
           value=settings_pb2.Value(string="pressure-based"),
       ),
       metadata=metadata,
   )

   # Create a new wall boundary condition.
   stub.CreateObject(
       settings_pb2.CreateObjectRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent", path="setup/boundary-conditions/wall"
           ),
           name="heated-wall",
       ),
       metadata=metadata,
   )

   # Configure an operating pressure for the case.
   stub.SetState(
       settings_pb2.SetStateRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           ),
           value=settings_pb2.Value(real=101325.0),
       ),
       metadata=metadata,
   )

   # Confirm the value was written.
   resp = stub.GetState(
       settings_pb2.GetStateRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           ),
       ),
       metadata=metadata,
   )
   print("Operating pressure:", resp.value.real)

   # Run 50 iterations.
   stub.ExecuteCommand(
       settings_pb2.ExecuteCommandRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="solution/run-calculation"),
           command="iterate",
           args=settings_pb2.Value(integer=50),
       ),
       metadata=metadata,
   )

   channel.close()

For the complete message and field reference — request/response types,
the ``Value`` and ``Schema`` message structures, and ``GetAttrs`` — see
:doc:`../../api/services/settings`.
