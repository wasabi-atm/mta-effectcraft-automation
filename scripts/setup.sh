#!/usr/bin/env bash
# setup.sh - install the headless toolchain into this repo (idempotent; safe to re-run).
#
#   .tools/bin/effectcraft-cli   EffectCraft, built from source at a pinned commit (needs Rust >= 1.95)
#   .venv/                       Python 3.13 with bpy (Blender as a module), Pillow, requests
#
# Options: --with-brand  also install Playwright + Chromium for `sneakpeek brand`
#          --skip-effectcraft / --skip-blender
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EC_REPO="https://github.com/storytold/effectcraft.git"
EC_REV="${EFFECTCRAFT_REV:-08627d4afa39f3ed09fb0fee03ab8d19aab35fb1}"   # 2026-10-15, v0.10.0
BPY_VERSION="${BPY_VERSION:-5.2.2}"                                      # Blender 5.2.2 LTS, needs Python 3.13
WITH_BRAND=0; SKIP_EC=0; SKIP_BL=0
for a in "$@"; do case "$a" in
  --with-brand) WITH_BRAND=1 ;; --skip-effectcraft) SKIP_EC=1 ;; --skip-blender) SKIP_BL=1 ;;
  *) echo "unknown option $a"; exit 2 ;; esac; done

say() { printf '\n== %s\n' "$*"; }

# ---- system packages: ffmpeg (GIF encode), libegl1 (only for EEVEE/Workbench; Cycles needs none)
if ! command -v ffmpeg >/dev/null 2>&1 && [ "$(id -u)" = 0 ] && command -v apt-get >/dev/null; then
  say "apt: ffmpeg"; apt-get update -qq && apt-get install -y -qq ffmpeg
fi

# ---- EffectCraft
if [ "$SKIP_EC" = 0 ]; then
  BIN="$ROOT/.tools/bin/effectcraft-cli"; STAMP="$ROOT/.tools/bin/.effectcraft-rev"
  if [ -x "$BIN" ] && [ "$(cat "$STAMP" 2>/dev/null)" = "$EC_REV" ]; then
    say "effectcraft-cli $EC_REV already built"
  else
    command -v cargo >/dev/null || { echo "cargo not found: install Rust >= 1.95 (https://rustup.rs)"; exit 1; }
    SRC="$ROOT/.tools/src/effectcraft"
    say "effectcraft source @ $EC_REV"
    if [ ! -d "$SRC/.git" ]; then git init -q "$SRC"; git -C "$SRC" remote add origin "$EC_REPO"; fi
    git -C "$SRC" fetch -q --depth 1 origin "$EC_REV"
    git -C "$SRC" checkout -q --force FETCH_HEAD
    say "cargo build --release -p effectcraft-cli (first build ~20-30 min on 4 cores)"
    (cd "$SRC" && cargo build --release -p effectcraft-cli)
    mkdir -p "$ROOT/.tools/bin"
    cp "$SRC/target/release/effectcraft-cli" "$BIN"
    echo "$EC_REV" > "$STAMP"
  fi
fi

# ---- Blender (bpy) + Python deps
if [ "$SKIP_BL" = 0 ]; then
  say "python venv (.venv, Python 3.13) with bpy==$BPY_VERSION"
  if command -v uv >/dev/null 2>&1; then
    [ -x "$ROOT/.venv/bin/python" ] || uv venv -q -p 3.13 "$ROOT/.venv"
    VIRTUAL_ENV="$ROOT/.venv" uv pip install -q "bpy==$BPY_VERSION" pillow requests
    [ "$WITH_BRAND" = 1 ] && VIRTUAL_ENV="$ROOT/.venv" uv pip install -q playwright
  else
    [ -x "$ROOT/.venv/bin/python" ] || python3.13 -m venv "$ROOT/.venv"
    "$ROOT/.venv/bin/pip" install -q "bpy==$BPY_VERSION" pillow requests
    [ "$WITH_BRAND" = 1 ] && "$ROOT/.venv/bin/pip" install -q playwright
  fi
  if [ "$WITH_BRAND" = 1 ] && [ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]; then
    "$ROOT/.venv/bin/python" -m playwright install chromium
  fi
fi

say "doctor"
"$ROOT/bin/sneakpeek" doctor || true
