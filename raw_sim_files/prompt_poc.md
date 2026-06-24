# Porter POC — Quick Visual Demo
## Goal
Build a single HTML file that shows a person following a Porter cart through an isometric grocery store. This is a visual proof of concept only. No data, no analytics, no plumbing.

---

## Assets Available
All assets are in the same directory as this file:

- `AdobeStock_1891565163.png` — Isometric store scene (left side) + isolated elements (right side): shelves, people, carts, checkout. Transparent background.
- `AdobeStock_1810976829.png` — Isometric woman pushing a full grocery cart. Transparent background.

---

## What to Build
A single `index.html` file using HTML5 Canvas.

### Scene Setup
- Canvas size: 1280x720px
- Use the LEFT side of `AdobeStock_1891565163.png` as the static store background
- Crop and position it to fill the canvas nicely

### Animation
- Extract or approximate a **Porter cart sprite** from the assets — a simple isometric cart shape (can be drawn with canvas if extraction is complex)
- Extract or use `AdobeStock_1810976829.png` as the **shopper sprite**
- The cart leads — it moves along a simple pre-defined waypoint path through the store aisles
- The shopper follows ~80px behind the cart, mirroring its path with a slight lag
- Path should visually go through at least 3 sections of the store (e.g. entrance → produce aisle → dairy → checkout)
- Movement should be smooth (linear interpolation between waypoints)
- Loop the animation after reaching checkout

### UI Overlays
- Small label above the cart: **"Porter"** with a blue dot
- When cart reaches each waypoint/section, briefly show a popup: e.g. **"Navigating to Dairy →"**
- Bottom left corner: **"Porter by Offload Robotics"** watermark text

### Visual Polish
- Smooth movement, no snapping
- Cart slightly ahead of shopper at all times
- Faint dotted trail behind the cart showing its path
- Popups fade in/out smoothly

---

## Tech Requirements
- Single `index.html` file, no dependencies, no npm, no build step
- Vanilla HTML + CSS + JavaScript only
- Canvas 2D API for rendering
- Must run by simply opening `index.html` in a browser

---

## Out of Scope
- No pathfinding algorithms
- No data logging
- No multiple carts
- No backend
- No user interaction needed

---

## Success Criteria
Opening `index.html` in Chrome shows a smooth looping animation of a Porter cart leading a shopper through the isometric store. Looks good enough to screen record for a pitch.
