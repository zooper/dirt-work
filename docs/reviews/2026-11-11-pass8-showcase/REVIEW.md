# Pass 8 — showcase loading bay (state after passes 2–8)

Reference: `docs/image.png`. Full review set in this folder (Mobile preview renderer on the Linux host, **fog/SSAO/SSIL off** — the Mac's Forward+ adds haze, contact shadows and bounce light).

## This pass
Loading-bay dressing in `SiteProps._loading_bay()`: angular cobble stockpile (foreground right in `hero.jpg`), big boulders, a lone pine at the bay edge, a floodlight among the site buildings. All have simple collision and sit in the yard, outside the driving-test area.

## Where we are vs the reference (`hero.jpg`)
Matches in layout and content: loader at left in rear-quarter view with fictional "DW-90" on the hood, bucket raised over an articulated "DW-40" hauler loaded with gravel, conveyors/crusher behind, floodlight, lake + forested hills + snowy mountains at left, terraced faceted cliffs at right, pine and boulders framing the left, cobble pile bottom-right, warm low sun from the camera side.

Remaining gaps (largest first):
1. **Atmosphere** — no visible dust/haze in these previews (fog disabled on the software renderer; the pour stream is subtle). Needs checking in Forward+ on the Mac.
2. **Material response** — surfaces are clean and uniformly saturated; the reference has worn steel, dirt on tyres/lower body, roughness variation.
3. **Upper bench activity** — the reference shows an excavator and a second hauler on a terrace; not built.
4. **Model detail** — the reference's boom has visible twin lift cylinders and hoses, the bucket a heavier profile, the hood more panel breaks; tyres have deeper blocks.
5. **Cliff at frame right** is a flat-lit end face rather than terraced shaded rock.

Tests: `tests/check.sh` passes (all checks, no script errors).
