"""Sphinx extension that generates API reference fragments from .proto files.

For each ``.proto`` file under ``ansys/api/fluent/v1`` this extension produces
an RST fragment under ``docs/source/api/_generated/<basename>.rst`` containing:

* a metadata block (source file, proto package, content counts),
* the list of RPCs defined by services in that file (with leading comments),
* every message with a table of its fields (name, tag, type, comment),
* every enum with a table of its values.

Comments are extracted from the proto ``SourceCodeInfo`` produced by
``grpc_tools.protoc``. Hand-curated narrative pages in ``api/services``,
``api/helpers`` and ``api/legacy`` consume these fragments via an
``.. include::`` directive at the bottom of each page.

The matching stylesheet at ``docs/source/_static/proto_docgen.css`` controls
the visual layout of the generated blocks.
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

# Indentation used inside ``.. container::`` directive bodies.
_INDENT = "   "


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


def _short_type_name(type_name: str) -> str:
    """Strip the proto package prefix from a fully-qualified type name."""
    return type_name.lstrip(".").rsplit(".", 1)[-1]


def _render_field_type(field: descriptor_pb2.FieldDescriptorProto) -> str:
    if field.type in (
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        descriptor_pb2.FieldDescriptorProto.TYPE_ENUM,
    ):
        return _short_type_name(field.type_name)
    return _FIELD_TYPE_NAMES.get(field.type, str(field.type))


# ---------------------------------------------------------------------------
# RST emission helpers
# ---------------------------------------------------------------------------


def _heading(title: str, char: str) -> str:
    return f"{title}\n{char * len(title)}\n"


def _rst_escape_cell(text: str) -> str:
    """Escape characters that would break a list-table cell."""
    if not text:
        return ""
    return text.replace("|", r"\|")


def _qualifier_badges(field: descriptor_pb2.FieldDescriptorProto, oneof_name: str | None) -> str:
    """Return inline ``:guilabel:`` badges describing a field's qualifiers."""
    badges: list[str] = []
    if field.label == descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED:
        badges.append(":guilabel:`repeated`")
    if oneof_name is not None:
        badges.append(f":guilabel:`oneof: {oneof_name}`")
    return " ".join(badges)


def _emit_list_table_header(out: list[str], indent: str, headers: list[tuple[str, int]]) -> None:
    widths = " ".join(str(w) for _, w in headers)
    out.append(f"{indent}.. list-table::")
    out.append(f"{indent}   :widths: {widths}")
    out.append(f"{indent}   :header-rows: 1")
    out.append(f"{indent}   :class: proto-table")
    out.append("")
    for i, (title, _) in enumerate(headers):
        marker = "* - " if i == 0 else "  - "
        out.append(f"{indent}   {marker}{title}")


def _emit_list_table_row(out: list[str], indent: str, cells: list[str]) -> None:
    for i, cell in enumerate(cells):
        marker = "* - " if i == 0 else "  - "
        out.append(f"{indent}   {marker}{cell}")


# ---------------------------------------------------------------------------
# Section emitters
# ---------------------------------------------------------------------------


def _emit_service(
    out: list[str],
    service: descriptor_pb2.ServiceDescriptorProto,
    service_idx: int,
    comments: dict[tuple[int, ...], str],
    file_stem: str,
) -> None:
    out.append(f".. _proto-{file_stem}-service-{service.name.lower()}:")
    out.append("")
    out.append(".. container:: proto-block proto-service")
    out.append("")
    out.append(f"{_INDENT}.. rubric:: Service ``{service.name}``")
    out.append("")

    svc_doc = _clean_comment(comments.get((6, service_idx), ""))
    if svc_doc:
        out.append(f"{_INDENT}.. container:: proto-doc")
        out.append("")
        out.append(f"{_INDENT}{_INDENT}{svc_doc}")
        out.append("")

    if not service.method:
        return

    _emit_list_table_header(
        out,
        _INDENT,
        [("RPC", 22), ("Request", 26), ("Response", 26), ("Description", 36)],
    )
    for method_idx, method in enumerate(service.method):
        method_doc = _clean_comment(comments.get((6, service_idx, 2, method_idx), ""))
        request = _short_type_name(method.input_type)
        response = _short_type_name(method.output_type)
        request_cell = (
            f":guilabel:`stream` ``{request}``" if method.client_streaming else f"``{request}``"
        )
        response_cell = (
            f":guilabel:`stream` ``{response}``" if method.server_streaming else f"``{response}``"
        )
        _emit_list_table_row(
            out,
            _INDENT,
            [
                f"``{method.name}``",
                request_cell,
                response_cell,
                _rst_escape_cell(method_doc) or "—",
            ],
        )
    out.append("")


