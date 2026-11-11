# Dirt Work — Game Design (draft)

## Pillars
1. Satisfying, accessible heavy machinery operation with weighty movement and convincing sound.
2. Visible, persistent impact on the world: move gravel, shape ground, clear snow.
3. Earn money from jobs and reinvest in equipment and upgrades.
4. Premium stylized low-poly Nordic environments with readable silhouettes and lighting.

## First playable loop
Enter a quarry → drive a wheel loader → scoop an abstract amount of gravel → tip into a truck or delivery trigger → earn a contract reward → repeat.

## First vehicle
Articulated wheel loader: throttle, reverse, steering, brake, lift arms, tilt bucket, camera orbit/reset. Keyboard and Xbox-style gamepad support. Begin with simple collision and suspension approximations; tune feel before adding simulation fidelity.

## Materials
Start with a deterministic material inventory: each pile has volume, each bucket has capacity, delivery converts volume to weight using a defined density. Represent scooping and dumping with simple meshes/particles. Avoid individual rock rigid bodies and expensive terrain deformation in MVP.

## Future features (not MVP)
Dump trucks, bulldozers, excavators; seasonal snow removal; dynamic weather; company finances, repairs and contracts; AI workers; multiplayer; Xbox release.

## Art direction
Premium low-poly: faceted rocks, stylized Scandinavian pines, believable machine proportions, bright readable color palette, soft shadows, dust and snow effects. Avoid realistic licensed branding.

## Success criteria
A first-time player can drive, scoop, dump, and complete a job with a controller in under five minutes. Stable performance on a modest Mac is more important than advanced visual effects.
