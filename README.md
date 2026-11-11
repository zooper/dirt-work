# Dirt Work

A stylized low-poly heavy equipment game prototype built with Godot 4 and GDScript.

## Goal
Drive a wheel loader in a Nordic gravel quarry, load material into a dump truck, and earn money from contracts. Later: snow clearing, seasons, fleet management and Xbox exploration.

## Development
Linux server over SSH, Claude Code for implementation, macOS for hands-on playtesting. See `CLAUDE.md` and `docs/GAME_DESIGN.md` after merging the bootstrap PR.

## Status
M1 in progress: drivable wheel loader in a blockout quarry (`scenes/levels/quarry.tscn`). Not yet playtested on macOS.

## Controls
Defaults follow Farming Simulator conventions.

| Action | Keyboard / mouse | Gamepad (Xbox layout) |
|---|---|---|
| Accelerate | W | RT |
| Brake / reverse | S | LT |
| Steer | A / D | Left stick |
| Front loader arm up / down | J / N, or hold left mouse + move mouse up/down | Hold LB + right stick up/down |
| Bucket curl / dump | K / M, or hold left mouse + move mouse left/right | Hold LB + right stick left/right |
| Look around | Mouse, arrow keys | Right stick |
| Switch camera (chase / cab) | C | Right stick click (R3) |
| Zoom camera | Mouse wheel, Page Up / Page Down | D-pad up / down |
| Cruise control on / off | 3 | Y |
| Cruise speed slower / faster | 1 / 2 | D-pad left / right |
| Handbrake | Space | A |
| Screenshot | F12 | View |

Holding brake when nearly stopped reverses; throttle while reversing brakes. The mouse is captured while playing; Esc releases it, a click recaptures it.

## Checks
```bash
tests/check.sh   # import + boot + tests; fails on any script error
```
Render review shots on a machine with a display (or Xvfb):
```bash
DISPLAY=:0 godot --path . --resolution 1600x900 -s tools/capture_shots.gd -- /tmp/shots
```
The loader scene is generated: edit `tools/gen_wheel_loader.py`, then run it.

Screenshots (F12) are saved to `~/Library/Application Support/Godot/app_userdata/Dirt Work/screenshots/` on macOS.