def _emit_message(
    out: list[str],
    msg: descriptor_pb2.DescriptorProto,
    comments: dict[tuple[int, ...], str],
    path_prefix: tuple[int, ...],
    qualified_name: str,
    file_stem: str,
) -> None:
    anchor = f"proto-{file_stem}-{qualified_name.lower().replace('.', '-')}"
    out.append(f".. _{anchor}:")
    out.append("")
    out.append(".. container:: proto-block proto-message")
    out.append("")
    out.append(f"{_INDENT}.. rubric:: ``{qualified_name}``")
    out.append("")

    msg_doc = _clean_comment(comments.get(path_prefix, ""))
    if msg_doc:
        out.append(f"{_INDENT}.. container:: proto-doc")
        out.append("")
        out.append(f"{_INDENT}{_INDENT}{msg_doc}")
        out.append("")

    if msg.field:
        oneof_names = {i: oneof.name for i, oneof in enumerate(msg.oneof_decl)}
        _emit_list_table_header(
            out,
            _INDENT,
            [("Field", 22), ("#", 6), ("Type", 22), ("Description", 50)],
        )
        for field_idx, field in enumerate(msg.field):
            field_doc = _clean_comment(comments.get(path_prefix + (2, field_idx), ""))
            oneof_name = (
                oneof_names.get(field.oneof_index)
                if field.HasField("oneof_index")
                else None
            )
            qualifiers = _qualifier_badges(field, oneof_name)
            type_repr = f"``{_render_field_type(field)}``"
            type_cell = f"{qualifiers} {type_repr}" if qualifiers else type_repr
            _emit_list_table_row(
                out,
                _INDENT,
                [
                    f"``{field.name}``",
                    str(field.number),
                    type_cell,
                    _rst_escape_cell(field_doc) or "—",
                ],
            )
        out.append("")

    # Nested enums
    for enum_idx, enum in enumerate(msg.enum_type):
        _emit_enum(
            out,
            enum,
            comments,
            path_prefix + (4, enum_idx),
            f"{qualified_name}.{enum.name}",
            file_stem,
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
            file_stem,
        )


def _emit_enum(
    out: list[str],
    enum: descriptor_pb2.EnumDescriptorProto,
    comments: dict[tuple[int, ...], str],
    path_prefix: tuple[int, ...],
    qualified_name: str,
    file_stem: str,
) -> None:
    anchor = f"proto-{file_stem}-{qualified_name.lower().replace('.', '-')}"
    out.append(f".. _{anchor}:")
    out.append("")
    out.append(".. container:: proto-block proto-enum")
    out.append("")
    out.append(f"{_INDENT}.. rubric:: ``{qualified_name}`` (enum)")
    out.append("")

    enum_doc = _clean_comment(comments.get(path_prefix, ""))
    if enum_doc:
        out.append(f"{_INDENT}.. container:: proto-doc")
        out.append("")
        out.append(f"{_INDENT}{_INDENT}{enum_doc}")
        out.append("")

    _emit_list_table_header(
        out,
        _INDENT,
        [("Name", 32), ("#", 6), ("Description", 60)],
    )
    for value_idx, value in enumerate(enum.value):
        value_doc = _clean_comment(comments.get(path_prefix + (2, value_idx), ""))
        _emit_list_table_row(
            out,
            _INDENT,
            [
                f"``{value.name}``",
                str(value.number),
                _rst_escape_cell(value_doc) or "—",
            ],
        )
    out.append("")


def _emit_group_heading(out: list[str], title: str) -> None:
    out.append(".. rst-class:: proto-group-heading")
    out.append("")
    out.append(title)
    out.append("")


def _emit_metadata_block(out: list[str], file_proto: descriptor_pb2.FileDescriptorProto) -> None:
    """Emit a styled metadata header (source file + proto package) on
    separate lines using an RST field list inside a styled container.
    """
    proto_path = f"ansys/api/fluent/v1/{Path(file_proto.name).name}"
    out.append(".. container:: proto-meta")
    out.append("")
    out.append(f"{_INDENT}:Source file: :file:`{proto_path}`")
    out.append(f"{_INDENT}:Proto package: ``{file_proto.package}``")

    counts: list[str] = []
    if file_proto.service:
        n = len(file_proto.service)
        counts.append(f"{n} service" + ("s" if n != 1 else ""))
    if file_proto.message_type:
        n = len(file_proto.message_type)
        counts.append(f"{n} message" + ("s" if n != 1 else ""))
    if file_proto.enum_type:
        n = len(file_proto.enum_type)
        counts.append(f"{n} enum" + ("s" if n != 1 else ""))
    if counts:
        out.append(f"{_INDENT}:Contains: {', '.join(counts)}")
    out.append("")


def _emit_file(file_proto: descriptor_pb2.FileDescriptorProto) -> str:
    comments = _build_comment_index(file_proto)
    file_stem = Path(file_proto.name).stem
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

    _emit_metadata_block(out, file_proto)

    if file_proto.service:
        _emit_group_heading(out, "Services")
        for service_idx, service in enumerate(file_proto.service):
            _emit_service(out, service, service_idx, comments, file_stem)

    if file_proto.message_type:
        _emit_group_heading(out, "Messages")
        for msg_idx, msg in enumerate(file_proto.message_type):
            _emit_message(out, msg, comments, (4, msg_idx), msg.name, file_stem)

    if file_proto.enum_type:
        _emit_group_heading(out, "Enumerations")
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
    return {"version": "0.2", "parallel_read_safe": True, "parallel_write_safe": True}


# Allow running directly (e.g. ``python docs/_ext/proto_docgen.py``).
if __name__ == "__main__":
    generate()
    print(f"Wrote generated fragments to {_OUT_DIR}")
