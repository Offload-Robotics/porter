# Porter Sim — Pygame Full Execution Plan
**Project:** porter-pygame-full  
**Company:** Offload Robotics  
**Product:** Porter — Autonomous Shopping Cart  
**Goal:** Full simulation system with realistic shopper behavior, data collection, and a separate analytics dashboard. Target: investor-ready demo in 3 weeks.  
**Timeline:** 3 weeks  
**Developer:** Solo, using Claude CLI / Codex CLI

---

## Product Context
Porter is an autonomous robotic shopping cart built by Offload Robotics. It navigates a grocery store autonomously, follows shoppers, leads shoppers to products, coordinates with other carts via V2X/V2I, and returns itself to a charging queue when done. While operating, it passively collects behavioral and inventory data that feeds a store analytics engine.

This simulation uses **synthetic data** to prove the analytics architecture. All data is seeded with realistic priors (not purely random) to produce meaningful, non-trivial insights. This will be disclosed as synthetic to all audiences.

---

## System Architecture
Two decoupled components:

```
porter_sim/
├── sim/
│   ├── main.py              # Pygame sim entry point
│   ├── store.py             # Store layout, aisle graph, sections
│   ├── cart.py              # Cart agent: state machine, navigation
│   ├── shopper.py           # Shopper agent: behavior, product list
│   ├── scheduler.py         # Spawns shoppers, manages sim time
│   ├── v2x.py               # V2X/V2I coordination between carts
│   ├── data_logger.py       # Writes events to CSV/JSON
│   └── config.py            # All tunable parameters
├── analytics/
│   ├── dashboard.py         # Analytics dashboard entry point (separate window)
│   ├── ingestion.py         # Reads and aggregates logged data
│   ├── plots.py             # All matplotlib/seaborn chart generators
│   └── filters.py           # Time/day window filtering logic
├── data/
│   └── logs/                # Sim output logs land here
└── README.md
```

---

## Week 1: Sim Foundation

### Store Layout (`store.py`)
- Sprouts-style store, ~150x100 ft floor plan
- Tile-based grid (1 tile = 1 ft)
- Sections with defined bounding boxes:
  - Produce, Dairy, Meat/Deli, Bakery, Bulk, Frozen, Beverages, Snacks, Canned Goods, Personal Care
  - Checkout lanes (4-6), Charging queue (front-left), Entrance/Exit (front-center)
- Aisle graph: nodes at intersections, edges along walkable paths
- NavMesh equivalent: precomputed adjacency list for A* pathfinding
- Render: dark floor, colored shelf blocks per section, aisle labels

### Cart Agent (`cart.py`)
State machine with 5 states:
1. **IDLE** — in charging queue, awaiting assignment
2. **AUTONOMOUS_NAV** — navigating to a target section independently
3. **FOLLOW** — trailing assigned shopper with ~2 tile lag
4. **LEAD** — moving ahead of shopper toward target aisle, pausing to wait
5. **RETURN_TO_CHARGE** — shopper has exited, cart returns to charging queue

- Pathfinding: A* on aisle graph
- Collision avoidance: velocity obstacle or simple priority-based yielding
- V2X: broadcast position + intent to nearby carts, yield at intersections

### Shopper Agent (`shopper.py`)
- Spawned with a randomized shopping list (4-12 items)
- Items drawn from a weighted product catalog (realistic priors — see below)
- Behavior sequence:
  1. Enter store at entrance
  2. Request Porter cart → cart assigned from queue
  3. For each item: request lead to section → cart leads → shopper dwells → item collected
  4. Shopper browses additional items with probability p=0.3 (impulse buys)
  5. Shopper proceeds to checkout → pays → exits
  6. Cart returns to charging queue

### Realistic Priors (Critical for Non-Trivial Analytics)
Seed behavioral data with these priors from grocery research:
- **High traffic sections:** Produce (85% of shoppers visit), Dairy (78%), Beverages (65%)
- **Low traffic:** Bulk Foods (22%), Personal Care (31%)
- **Peak hours:** 11am-1pm (lunch), 5pm-7pm (after work) — simulate time-of-day variation
- **Dwell time by section:** Produce ~4min, Frozen ~2min, Bulk ~6min
- **Impulse buy probability:** highest near Bakery (p=0.45) and Checkout (p=0.35)
- **Cart abandonment:** ~15% of shoppers remove at least one item from cart

---

## Week 2: Data Collection + V2X

### Data Logger (`data_logger.py`)
Log every meaningful event to CSV with timestamp, sim_time, day_of_week, hour_of_day:

