"""Sphinx extension that generates API reference fragments from .proto files.

For each ``.proto`` file under ``ansys/api/fluent/v1`` this extension produces
an RST fragment under ``docs/source/api/_generated/<basename>.rst`` containing:

* a metadata field list (source file, proto package, content counts),
* each RPC defined by services in that file, rendered as a definition list
  with request/response types and a description paragraph,
* every message with its fields as a definition list (name, type, field
  number, description),
* every enum with its values as a definition list.

All output uses plain RST definition lists and field lists — no tables and no
custom CSS. Comments are extracted from the proto ``SourceCodeInfo`` produced
by ``grpc_tools.protoc``. The static wrapper pages in ``api/services``,
``api/helpers`` and ``api/legacy`` include these fragments via
``.. include::`` directives.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from google.protobuf import descriptor_pb2

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
_PROTO_ROOT = _REPO_ROOT / "ansys" / "api" / "fluent" / "v1"
_OUT_DIR = _REPO_ROOT / "docs" / "source" / "api" / "_generated"

# ---------------------------------------------------------------------------
# FileDescriptorSet construction
# ---------------------------------------------------------------------------


def _compile_descriptor_set(proto_files: Iterable[Path]) -> descriptor_pb2.FileDescriptorSet:
    """Run ``protoc`` to compile *proto_files* into a ``FileDescriptorSet``.

    ``--include_source_info`` is required so that field/RPC comments survive
    into the descriptor.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "descriptors.pb"
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={_REPO_ROOT.as_posix()}",
            f"--descriptor_set_out={out_path}",
            "--include_source_info",
            "--include_imports",
        ]
        cmd.extend(p.relative_to(_REPO_ROOT).as_posix() for p in proto_files)
        subprocess.run(cmd, check=True, cwd=_REPO_ROOT)
        fds = descriptor_pb2.FileDescriptorSet()
        fds.ParseFromString(out_path.read_bytes())
        return fds


# ---------------------------------------------------------------------------
# Comment extraction
# ---------------------------------------------------------------------------


def _build_comment_index(file_proto: descriptor_pb2.FileDescriptorProto) -> dict[tuple[int, ...], str]:
    """Index leading + trailing comments by ``SourceCodeInfo.Location.path``."""
    index: dict[tuple[int, ...], str] = {}
    for loc in file_proto.source_code_info.location:
        text = (loc.leading_comments or "") + (loc.trailing_comments or "")
        text = text.strip()
        if text:
            index[tuple(loc.path)] = text
    return index


