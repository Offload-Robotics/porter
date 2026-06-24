import math
import random
from dataclasses import dataclass, field

import pygame


STORE_W_TILES = 150
STORE_H_TILES = 100
TILE = 8
HUD_W = 240
WIDTH = STORE_W_TILES * TILE + HUD_W
HEIGHT = STORE_H_TILES * TILE
FPS = 60
RANDOM_SEED = 42

STORE_W = STORE_W_TILES * TILE
STORE_H = STORE_H_TILES * TILE

FLOOR = (26, 26, 46)
WALL = (52, 55, 76)
AISLE = (35, 36, 58)
GRID = (43, 45, 66)
TEXT = (235, 238, 245)
MUTED = (166, 174, 196)
CYAN = (67, 224, 240)

MODE_COLORS = {
    "nav": (70, 143, 255),
    "follow": (68, 211, 126),
    "lead": (248, 215, 82),
    "idle": (158, 164, 176),
    "return": (158, 164, 176),
}

SECTION_COLORS = {
    "Produce": (55, 139, 82),
    "Meat/Deli": (151, 63, 76),
    "Frozen Foods": (53, 105, 173),
    "Dairy": (76, 180, 194),
    "Bakery": (198, 132, 56),
    "Bulk Foods": (142, 112, 58),
    "Checkout": (101, 93, 139),
    "Charging": (78, 84, 99),
}


def clamp(value, low, high):
    return max(low, min(high, value))


def vec_from_angle(angle):
    return pygame.Vector2(math.cos(angle), math.sin(angle))


def move_toward(pos, target, speed):
    delta = target - pos
    dist = delta.length()
    if dist <= speed or dist == 0:
        return target.copy(), True
    return pos + delta.normalize() * speed, False


