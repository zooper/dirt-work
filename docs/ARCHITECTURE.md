# Architecture notes

Godot 4 GDScript; scenes compose visual/physics entities. Scripts under scripts/vehicles, scripts/gameplay and scripts/core. Use InputMap actions for every player control. Material quantities should be deterministic game state independent of visual particle effects. Keep rendering and physics settings conservative for macOS and possible console ports. Prefer data-driven contract definitions (Resources) once the first loop works. Avoid premature networking, native plugins and platform APIs.

Headless CI checks import and engine startup, not visual correctness or gameplay feel. Test on macOS with a controller after each milestone.