def _clean_comment(text: str) -> str:
    """Normalize comment text into a single-paragraph RST-safe string."""
    if not text:
        return ""
    lines = [ln.strip().lstrip("*").strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    result = " ".join(lines)
    # Re-encode to UTF-8 replacing any characters that cannot be represented
    # (e.g. lone surrogates from protoc SourceCodeInfo) so write_text never
    # raises UnicodeEncodeError.
    return result.encode("utf-8", errors="replace").decode("utf-8")


# ---------------------------------------------------------------------------
# Type rendering
# ---------------------------------------------------------------------------


_FIELD_TYPE_NAMES = {
    descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE: "double",
    descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT: "float",
    descriptor_pb2.FieldDescriptorProto.TYPE_INT64: "int64",
    descriptor_pb2.FieldDescriptorProto.TYPE_UINT64: "uint64",
    descriptor_pb2.FieldDescriptorProto.TYPE_INT32: "int32",
    descriptor_pb2.FieldDescriptorProto.TYPE_FIXED64: "fixed64",
    descriptor_pb2.FieldDescriptorProto.TYPE_FIXED32: "fixed32",
    descriptor_pb2.FieldDescriptorProto.TYPE_BOOL: "bool",
    descriptor_pb2.FieldDescriptorProto.TYPE_STRING: "string",
    descriptor_pb2.FieldDescriptorProto.TYPE_BYTES: "bytes",
    descriptor_pb2.FieldDescriptorProto.TYPE_UINT32: "uint32",
    descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED32: "sfixed32",
    descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED64: "sfixed64",
    descriptor_pb2.FieldDescriptorProto.TYPE_SINT32: "sint32",
    descriptor_pb2.FieldDescriptorProto.TYPE_SINT64: "sint64",
}


def _short_type_name(type_name: str) -> str:
    """Strip the proto package prefix from a fully-qualified type name."""
    return type_name.lstrip(".").rsplit(".", 1)[-1]


def _anchor_for(file_stem: str, qualified_name: str) -> str:
    return f"proto-{file_stem}-{qualified_name.lower().replace('.', '-')}"


def _build_type_index(
    file_protos: Iterable[descriptor_pb2.FileDescriptorProto],
) -> dict[str, tuple[str, str]]:
    """Map fully-qualified proto type names to ``(file_stem, qualified_name)``.

    The qualified name is the dotted path within the file (e.g.
    ``Outer.Inner``) used to build anchors.
    """
    index: dict[str, tuple[str, str]] = {}

    def _walk_message(
        msg: descriptor_pb2.DescriptorProto,
        package: str,
        file_stem: str,
        qualified: str,
    ) -> None:
        full = f".{package}.{qualified}" if package else f".{qualified}"
        index[full] = (file_stem, qualified)
        for nested in msg.nested_type:
            if nested.options.map_entry:
                continue
            _walk_message(
                nested, package, file_stem, f"{qualified}.{nested.name}"
            )
        for enum in msg.enum_type:
            enum_q = f"{qualified}.{enum.name}"
            full_e = f".{package}.{enum_q}" if package else f".{enum_q}"
            index[full_e] = (file_stem, enum_q)

    for fp in file_protos:
        file_stem = Path(fp.name).stem
        package = fp.package
        for msg in fp.message_type:
            _walk_message(msg, package, file_stem, msg.name)
        for enum in fp.enum_type:
            full_e = f".{package}.{enum.name}" if package else f".{enum.name}"
            index[full_e] = (file_stem, enum.name)
    return index


def _render_type_ref(
    full_type_name: str, type_index: dict[str, tuple[str, str]]
) -> str:
    """Render a message/enum type as a clickable ``:ref:`` link if known."""
    short = _short_type_name(full_type_name)
    target = type_index.get(full_type_name)
    if target is None:
        return f"``{short}``"
    file_stem, qualified = target
    anchor = _anchor_for(file_stem, qualified)
    # ``:ref:`` cannot contain nested inline literals, so the link text is
    # rendered as plain text.
    return f":ref:`{short} <{anchor}>`"


def _render_field_type(
    field: descriptor_pb2.FieldDescriptorProto,
    type_index: dict[str, tuple[str, str]],
) -> str:
    if field.type in (
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        descriptor_pb2.FieldDescriptorProto.TYPE_ENUM,
    ):
        return _render_type_ref(field.type_name, type_index)
    return f"``{_FIELD_TYPE_NAMES.get(field.type, str(field.type))}``"


# ---------------------------------------------------------------------------
# RST emitters — paragraph / definition-list format
# ---------------------------------------------------------------------------


def _emit_metadata_block(
    out: list[str], file_proto: descriptor_pb2.FileDescriptorProto
) -> None:
    """Emit an RST field list with source file, package, and content counts.

    The field list is rendered by Sphinx as a compact description block and
    requires no custom CSS.
    """
    proto_path = f"ansys/api/fluent/v1/{Path(file_proto.name).name}"
    out.append(f":Source file: :file:`{proto_path}`")
    out.append(f":Proto package: ``{file_proto.package}``")

    counts: list[str] = []
    if file_proto.service:
        n = len(file_proto.service)
        counts.append(f"{n} service{'s' if n != 1 else ''}")
    if file_proto.message_type:
        n = len(file_proto.message_type)
        counts.append(f"{n} message{'s' if n != 1 else ''}")
    if file_proto.enum_type:
        n = len(file_proto.enum_type)
        counts.append(f"{n} enum{'s' if n != 1 else ''}")
    if counts:
        out.append(f":Contains: {', '.join(counts)}")
    out.append("")


def _emit_service(
    out: list[str],
    service: descriptor_pb2.ServiceDescriptorProto,
    service_idx: int,
    comments: dict[tuple[int, ...], str],
    file_stem: str,
    type_index: dict[str, tuple[str, str]],
) -> None:
    """Emit a service as a rubric followed by a definition list of RPCs.

    Each RPC entry shows its name as the definition term, with request/
    response types as an RST field list and the description as a body
    paragraph inside the definition.

    Example output::

        ``GetState``
           :Request: GetStateRequest
           :Response: GetStateResponse

           Retrieves the current state at a specified path.
    """
    out.append(f".. _proto-{file_stem}-service-{service.name.lower()}:")
    out.append("")
    out.append("----")
    out.append("")
    out.append(f"**Service:** **{service.name}**")
    out.append("")

    svc_doc = _clean_comment(comments.get((6, service_idx), ""))
    if svc_doc:
        out.append(svc_doc)
        out.append("")

    for method_idx, method in enumerate(service.method):
        method_doc = _clean_comment(comments.get((6, service_idx, 2, method_idx), ""))
        request_ref = _render_type_ref(method.input_type, type_index)
        response_ref = _render_type_ref(method.output_type, type_index)

        # Annotate server-streaming responses.
        if method.server_streaming:
            response_ref = f"stream of {response_ref}"

        out.append(f"``{method.name}``")
        out.append(f"   :Request: {request_ref}")
        out.append(f"   :Response: {response_ref}")
        if method_doc:
            out.append("")
            out.append(f"   {method_doc}")
        out.append("")


def _emit_message(
    out: list[str],
    msg: descriptor_pb2.DescriptorProto,
    comments: dict[tuple[int, ...], str],
    path_prefix: tuple[int, ...],
    qualified_name: str,
    file_stem: str,
    type_index: dict[str, tuple[str, str]],
) -> None:
    """Emit a message as a rubric followed by a definition list of fields.

    Each field entry uses the pattern ``N. field_name : [qualifiers] type``
    as the definition term, with the field's comment as the body paragraph.

    Example output::

        ``rules`` (1) : ``string``
           The rules context for the state query.

        ``path`` (2) : ``string``
           The path to retrieve state from.

    Nested enums and messages are emitted recursively after the field list.
    Synthetic map-entry types generated by protoc are skipped.
    """
    anchor = _anchor_for(file_stem, qualified_name)
    out.append(f".. _{anchor}:")
    out.append("")
    out.append("----")
    out.append("")
    out.append(f"**{qualified_name}**")
    out.append("")

    msg_doc = _clean_comment(comments.get(path_prefix, ""))
    if msg_doc:
        out.append(msg_doc)
        out.append("")

    if msg.field:
        oneof_names = {i: oneof.name for i, oneof in enumerate(msg.oneof_decl)}
        for field_idx, field in enumerate(msg.field):
            field_doc = _clean_comment(comments.get(path_prefix + (2, field_idx), ""))

            # Build optional qualifier prefix (repeated, oneof membership).
            qualifiers: list[str] = []
            if field.label == descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED:
                qualifiers.append("repeated")
            if field.HasField("oneof_index"):
                qualifiers.append(f"oneof {oneof_names[field.oneof_index]}")
            prefix = f"{', '.join(qualifiers)} " if qualifiers else ""

            type_repr = _render_field_type(field, type_index)
            # Term: ``field_name`` (N) : [qualifiers] type
            out.append(f"``{field.name}`` ({field.number}) : {prefix}{type_repr}")
            out.append(f"   {field_doc}" if field_doc else "   —")
            out.append("")

    # Nested enums.
    for enum_idx, enum in enumerate(msg.enum_type):
        _emit_enum(
            out,
            enum,
            comments,
            path_prefix + (4, enum_idx),
            f"{qualified_name}.{enum.name}",
            file_stem,
        )

    # Nested messages (skip synthetic map-entry types generated by protoc).
    for nested_idx, nested in enumerate(msg.nested_type):
        if nested.options.map_entry:
            continue
        _emit_message(
            out,
            nested,
            comments,
            path_prefix + (3, nested_idx),
            f"{qualified_name}.{nested.name}",
            file_stem,
            type_index,
        )


def _emit_enum(
    out: list[str],
    enum: descriptor_pb2.EnumDescriptorProto,
    comments: dict[tuple[int, ...], str],
    path_prefix: tuple[int, ...],
    qualified_name: str,
    file_stem: str,
) -> None:
    """Emit an enum as a rubric followed by a definition list of values.

    Example output::

        ``DIFF_STATE_UNSPECIFIED`` (0)
           Unspecified diff state.

        ``DIFF_STATE_FULL`` (1)
           Full state including commands.
    """
    anchor = _anchor_for(file_stem, qualified_name)
    out.append(f".. _{anchor}:")
    out.append("")
    out.append("----")
    out.append("")
    out.append(f"**{qualified_name}** *(enum)*")
    out.append("")

    enum_doc = _clean_comment(comments.get(path_prefix, ""))
    if enum_doc:
        out.append(enum_doc)
        out.append("")

    for value_idx, value in enumerate(enum.value):
        value_doc = _clean_comment(comments.get(path_prefix + (2, value_idx), ""))
        out.append(f"``{value.name}`` ({value.number})")
        out.append(f"   {value_doc}" if value_doc else "   —")
        out.append("")


def _emit_file(
    file_proto: descriptor_pb2.FileDescriptorProto,
    type_index: dict[str, tuple[str, str]],
) -> str:
    """Render one proto file as a self-contained RST fragment.

    The fragment uses a ``.. rubric::`` as its top-level heading so it can be
    included under any parent section without disrupting the heading hierarchy
    of the host page.
    """
    comments = _build_comment_index(file_proto)
    file_stem = Path(file_proto.name).stem
    out: list[str] = []

    out.append(".. Auto-generated by docs/_ext/proto_docgen.py — do not edit by hand.")
    out.append("")
    out.append("**Generated reference**")
    out.append("")

    _emit_metadata_block(out, file_proto)

    if file_proto.service:
        out.append("**Services**")
        out.append("")
        for service_idx, service in enumerate(file_proto.service):
            _emit_service(out, service, service_idx, comments, file_stem, type_index)

    if file_proto.message_type:
        out.append("**Messages**")
        out.append("")
        for msg_idx, msg in enumerate(file_proto.message_type):
            _emit_message(out, msg, comments, (4, msg_idx), msg.name, file_stem, type_index)

    if file_proto.enum_type:
        out.append("**Enumerations**")
        out.append("")
        for enum_idx, enum in enumerate(file_proto.enum_type):
            _emit_enum(out, enum, comments, (5, enum_idx), enum.name, file_stem)

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Sphinx hook
# ---------------------------------------------------------------------------


def generate(app=None) -> None:
    """Compile v1 protos and write generated RST fragments to disk."""
    proto_files = sorted(_PROTO_ROOT.glob("*.proto"))
    if not proto_files:
        return

    if _OUT_DIR.exists():
        shutil.rmtree(_OUT_DIR)
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    fds = _compile_descriptor_set(proto_files)
    requested = {p.name for p in proto_files}
    emitted_files = [
        fp for fp in fds.file if Path(fp.name).name in requested
    ]
    type_index = _build_type_index(emitted_files)
    written: list[str] = []
    for file_proto in emitted_files:
        rst = _emit_file(file_proto, type_index)
        out_path = _OUT_DIR / f"{Path(file_proto.name).stem}.rst"
        out_path.write_text(rst, encoding="utf-8", errors="replace")
        written.append(out_path.name)

    # Stub index so Sphinx does not warn about an empty directory.
    (_OUT_DIR / "README.rst").write_text(
        ":orphan:\n\nAuto-generated proto reference fragments. Included from hand-written pages.\n",
        encoding="utf-8",
    )

    if app is not None:
        try:
            from sphinx.util import logging as sphinx_logging

            sphinx_logging.getLogger(__name__).info(
                "proto_docgen: regenerated %d RST fragment(s)", len(written)
            )
        except Exception:
            pass


def setup(app):
    app.connect("builder-inited", generate)
    return {"version": "0.2", "parallel_read_safe": True, "parallel_write_safe": True}


# Allow running directly (e.g. ``python docs/_ext/proto_docgen.py``).
if __name__ == "__main__":
    generate()
    print(f"Wrote generated fragments to {_OUT_DIR}")
