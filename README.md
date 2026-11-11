# Dirt Work

A stylized low-poly heavy equipment game prototype built with Godot 4 and GDScript.

## Goal
Drive a wheel loader in a Nordic gravel quarry, load material into a dump truck, and earn money from contracts. Later: snow clearing, seasons, fleet management and Xbox exploration.

## Development
Linux server over SSH, Claude Code for implementation, macOS for hands-on playtesting. See `CLAUDE.md` and `docs/GAME_DESIGN.md` after merging the bootstrap PR.

## Status
M1 in progress: drivable wheel loader in a blockout quarry (`scenes/levels/quarry.tscn`). Not yet playtested on macOS.

## Controls
| Action | Keyboard | Gamepad (Xbox layout) |
|---|---|---|
| Throttle | W / Up | RT |
| Brake / reverse | S / Down | LT |
| Steer | A, D / Left, Right | Left stick X |
| Handbrake | Space | A |
| Lift arms up / down | I / K | Right stick Y |
| Curl bucket / dump | J / L | Right stick X |
| Orbit camera | Q / E | LB / RB |
| Reset camera | C | R3 |
| Screenshot | F12 | View |

Holding brake when nearly stopped reverses; throttle while reversing brakes.

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
