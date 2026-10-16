#!/usr/bin/env python3
"""Headless Blender MCP server.

Blender runs in-process as the `bpy` module (PyPI `bpy`, Blender built as a Python module), so there
is no `blender` binary, no GUI, no addon socket and no display. One persistent scene lives in the
server process; tools edit it, render it and save it.

Transport: MCP over stdio, JSON-RPC 2.0, one message per line (stdlib only, single thread, because
bpy must stay on the thread that imported it).

Blender prints render logs to stdout, which would corrupt the protocol stream, so fd 1 is pointed
at stderr at start-up and the protocol writes to a private duplicate of the original stdout.
"""
import base64
import contextlib
import io
import json
import os
import sys
import traceback

PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]
SERVER_INFO = {"name": "mta-blender-headless", "version": "0.1.0"}

_proto_out = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
os.dup2(2, 1)
sys.stdout = sys.stderr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sneakpeek", "blender"))

import bpy  # noqa: E402
import mta3d  # noqa: E402

NS = {"bpy": bpy, "mta3d": mta3d, "M": mta3d}


def _text(s):
    return {"type": "text", "text": s}


def _image_block(path, max_side=None):
    data = open(path, "rb").read()
    if max_side:
        try:
            from PIL import Image
            im = Image.open(path)
            if max(im.size) > max_side:
                im.thumbnail((max_side, max_side))
                buf = io.BytesIO()
                im.save(buf, "PNG")
                data = buf.getvalue()
        except ImportError:
            pass
    return {"type": "image", "data": base64.b64encode(data).decode(), "mimeType": "image/png"}


def _exec(code, filename="<run_python>"):
    out = io.StringIO()
    NS.pop("result", None)
    with contextlib.redirect_stdout(out):
        exec(compile(code, filename, "exec"), NS)
    return out.getvalue(), NS.get("result")


def tool_run_python(code):
    printed, result = _exec(code)
    body = {"output": printed[-20000:], "result": result}
    return [_text(json.dumps(body, default=str, indent=1))]


def tool_run_file(path, args=None):
    NS["ARGS"] = args or {}
    NS["__file__"] = os.path.abspath(path)
    printed, result = _exec(open(path, encoding="utf-8").read(), os.path.abspath(path))
    return [_text(json.dumps({"output": printed[-20000:], "result": result}, default=str, indent=1))]


def tool_scene_info():
    return [_text(json.dumps(mta3d.info(), indent=1))]


def tool_render_frame(frame=None, path=None, max_side=640, samples=None, inline=True):
    path = path or os.path.join(os.environ.get("TMPDIR", "/tmp"), "mta-blender-frame.png")
    mta3d.render_still(path, frame=frame, samples=samples)
    blocks = [_text(json.dumps({"path": path}))]
    if inline:
        blocks.append(_image_block(path, max_side))
    return blocks


def tool_render_sequence(out_dir, start=None, end=None, samples=None):
    files = mta3d.render_sequence(out_dir, start=start, end=end, samples=samples)
    return [_text(json.dumps({"out_dir": out_dir, "frames": len(files), "first": files[0] if files else None}))]


def tool_save_blend(path):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path), copy=True)
    return [_text(json.dumps({"saved": os.path.abspath(path)}))]


def tool_open_blend(path):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path))
    return tool_scene_info()


def tool_reset(width=1280, height=720, fps=20, duration=5.0, transparent=True):
    mta3d.reset(width, height, fps, duration, transparent)
    return tool_scene_info()


TOOLS = {
    "run_python": (tool_run_python, "Run Python in the persistent Blender session. `bpy` and `mta3d` (alias `M`, the MTA 3D helpers: text3d, svg3d, mat, key, cam, rig3, render_sequence...) are in scope. Assign `result` to return a value; print() output is returned too.",
                   {"code": {"type": "string"}}, ["code"]),
    "run_file": (tool_run_file, "Run a Python scene file in the session (same scope as run_python; `ARGS` holds `args`).",
                 {"path": {"type": "string"}, "args": {"type": "object"}}, ["path"]),
    "scene_info": (tool_scene_info, "Objects, camera, frame range, fps, resolution and render engine of the current scene.", {}, []),
    "render_frame": (tool_render_frame, "Render one frame (Cycles CPU by default) to a PNG and return it inline.",
                     {"frame": {"type": "integer"}, "path": {"type": "string"}, "max_side": {"type": "integer"}, "samples": {"type": "integer"}, "inline": {"type": "boolean"}}, []),
    "render_sequence": (tool_render_sequence, "Render the frame range to an RGBA PNG sequence (f_0001.png...) for EffectCraft to import as footage.",
                        {"out_dir": {"type": "string"}, "start": {"type": "integer"}, "end": {"type": "integer"}, "samples": {"type": "integer"}}, ["out_dir"]),
    "save_blend": (tool_save_blend, "Save the session as a .blend file.", {"path": {"type": "string"}}, ["path"]),
    "open_blend": (tool_open_blend, "Open a .blend file into the session.", {"path": {"type": "string"}}, ["path"]),
    "reset": (tool_reset, "Empty the scene and set the MTA defaults (1280x720, 20 fps, 5 s, transparent film, Cycles CPU).",
              {"width": {"type": "integer"}, "height": {"type": "integer"}, "fps": {"type": "integer"}, "duration": {"type": "number"}, "transparent": {"type": "boolean"}}, []),
}


def tools_list():
    return [{"name": n, "description": d, "inputSchema": {"type": "object", "properties": p, "required": r, "additionalProperties": False}}
            for n, (_, d, p, r) in TOOLS.items()]


def handle(msg):
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if method == "initialize":
        want = params.get("protocolVersion")
        return {"protocolVersion": want if want in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
                "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO,
                "instructions": "Headless Blender " + bpy.app.version_string + " (bpy module). Build 3D elements, render RGBA PNG "
                                "sequences with render_sequence, then import them into EffectCraft as footage."}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": tools_list()}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        if name not in TOOLS:
            raise ValueError("unknown tool " + str(name))
        try:
            return {"content": TOOLS[name][0](**args), "isError": False}
        except Exception:
            return {"content": [_text(traceback.format_exc(limit=8))], "isError": True}
    if mid is None:
        return None  # notification
    raise LookupError("method not found: " + str(method))


def main():
    mta3d.reset()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            _proto_out.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}) + "\n")
            continue
        mid = msg.get("id")
        try:
            res = handle(msg)
            if mid is not None:
                _proto_out.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}) + "\n")
        except LookupError as e:
            _proto_out.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": str(e)}}) + "\n")
        except Exception as e:
            _proto_out.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}}) + "\n")


if __name__ == "__main__":
    main()
