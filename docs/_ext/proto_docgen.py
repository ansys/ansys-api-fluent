"""Sphinx extension that generates API reference fragments from .proto files.

For each ``.proto`` file under ``ansys/api/fluent/v1`` this extension produces
an RST fragment under ``docs/source/api/_generated/<basename>.rst`` containing:

* the list of RPCs defined by services in that file (with leading comments),
* every message with a table of its fields (name, type, comment),
* every enum with a table of its values.

Comments are extracted from the proto ``SourceCodeInfo`` produced by
``grpc_tools.protoc``. Hand-curated narrative pages in ``api/services``,
``api/helpers`` and ``api/legacy`` consume these fragments via an
``.. include::`` directive at the bottom of each page.
"""

from __future__ import annotations

import os
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
    return " ".join(lines)


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


def _render_field_type(field: descriptor_pb2.FieldDescriptorProto) -> str:
    if field.type in (
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        descriptor_pb2.FieldDescriptorProto.TYPE_ENUM,
    ):
        # type_name is a fully-qualified name like ".ansys.api.fluent.v1.variant.Variant".
        type_name = field.type_name.lstrip(".").rsplit(".", 1)[-1]
    else:
        type_name = _FIELD_TYPE_NAMES.get(field.type, str(field.type))
    if field.label == descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED:
        return f"repeated {type_name}"
    return type_name


def _render_rpc_type(name: str) -> str:
    return name.lstrip(".").rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# RST emission
# ---------------------------------------------------------------------------


def _heading(title: str, char: str) -> str:
    return f"{title}\n{char * len(title)}\n"


def _rst_escape_cell(text: str) -> str:
    """Escape characters that would break a list-table cell."""
    if not text:
        return ""
    return text.replace("|", r"\|")


def _emit_rpc_section(
    out: list[str],
    service: descriptor_pb2.ServiceDescriptorProto,
    service_idx: int,
    comments: dict[tuple[int, ...], str],
) -> None:
    out.append(f".. rubric:: Service ``{service.name}``")
    out.append("")
    svc_doc = _clean_comment(comments.get((6, service_idx), ""))
    if svc_doc:
        out.append(svc_doc)
        out.append("")

    if not service.method:
        return

    out.append(".. list-table::")
    out.append("   :widths: 25 30 30 30")
    out.append("   :header-rows: 1")
    out.append("")
    out.append("   * - RPC")
    out.append("     - Request")
    out.append("     - Response")
    out.append("     - Description")
    for method_idx, method in enumerate(service.method):
        method_doc = _clean_comment(comments.get((6, service_idx, 2, method_idx), ""))
        request = _render_rpc_type(method.input_type)
        response = _render_rpc_type(method.output_type)
        if method.client_streaming:
            request = f"stream {request}"
        if method.server_streaming:
            response = f"stream {response}"
        out.append(f"   * - ``{method.name}``")
        out.append(f"     - ``{request}``")
        out.append(f"     - ``{response}``")
        out.append(f"     - {_rst_escape_cell(method_doc) or '—'}")
    out.append("")


def _emit_message(
    out: list[str],
    msg: descriptor_pb2.DescriptorProto,
    comments: dict[tuple[int, ...], str],
    path_prefix: tuple[int, ...],
    qualified_name: str,
) -> None:
    out.append(f".. rubric:: ``{qualified_name}``")
    out.append("")
    msg_doc = _clean_comment(comments.get(path_prefix, ""))
    if msg_doc:
        out.append(msg_doc)
        out.append("")

    if msg.field:
        out.append(".. list-table::")
        out.append("   :widths: 25 25 50")
        out.append("   :header-rows: 1")
        out.append("")
        out.append("   * - Field")
        out.append("     - Type")
        out.append("     - Description")
        for field_idx, field in enumerate(msg.field):
            field_doc = _clean_comment(comments.get(path_prefix + (2, field_idx), ""))
            out.append(f"   * - ``{field.name}``")
            out.append(f"     - ``{_render_field_type(field)}``")
            out.append(f"     - {_rst_escape_cell(field_doc) or '—'}")
        out.append("")

    # Nested enums
    for enum_idx, enum in enumerate(msg.enum_type):
        _emit_enum(
            out,
            enum,
            comments,
            path_prefix + (4, enum_idx),
            f"{qualified_name}.{enum.name}",
        )

    # Nested messages (skip synthetic map entries)
    for nested_idx, nested in enumerate(msg.nested_type):
        if nested.options.map_entry:
            continue
        _emit_message(
            out,
            nested,
            comments,
            path_prefix + (3, nested_idx),
            f"{qualified_name}.{nested.name}",
        )