| Event Type | Fields |
|-----------|--------|
| `shopper_enter` | shopper_id, entry_time |
| `shopper_exit` | shopper_id, exit_time, total_items, total_value |
| `section_enter` | shopper_id, cart_id, section, timestamp |
| `section_exit` | shopper_id, cart_id, section, dwell_seconds |
| `item_added` | shopper_id, cart_id, product, category, price |
| `item_removed` | shopper_id, cart_id, product, category |
| `cart_mode_change` | cart_id, from_mode, to_mode, timestamp |
| `v2x_event` | cart_id_a, cart_id_b, intersection, resolution |
| `low_stock_signal` | section, product, estimated_remaining |
| `checkout_start` | shopper_id, cart_id, item_count, basket_value |

### V2X Coordination (`v2x.py`)
- Each cart broadcasts: position, heading, speed, state, intended path
- Within 5-tile radius: check for intersection conflicts
- Resolution: lower priority cart yields (priority = cart with longer path remaining)
- Log every V2X resolution event
- Visual: cyan flash at conflict point, brief slowdown animation

---

## Week 3: Analytics Dashboard

### Dashboard (`dashboard.py`)
Standalone Python window (matplotlib or Dash). Launched separately from sim:
```
python analytics/dashboard.py
```

### Data Ingestion (`ingestion.py`)
- Reads all CSVs from `data/logs/`
- Aggregates into pandas DataFrames
- Supports filtering by: time range, day of week, hour of day, section, cart ID

### Charts to Generate (`plots.py`)

1. **Store Heatmap** — overlay on store layout showing dwell time per section (color gradient)
2. **Traffic by Hour** — line chart, shopper count per hour of day
3. **Top Products Added** — bar chart, most frequently added items
4. **Cart Abandonment Rate** — by section and product category
5. **Basket Composition** — pie/donut chart, revenue by section
6. **V2X Event Frequency** — bar chart by intersection/aisle
7. **Cart Utilization** — % time each cart spent in each mode
8. **Impulse Buy Heatmap** — which sections generate most unplanned adds
9. **Low Stock Signals** — timeline of low_stock_signal events by section

### Time Window Filter (`filters.py`)
UI controls in dashboard:
- Date picker (simulated dates)
- Hour range slider (e.g. 9am-12pm)
- Day of week selector (Mon-Sun)
- Section multi-select filter
All charts re-render on filter change.

---

## Config (`config.py`)
All tunable parameters in one place:
```python
NUM_CARTS = 15
NUM_SHOPPERS_PER_HOUR = 20
STORE_WIDTH_TILES = 150
STORE_HEIGHT_TILES = 100
TILE_SIZE_PX = 8
SIM_SPEED_MULTIPLIER = 1.0
LOG_DIR = "data/logs/"
SIM_DAYS = 7          # How many simulated days to run
RANDOM_SEED = 42      # For reproducibility
```

---

## Visual Polish (Sim Window)
- Dark floor (#1a1a2e)
- Section colors: Produce=green, Frozen=blue, Dairy=cyan, Bakery=orange, Meat=red
- Cart color by mode: blue=autonomous, green=follow, yellow=lead, gray=idle
- Directional arrow on each cart
- Faint dotted trail (last 10 positions)
- Follow mode: faint line from cart to shopper
- Lead mode: faint arrow from cart toward destination
- HUD sidebar (200px right):
  - Live cart mode counters
  - Current sim time / day
  - Events per minute
  - Sim speed control (+/- keys)
  - P to pause, R to reset

---

## Tech Stack
```
Python 3.10+
pygame==2.5.x          # Sim rendering
pandas==2.x            # Data aggregation
matplotlib==3.x        # Charts
seaborn==0.x           # Heatmaps
dash==2.x              # Optional: browser-based dashboard alternative
numpy==1.x             # Math utilities
```
Install: `pip install pygame pandas matplotlib seaborn numpy`

---

## Running the System
```bash
# Run simulation (generates logs)
python sim/main.py

# Run analytics dashboard (reads logs)
python analytics/dashboard.py
```

---

## 3-Week Milestones

| Week | Deliverable |
|------|------------|
| Week 1 | Store renders, carts move, shoppers navigate, A* pathfinding works |
| Week 2 | All data logging, V2X coordination, full shopper lifecycle |
| Week 3 | Analytics dashboard with all 9 charts + time window filter |

---

## Course-Correction Rules (For CLI Agent)
When in doubt, refer back to this document. Key invariants:
- Store layout dimensions must not change mid-build (150x100 tiles)
- All behavioral priors must remain seeded as specified — do not randomize uniformly
- Data schema (event types + fields) is frozen after Week 1 — analytics depends on it
- Sim and analytics are always two separate processes — never merge them
- RANDOM_SEED = 42 always, for reproducibility
- If a feature isn't in this doc, do not add it without flagging it first

---

## Out of Scope
- Real hardware integration
- Real V2X protocol implementation
- Machine learning / model training
- Unity or 3D rendering
- Authentication or multi-user support
- Cloud deployment