def draw_text(surface, font, text, pos, color=TEXT, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(image, rect)
    return rect


@dataclass
class Section:
    name: str
    rect: pygame.Rect
    color: tuple

    @property
    def center(self):
        return pygame.Vector2(self.rect.center)


@dataclass
class Shopper:
    idx: int
    pos: pygame.Vector2
    color: tuple
    waypoints: list
    waypoint_idx: int = 0
    speed: float = 55.0
    dwell: float = 0.0

    def update(self, dt):
        if self.dwell > 0:
            self.dwell -= dt
            return

        target = self.waypoints[self.waypoint_idx]
        self.pos, arrived = move_toward(self.pos, target, self.speed * dt)
        if arrived:
            self.waypoint_idx = (self.waypoint_idx + 1) % len(self.waypoints)
            self.dwell = random.uniform(0.5, 2.4)


@dataclass
class Cart:
    idx: int
    pos: pygame.Vector2
    mode: str
    route: list
    shopper: Shopper | None = None
    target: pygame.Vector2 | None = None
    route_idx: int = 0
    heading: float = 0.0
    pause: float = 0.0
    speed: float = 72.0
    trail: list = field(default_factory=list)

    def current_color(self):
        return MODE_COLORS[self.mode]

    def set_route(self, route):
        self.route = [p.copy() for p in route]
        self.route_idx = 0

    def route_target(self):
        if not self.route:
            return self.pos
        return self.route[self.route_idx]

    def update(self, dt, carts, store_points):
        if self.pause > 0:
            self.pause -= dt
            return

        previous = self.pos.copy()

        if self.mode == "follow" and self.shopper:
            offset = vec_from_angle(self.heading + math.pi) * 18
            target = self.shopper.pos + offset
            self._move_to(target, dt, carts, speed_scale=0.88)
        elif self.mode == "lead" and self.shopper:
            lead_target = self.target or self.route_target()
            shopper_dist = self.pos.distance_to(self.shopper.pos)
            if shopper_dist > 88 and random.random() < 0.025:
                self.pause = random.uniform(0.4, 1.1)
            else:
                self._move_route(dt, carts, speed_scale=0.82)
                if self.pos.distance_to(lead_target) < 24:
                    self.target = random.choice(store_points)
                    self.set_route(make_route(self.pos, self.target))
        elif self.mode == "idle":
            self.pause = random.uniform(0.2, 1.2)
        else:
            self._move_route(dt, carts, speed_scale=1.0)
            if self.mode == "return" and self.route_idx == len(self.route) - 1:
                if self.pos.distance_to(self.route_target()) < 4:
                    self.mode = "idle"

        moved = self.pos - previous
        if moved.length_squared() > 0.05:
            self.heading = math.atan2(moved.y, moved.x)
            self.trail.append(self.pos.copy())
            if len(self.trail) > 24:
                self.trail.pop(0)

    def _move_route(self, dt, carts, speed_scale=1.0):
        if not self.route:
            return
        target = self.route[self.route_idx]
        arrived = self._move_to(target, dt, carts, speed_scale=speed_scale)
        if arrived:
            self.route_idx = (self.route_idx + 1) % len(self.route)

    def _move_to(self, target, dt, carts, speed_scale=1.0):
        separation = pygame.Vector2()
        for other in carts:
            if other is self:
                continue
            distance = self.pos.distance_to(other.pos)
            if 0 < distance < 22:
                separation += (self.pos - other.pos).normalize() * (22 - distance)

        desired = pygame.Vector2(target)
        if separation.length_squared() > 0:
            desired += separation * 0.8

        self.pos, arrived = move_toward(self.pos, desired, self.speed * speed_scale * dt)
        self.pos.x = clamp(self.pos.x, 20, STORE_W - 20)
        self.pos.y = clamp(self.pos.y, 20, STORE_H - 20)
        return arrived


def tile_rect(x, y, w, h):
    return pygame.Rect(x * TILE, y * TILE, w * TILE, h * TILE)


def make_route(start, dest):
    start = pygame.Vector2(start)
    dest = pygame.Vector2(dest)
    mid_y = random.choice([22, 38, 56, 74]) * TILE
    mid_x = random.choice([28, 48, 68, 88, 108, 128]) * TILE
    return [
        pygame.Vector2(start.x, mid_y),
        pygame.Vector2(mid_x, mid_y),
        pygame.Vector2(mid_x, dest.y),
        dest.copy(),
    ]


def build_sections():
    return [
        Section("Produce", tile_rect(7, 61, 35, 27), SECTION_COLORS["Produce"]),
        Section("Meat/Deli", tile_rect(6, 7, 35, 18), SECTION_COLORS["Meat/Deli"]),
        Section("Frozen Foods", tile_rect(52, 6, 45, 12), SECTION_COLORS["Frozen Foods"]),
        Section("Dairy", tile_rect(105, 7, 36, 18), SECTION_COLORS["Dairy"]),
        Section("Bakery", tile_rect(108, 64, 32, 24), SECTION_COLORS["Bakery"]),
        Section("Bulk Foods", tile_rect(58, 43, 36, 18), SECTION_COLORS["Bulk Foods"]),
        Section("Checkout", tile_rect(54, 82, 42, 12), SECTION_COLORS["Checkout"]),
        Section("Charging", tile_rect(8, 88, 26, 8), SECTION_COLORS["Charging"]),
    ]


def build_aisles():
    aisles = []
    labels = ["Snacks", "Canned Goods", "Beverages", "Pantry", "Personal Care", "Household", "Organic", "Coffee"]
    x_positions = [47, 58, 69, 80, 91, 102, 113, 124]
    for i, x in enumerate(x_positions):
        aisles.append((tile_rect(x, 25, 6, 44), labels[i]))
    return aisles


def shopper_route(sections):
    entrance = pygame.Vector2(75 * TILE, 96 * TILE)
    weighted = [
        ("Produce", 5),
        ("Dairy", 5),
        ("Bakery", 3),
        ("Frozen Foods", 3),
        ("Bulk Foods", 2),
        ("Meat/Deli", 3),
    ]
    by_name = {s.name: s.center for s in sections}
    route = [entrance.copy()]
    for _ in range(random.randint(4, 7)):
        name = random.choice([name for name, weight in weighted for _ in range(weight)])
        point = by_name[name] + pygame.Vector2(random.uniform(-40, 40), random.uniform(-25, 25))
        route.append(point)
    route.append(pygame.Vector2(random.uniform(55, 95) * TILE, 86 * TILE))
    route.append(entrance.copy())
    return route


def draw_arrow(surface, start, end, color, width=2):
    start = pygame.Vector2(start)
    end = pygame.Vector2(end)
    delta = end - start
    if delta.length_squared() < 1:
        return
    direction = delta.normalize()
    tip = end
    left = tip - direction * 10 + direction.rotate(135) * 7
    right = tip - direction * 10 + direction.rotate(-135) * 7
    pygame.draw.line(surface, color, start, tip, width)
    pygame.draw.polygon(surface, color, [tip, left, right])


def draw_store(surface, fonts, sections, aisles):
    surface.fill(FLOOR, pygame.Rect(0, 0, STORE_W, STORE_H))
    for x in range(0, STORE_W, TILE * 10):
        pygame.draw.line(surface, GRID, (x, 0), (x, STORE_H), 1)
    for y in range(0, STORE_H, TILE * 10):
        pygame.draw.line(surface, GRID, (0, y), (STORE_W, y), 1)

    pygame.draw.rect(surface, WALL, pygame.Rect(0, 0, STORE_W, STORE_H), 7)
    entrance = pygame.Rect(62 * TILE, 95 * TILE, 26 * TILE, 5 * TILE)
    pygame.draw.rect(surface, (78, 96, 128), entrance, border_radius=4)
    draw_text(surface, fonts["small"], "Entrance / Exit", entrance.midtop + pygame.Vector2(0, -18), MUTED, center=True)

    for section in sections:
        pygame.draw.rect(surface, section.color, section.rect, border_radius=6)
        pygame.draw.rect(surface, (235, 238, 245, 40), section.rect, 2, border_radius=6)
        draw_text(surface, fonts["label"], section.name, section.rect.center, TEXT, center=True)

    for rect, label in aisles:
        pygame.draw.rect(surface, (74, 77, 105), rect, border_radius=4)
        pygame.draw.rect(surface, (95, 99, 132), rect.inflate(-12, -8), border_radius=3)
        label_surface = fonts["small"].render(label, True, (220, 224, 235))
        rotated = pygame.transform.rotate(label_surface, 90)
        surface.blit(rotated, rotated.get_rect(center=rect.center))

    for x in [43, 54, 65, 76, 87, 98, 109, 120, 131]:
        pygame.draw.line(surface, AISLE, (x * TILE, 22 * TILE), (x * TILE, 78 * TILE), 3)
    for y in [22, 38, 56, 74, 86]:
        pygame.draw.line(surface, AISLE, (38 * TILE, y * TILE), (137 * TILE, y * TILE), 3)

    for i in range(6):
        lane = tile_rect(56 + i * 7, 84, 4, 10)
        pygame.draw.rect(surface, (70, 68, 103), lane, border_radius=3)
        draw_text(surface, fonts["tiny"], str(i + 1), lane.center, TEXT, center=True)

    charge = pygame.Rect(10 * TILE, 90 * TILE, 20 * TILE, 4 * TILE)
    for i in range(5):
        slot = pygame.Rect(charge.x + i * 30, charge.y, 22, 22)
        pygame.draw.rect(surface, (103, 109, 128), slot, 1, border_radius=4)


def draw_shoppers(surface, shoppers):
    for shopper in shoppers:
        pygame.draw.circle(surface, (8, 10, 18), shopper.pos, 8)
        pygame.draw.circle(surface, shopper.color, shopper.pos, 6)
        pygame.draw.circle(surface, (245, 247, 252), shopper.pos + pygame.Vector2(2, -2), 2)


def draw_cart(surface, cart):
    for i, point in enumerate(cart.trail[::2]):
        alpha_color = tuple(max(0, c - 35) for c in cart.current_color())
        pygame.draw.circle(surface, alpha_color, point, max(1, i // 3 + 1))

    if cart.mode == "follow" and cart.shopper:
        pygame.draw.line(surface, (83, 224, 145), cart.pos, cart.shopper.pos, 1)
    if cart.mode == "lead" and cart.target:
        end = cart.pos + (cart.target - cart.pos).normalize() * 34 if cart.pos.distance_to(cart.target) > 1 else cart.pos
        draw_arrow(surface, cart.pos, end, (245, 218, 86), width=1)

    body = pygame.Rect(0, 0, 18, 12)
    body.center = cart.pos
    pygame.draw.rect(surface, (9, 12, 24), body.inflate(4, 4), border_radius=4)
    pygame.draw.rect(surface, cart.current_color(), body, border_radius=4)
    pygame.draw.circle(surface, (246, 248, 252), cart.pos + pygame.Vector2(5, -3), 3)
    direction = vec_from_angle(cart.heading)
    draw_arrow(surface, cart.pos, cart.pos + direction * 18, (246, 248, 252), width=2)


def draw_hud(surface, fonts, carts, speed, paused):
    hud = pygame.Rect(STORE_W, 0, HUD_W, HEIGHT)
    overlay = pygame.Surface((HUD_W, HEIGHT), pygame.SRCALPHA)
    overlay.fill((12, 14, 26, 232))
    surface.blit(overlay, hud.topleft)

    x = STORE_W + 18
    y = 22
    draw_text(surface, fonts["title"], "Porter", (x, y), TEXT)
    y += 28
    draw_text(surface, fonts["small"], "by Offload Robotics", (x, y), MUTED)
    y += 42

    counts = {
        "Active": sum(1 for c in carts if c.mode != "idle"),
        "Follow Mode": sum(1 for c in carts if c.mode == "follow"),
        "Lead Mode": sum(1 for c in carts if c.mode == "lead"),
        "Charging": sum(1 for c in carts if c.mode == "idle"),
    }
    for label, value in counts.items():
        draw_text(surface, fonts["body"], f"{label}: {value}", (x, y), TEXT)
        y += 28

    y += 20
    draw_text(surface, fonts["body"], "Mode Legend", (x, y), TEXT)
    y += 30
    legend = [("nav", "Autonomous nav"), ("follow", "Follow shopper"), ("lead", "Lead to product"), ("idle", "Idle / charging")]
    for mode, label in legend:
        pygame.draw.circle(surface, MODE_COLORS[mode], (x + 8, y + 8), 7)
        draw_text(surface, fonts["small"], label, (x + 24, y), MUTED)
        y += 24

    y += 24
    draw_text(surface, fonts["body"], f"Sim speed: {speed:.1f}x", (x, y), TEXT)
    y += 24
    draw_text(surface, fonts["small"], "+ / - adjust speed", (x, y), MUTED)
    y += 20
    draw_text(surface, fonts["small"], "P pause    R reset", (x, y), MUTED)
    y += 30
    draw_text(surface, fonts["body"], "Status", (x, y), TEXT)
    y += 24
    draw_text(surface, fonts["small"], "Paused" if paused else "Running", (x, y), (248, 215, 82) if paused else (68, 211, 126))


def spawn_world():
    random.seed(RANDOM_SEED)
    sections = build_sections()
    aisles = build_aisles()
    points = []
    for section in sections:
        if section.name not in {"Charging", "Checkout"}:
            points.append(section.center)
    points.extend(
        pygame.Vector2(x * TILE, y * TILE)
        for x in [43, 54, 65, 76, 87, 98, 109, 120, 131]
        for y in [22, 38, 56, 74]
    )

    shoppers = []
    for i in range(13):
        route = shopper_route(sections)
        shoppers.append(
            Shopper(
                idx=i,
                pos=route[0] + pygame.Vector2(random.uniform(-40, 40), random.uniform(-10, 18)),
                color=random.choice([(239, 112, 112), (118, 202, 255), (245, 173, 83), (196, 136, 255), (104, 221, 183)]),
                waypoints=route,
                speed=random.uniform(35, 58),
            )
        )

    carts = []
    charge_start = pygame.Vector2(13 * TILE, 91 * TILE)
    modes = ["follow"] * 5 + ["lead"] * 4 + ["nav"] * 4 + ["idle"] * 2
    random.shuffle(modes)
    for i in range(15):
        pos = charge_start + pygame.Vector2((i % 5) * 34, (i // 5) * 20)
        mode = modes[i]
        shopper = random.choice(shoppers) if mode in {"follow", "lead"} else None
        target = random.choice(points)
        route = make_route(pos, target)
        if mode == "idle":
            route = [pos.copy()]
        carts.append(
            Cart(
                idx=i,
                pos=pos,
                mode=mode,
                route=route,
                shopper=shopper,
                target=target,
                speed=random.uniform(62, 86),
                heading=random.uniform(-math.pi, math.pi),
            )
        )

    return sections, aisles, points, shoppers, carts


def update_cart_modes(carts, shoppers, points):
    for cart in carts:
        if cart.mode == "idle" and random.random() < 0.002:
            cart.mode = random.choice(["nav", "follow", "lead"])
            cart.shopper = random.choice(shoppers) if cart.mode in {"follow", "lead"} else None
            cart.target = random.choice(points)
            cart.set_route(make_route(cart.pos, cart.target))
        elif cart.mode in {"follow", "lead"} and random.random() < 0.0015:
            cart.mode = "return"
            cart.shopper = None
            cart.target = pygame.Vector2(random.uniform(12, 31) * TILE, random.uniform(89, 94) * TILE)
            cart.set_route(make_route(cart.pos, cart.target))
        elif cart.mode == "nav" and random.random() < 0.0018:
            cart.mode = random.choice(["follow", "lead"])
            cart.shopper = random.choice(shoppers)
            cart.target = random.choice(points)
            cart.set_route(make_route(cart.pos, cart.target))


def detect_v2x(carts, flashes):
    active = [c for c in carts if c.mode != "idle"]
    for i, a in enumerate(active):
        for b in active[i + 1 :]:
            if a.pos.distance_to(b.pos) < 30 and random.random() < 0.055:
                loser = a if a.idx > b.idx else b
                loser.pause = random.uniform(0.18, 0.45)
                flashes.append([((a.pos + b.pos) / 2), 0.45])


def draw_flashes(surface, flashes):
    for flash in flashes:
        point, ttl = flash
        radius = int(8 + (0.45 - ttl) * 42)
        alpha = int(clamp(ttl / 0.45, 0, 1) * 180)
        pulse = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(pulse, (*CYAN, alpha), (radius + 2, radius + 2), radius, 2)
        pygame.draw.circle(pulse, (*CYAN, alpha), (radius + 2, radius + 2), 4)
        surface.blit(pulse, pulse.get_rect(center=point))


def main():
    pygame.init()
    pygame.display.set_caption("Porter Sim - Offload Robotics")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.SysFont("arial", 28, bold=True),
        "body": pygame.font.SysFont("arial", 18, bold=True),
        "label": pygame.font.SysFont("arial", 15, bold=True),
        "small": pygame.font.SysFont("arial", 14),
        "tiny": pygame.font.SysFont("arial", 11, bold=True),
    }

    sections, aisles, points, shoppers, carts = spawn_world()
    flashes = []
    sim_speed = 1.0
    paused = False
    running = True

    while running:
        raw_dt = clock.tick(FPS) / 1000.0
        dt = 0 if paused else raw_dt * sim_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    sim_speed = clamp(sim_speed + 0.25, 0.25, 4.0)
                elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                    sim_speed = clamp(sim_speed - 0.25, 0.25, 4.0)
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_r:
                    sections, aisles, points, shoppers, carts = spawn_world()
                    flashes = []

        if dt > 0:
            for shopper in shoppers:
                shopper.update(dt)
            update_cart_modes(carts, shoppers, points)
            for cart in carts:
                cart.update(dt, carts, points)
            detect_v2x(carts, flashes)
            for flash in flashes:
                flash[1] -= dt
            flashes = [flash for flash in flashes if flash[1] > 0]

        draw_store(screen, fonts, sections, aisles)
        draw_flashes(screen, flashes)
        draw_shoppers(screen, shoppers)
        for cart in carts:
            draw_cart(screen, cart)
        draw_hud(screen, fonts, carts, sim_speed, paused)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