def _emit_enum(
    out: list[str],
    enum: descriptor_pb2.EnumDescriptorProto,
    comments: dict[tuple[int, ...], str],
    path_prefix: tuple[int, ...],
    qualified_name: str,
) -> None:
    out.append(f".. rubric:: ``{qualified_name}`` (enum)")
    out.append("")
    enum_doc = _clean_comment(comments.get(path_prefix, ""))
    if enum_doc:
        out.append(enum_doc)
        out.append("")
    out.append(".. list-table::")
    out.append("   :widths: 35 15 50")
    out.append("   :header-rows: 1")
    out.append("")
    out.append("   * - Name")
    out.append("     - Number")
    out.append("     - Description")
    for value_idx, value in enumerate(enum.value):
        value_doc = _clean_comment(comments.get(path_prefix + (2, value_idx), ""))
        out.append(f"   * - ``{value.name}``")
        out.append(f"     - {value.number}")
        out.append(f"     - {_rst_escape_cell(value_doc) or '—'}")
    out.append("")


def _emit_file(file_proto: descriptor_pb2.FileDescriptorProto) -> str:
    comments = _build_comment_index(file_proto)
    out: list[str] = []
    out.append(".. Auto-generated by docs/_ext/proto_docgen.py — do not edit by hand.")
    out.append("")
    # Top-level heading uses the H2 marker (``-``) so the fragment nests as a
    # sibling of the parent page's existing top-level sections. All deeper
    # subdivisions inside the fragment use ``.. rubric::`` directives, which
    # behave like headings visually but do not participate in the section
    # hierarchy. This keeps the fragment compatible with any parent page
    # heading convention.
    out.append(_heading("Generated reference", "-"))
    out.append(
        f"Generated from :file:`ansys/api/fluent/v1/{Path(file_proto.name).name}`. "
        f"Proto package: ``{file_proto.package}``."
    )
    out.append("")

    for service_idx, service in enumerate(file_proto.service):
        _emit_rpc_section(out, service, service_idx, comments)

    if file_proto.message_type:
        out.append(".. rubric:: Messages")
        out.append("")
        for msg_idx, msg in enumerate(file_proto.message_type):
            _emit_message(out, msg, comments, (4, msg_idx), msg.name)

    if file_proto.enum_type:
        out.append(".. rubric:: Enumerations")
        out.append("")
        for enum_idx, enum in enumerate(file_proto.enum_type):
            _emit_enum(out, enum, comments, (5, enum_idx), enum.name)

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
    written: list[str] = []
    for file_proto in fds.file:
        # Skip transitive imports we did not request explicitly.
        if Path(file_proto.name).name not in requested:
            continue
        rst = _emit_file(file_proto)
        out_path = _OUT_DIR / f"{Path(file_proto.name).stem}.rst"
        out_path.write_text(rst, encoding="utf-8")
        written.append(out_path.name)

    # Stub index so Sphinx does not warn about an empty directory.
    (_OUT_DIR / "README.rst").write_text(
        ":orphan:\n\nAuto-generated proto reference fragments. Included from hand-written pages.\n",
        encoding="utf-8",
    )

    if app is not None:
        app.info = getattr(app, "info", lambda *_: None)
        try:
            from sphinx.util import logging as sphinx_logging

            sphinx_logging.getLogger(__name__).info(
                "proto_docgen: regenerated %d RST fragment(s)", len(written)
            )
        except Exception:
            pass


def _on_builder_inited(app) -> None:
    generate(app)


def setup(app):
    app.connect("builder-inited", _on_builder_inited)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}


# Allow running directly (e.g. ``python docs/_ext/proto_docgen.py``).
if __name__ == "__main__":
    generate()
    print(f"Wrote generated fragments to {_OUT_DIR}")
