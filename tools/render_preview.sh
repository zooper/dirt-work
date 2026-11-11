#!/usr/bin/env bash
# Renders review shots (tools/capture_shots.gd) on a display-less Linux host using
# Xvfb + Mesa lavapipe. Forward+ crashes on lavapipe in Godot 4.3, so previews use
# the Mobile renderer: same materials/shadows/glow/tonemap, but NO SSAO/SSIL,
# and fog is disabled (lavapipe crashes on it).
# Usage: XVFB_DISPLAY=:97 VK_ICD_FILENAMES=/path/lvp_icd.json tools/render_preview.sh <out_dir>
set -euo pipefail
out="${1:?out dir}"
cd "$(dirname "$0")/.."
DW_PREVIEW_NO_FOG=1 DISPLAY="${XVFB_DISPLAY:-:97}" "${GODOT:-godot}" --rendering-method mobile --audio-driver Dummy \
	--path . --resolution 1600x900 -s tools/capture_shots.gd -- "$out" 2>&1 | grep -E "saved|SCRIPT ERROR" || true
