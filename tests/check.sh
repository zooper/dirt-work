#!/usr/bin/env bash
# Full headless validation: import, boot main scene, run tests.
# Fails on test failures AND on any engine/script error in the output.
set -uo pipefail
GODOT="${GODOT:-godot}"
cd "$(dirname "$0")/.."
log="$(mktemp)"
status=0
"$GODOT" --headless --path . --editor --import --quit >"$log" 2>&1 || status=1
"$GODOT" --headless --path . --quit-after 120 >>"$log" 2>&1 || status=1
"$GODOT" --headless --path . -s tests/run_tests.gd >>"$log" 2>&1 || status=1
for test in tests/bucket_material_test.gd tests/material_field_test.gd tests/material_gameplay_test.gd; do
  "$GODOT" --headless --path . -s "$test" >>"$log" 2>&1 || status=1
done
grep -E "^\s+(ok|FAIL)|TESTS" "$log"
# Known headless-only noise: the dummy renderer logs this for any Label3D
# (reproducible with a bare Label3D in Godot 4.3). Everything else is fatal.
if grep -vE 'Parameter "m" is null' "$log" | grep -E "SCRIPT ERROR|^ERROR:|Parse Error"; then
	echo "Engine/script errors found (see above)."
	status=1
fi
rm -f "$log"
exit $status
