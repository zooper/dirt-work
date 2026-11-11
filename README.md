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

Holding brake when nearly stopped reverses; throttle while reversing brakes.

## Checks
```bash
godot --headless --path . --editor --import --quit
godot --headless --path . --quit-after 60
godot --headless --path . -s tests/run_tests.gd
```
