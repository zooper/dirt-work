# Sky, cobbles and tyre tracks

Reference: [`docs/image.png`](../../image.png).

## Gaps
1. The clouds were small, lumpy hulls that read as pink rocks floating in the sky. The reference has soft cumulus with flat bases.
2. The foreground cobble pile was dark blue-grey. The reference cobbles are warm, light grey.
3. The pit floor was uniform. The reference shows packed wheel ruts.

## Changes
- `QuarryWorld._build_clouds()`: 14 cumulus at 420–720 m with flat bases and 5–8 round overlapping puffs (120–210 m wide), sunlit white tops and soft pink undersides. It uses its own RNG stream, so forest, rubble and pebbles don't move.
- Loading-bay cobbles use the warm pile palette and are only slightly darkened.
- `SiteProps._tyre_tracks()`: Catmull-Rom wheel ruts with alternating lug tone and soft ends, for the loader's approach, the hauler's path in, and the ramp approach.

## Result
`front34.jpg` and `overview.jpg` show cumulus clouds and visible ruts. In `hero.jpg` the cobble pile is now light warm grey.
