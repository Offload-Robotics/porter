# Porter Sim — Pygame Visual Proof of Concept
**Project:** porter-pygame-visual-poc  
**Company:** Offload Robotics  
**Product:** Porter — Autonomous Shopping Cart  
**Goal:** Purely visual 2D simulation. No data logging, no analytics, no plumbing. Goal is to produce a visually compelling screen capture for investor/customer demos within 1-2 days.

---

## What This Is
A top-down 2D Pygame simulation of a Sprouts-style grocery store (~15,000 sq ft) with 10-20 autonomous Porter carts moving around. This is a **visual prototype only** — no simulation logic needs to be accurate. It just needs to look believable and compelling on screen.

---

## Store Layout
Model a Sprouts Farmers Market style store — small/mid-size organic grocery, NOT a big box store.

- **Dimensions:** approximately 150 x 100 tiles (each tile = 1 ft), so ~150x100 ft floor plan
- **Sections to include (labeled):**
  - Produce (front-left)
  - Dairy (back-right wall)
  - Meat/Deli (back-left)
  - Bakery (front-right)
  - Bulk Foods (center)
  - Frozen Foods (back wall center)
  - Checkout lanes (front center, 4-6 lanes)
  - Cart charging queue (front-left corner near entrance)
  - Entrance/Exit (front center)
- **Aisles:** 6-8 parallel aisles running front-to-back with shelf blocks rendered as colored rectangles
- **Aisle labels:** render small text labels on each aisle (e.g. "Snacks", "Canned Goods", "Beverages", etc.)

---

## Cart Visuals
- Render 15 carts total
- Each cart = small rectangle or rounded rectangle with a colored indicator dot
- **Color coding by mode:**
  - 🔵 Blue = Autonomous nav (going to fetch/lead)
  - 🟢 Green = Follow mode (following a shopper)
  - 🟡 Yellow = Lead mode (leading a shopper to a product)
  - ⚪ Gray = Idle / in charging queue
- Carts should have a small directional arrow showing heading
- Optionally render a faint dotted trail behind each moving cart

---

## Shopper Visuals
- Render 10-15 shoppers as simple colored circles
- Shoppers wander semi-randomly between sections
- When a cart is in follow mode, draw a faint line connecting cart to its assigned shopper
- When a cart is in lead mode, draw a faint arrow from cart toward destination aisle

---

## Cart Behaviors (Visual Only — Fake It)
These don't need to be physically accurate. Just look believable:

1. **Autonomous Nav:** Cart moves along aisle paths toward a target section. Use simple waypoint movement — no real pathfinding required. Carts should avoid overlapping each other with basic separation logic.

2. **Follow Mode:** Cart trails 1-2 tiles behind an assigned shopper, mirroring their movement with slight lag.

3. **Lead Mode:** Cart moves ahead of shopper toward a target aisle, pausing occasionally as if waiting for shopper to catch up.

4. **Return to Charging:** When a shopper "exits" (reaches entrance/exit tile), cart switches to gray, navigates back to charging queue in front-left corner.

5. **V2X Coordination (visual):** When two carts approach the same aisle intersection, one briefly slows/pauses and the other passes. Render a brief cyan flash at the intersection point to suggest V2X communication.

---

## UI Overlay (Simple HUD)
Render a dark semi-transparent sidebar on the right (200px wide):

- **Title:** "Porter by Offload Robotics"
- **Live counters:**
  - Carts Active: N
  - Carts in Follow Mode: N
  - Carts in Lead Mode: N
  - Carts Charging: N
- **Mode legend** (color key)
- **Sim speed control:** +/- keys to speed up or slow down simulation

---

## Visual Polish
- Dark floor background (#1a1a2e or similar)
- Shelf blocks in muted colors per section (greens for produce, blues for frozen, etc.)
- Smooth cart movement (interpolated, not snapping tile-to-tile)
- Window title: "Porter Sim — Offload Robotics"
- Target FPS: 60

---

## Tech Stack
- Python 3.x
- Pygame (pip install pygame)
- No external dependencies beyond pygame
- Single file: `porter_sim.py`
- Run with: `python porter_sim.py`

---

## What Success Looks Like
A screen recording of this sim running for 60-90 seconds should be immediately understandable to a non-technical investor:
- They see carts moving purposefully through a store
- They see carts following shoppers
- They see carts leading shoppers to aisles
- They see carts returning to charge
- The color coding makes mode switching visually obvious

---

## Out of Scope (Do NOT implement)
- Data logging
- Analytics
- Pathfinding algorithms (A*, Dijkstra, etc.) — fake waypoints only
- Physics simulation
- Real V2X protocol
- Any file I/O
