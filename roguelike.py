import pygame
import random
import sys
from collections import deque

pygame.init()

TILE = 32
MAP_W = 20
MAP_H = 15
PANEL_W = 220
WIN_W = MAP_W * TILE + PANEL_W
WIN_H = MAP_H * TILE
FPS = 60
FOV_RADIUS = 5

WALL = 0
FLOOR = 1
STAIRS = 2

COLOR_BG = (20, 20, 30)
COLOR_WALL = (60, 60, 80)
COLOR_FLOOR = (40, 40, 50)
COLOR_WALL_DIM = (35, 35, 45)
COLOR_FLOOR_DIM = (25, 25, 32)
COLOR_STAIRS = (180, 160, 60)
COLOR_STAIRS_DIM = (90, 80, 30)
COLOR_PLAYER = (70, 130, 230)
COLOR_SLIME = (50, 200, 80)
COLOR_SKELETON = (210, 210, 210)
COLOR_BAT = (170, 60, 200)
COLOR_POTION = (220, 50, 50)
COLOR_WEAPON = (230, 200, 50)
COLOR_TRAP = (180, 80, 180)
COLOR_PANEL_BG = (25, 25, 35)
COLOR_TEXT = (220, 220, 220)
COLOR_HP_BAR_BG = (80, 20, 20)
COLOR_HP_BAR = (200, 50, 50)
COLOR_MSG = (180, 180, 180)


def dim_color(color):
    return (int(color[0] * 0.45), int(color[1] * 0.45), int(color[2] * 0.45))


class TileMap:
    def __init__(self):
        self.tiles = [[WALL] * MAP_W for _ in range(MAP_H)]
        self.visible = [[False] * MAP_W for _ in range(MAP_H)]
        self.explored = [[False] * MAP_W for _ in range(MAP_H)]
        self.rooms = []

    def generate(self):
        self.tiles = [[WALL] * MAP_W for _ in range(MAP_H)]
        self.visible = [[False] * MAP_W for _ in range(MAP_H)]
        self.explored = [[False] * MAP_W for _ in range(MAP_H)]
        self.rooms = []
        num_rooms = random.randint(4, 7)
        for _ in range(num_rooms * 10):
            if len(self.rooms) >= num_rooms:
                break
            rw = random.randint(3, 6)
            rh = random.randint(3, 5)
            rx = random.randint(1, MAP_W - rw - 1)
            ry = random.randint(1, MAP_H - rh - 1)
            new_room = pygame.Rect(rx, ry, rw, rh)
            overlap = False
            for r in self.rooms:
                if new_room.inflate(2, 2).colliderect(r):
                    overlap = True
                    break
            if overlap:
                continue
            self._carve_room(new_room)
            if self.rooms:
                prev = self.rooms[-1]
                self._carve_corridor(prev.centerx, prev.centery, new_room.centerx, new_room.centery)
            self.rooms.append(new_room)

    def _carve_room(self, room):
        for y in range(room.top, room.bottom):
            for x in range(room.left, room.right):
                self.tiles[y][x] = FLOOR

    def _carve_corridor(self, x1, y1, x2, y2):
        cx, cy = x1, y1
        while cx != x2:
            self.tiles[cy][cx] = FLOOR
            cx += 1 if x2 > cx else -1
        while cy != y2:
            self.tiles[cy][cx] = FLOOR
            cy += 1 if y2 > cy else -1
        self.tiles[cy][cx] = FLOOR

    def is_floor(self, x, y):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            return self.tiles[y][x] != WALL
        return False

    def place_stairs(self):
        if len(self.rooms) < 2:
            room = random.choice(self.rooms)
        else:
            room = self.rooms[-1]
        sx = random.randint(room.left, room.right - 1)
        sy = random.randint(room.top, room.bottom - 1)
        self.tiles[sy][sx] = STAIRS
        return sx, sy

    def get_spawn_pos(self, room_index=0):
        room = self.rooms[room_index]
        attempts = 0
        while attempts < 100:
            x = random.randint(room.left, room.right - 1)
            y = random.randint(room.top, room.bottom - 1)
            if self.tiles[y][x] == FLOOR:
                return x, y
            attempts += 1
        return room.centerx, room.centery

    def get_random_floor(self, occupied):
        attempts = 0
        while attempts < 200:
            x = random.randint(0, MAP_W - 1)
            y = random.randint(0, MAP_H - 1)
            if self.tiles[y][x] == FLOOR and (x, y) not in occupied:
                return x, y
            attempts += 1
        return None

    def is_visible(self, x, y):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            return self.visible[y][x]
        return False

    def is_explored(self, x, y):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            return self.explored[y][x]
        return False

    def compute_fov(self, px, py):
        for y in range(MAP_H):
            for x in range(MAP_W):
                self.visible[y][x] = False
        self.visible[py][px] = True
        self.explored[py][px] = True
        for dy in range(-FOV_RADIUS, FOV_RADIUS + 1):
            for dx in range(-FOV_RADIUS, FOV_RADIUS + 1):
                if dx * dx + dy * dy > FOV_RADIUS * FOV_RADIUS:
                    continue
                self._cast_line(px, py, px + dx, py + dy)

    def _cast_line(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx, cy = x0, y0
        while True:
            if 0 <= cx < MAP_W and 0 <= cy < MAP_H:
                self.visible[cy][cx] = True
                self.explored[cy][cx] = True
                if self.tiles[cy][cx] == WALL:
                    return
                if cx == x1 and cy == y1:
                    return
            else:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy


class Trap:
    def __init__(self, x, y, damage=0):
        self.x = x
        self.y = y
        self.damage = damage if damage > 0 else random.randint(3, 8)
        self.revealed = False
        self.triggered = False


class Entity:
    def __init__(self, x, y, name, color, hp, atk, defense, speed=1):
        self.x = x
        self.y = y
        self.name = name
        self.color = color
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.speed = speed
        self.alive = True

    def take_damage(self, dmg):
        actual = max(1, dmg - self.defense)
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, "Player", COLOR_PLAYER, 30, 5, 2, 1)
        self.kills = 0
        self.floor_reached = 1
        self.pickup_log = []

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)


class Monster(Entity):
    def __init__(self, x, y, name, color, hp, atk, defense, speed=1):
        super().__init__(x, y, name, color, hp, atk, defense, speed)


def create_monster(x, y, floor_num):
    roll = random.random()
    scale = 1 + (floor_num - 1) * 0.2
    if roll < 0.4:
        return Monster(x, y, "Slime", COLOR_SLIME, int(12 * scale), int(2 * scale), int(1 * scale), 1)
    elif roll < 0.75:
        return Monster(x, y, "Skeleton", COLOR_SKELETON, int(6 * scale), int(5 * scale), int(1 * scale), 1)
    else:
        return Monster(x, y, "Bat", COLOR_BAT, int(4 * scale), int(3 * scale), 0, 2)


class Item:
    def __init__(self, x, y, kind, value, name, color):
        self.x = x
        self.y = y
        self.kind = kind
        self.value = value
        self.name = name
        self.color = color


def create_item(x, y, floor_num):
    if random.random() < 0.6:
        heal = random.randint(8, 15)
        return Item(x, y, "potion", heal, f"Heal+{heal}", COLOR_POTION)
    else:
        bonus = random.randint(1, 2 + floor_num // 3)
        return Item(x, y, "weapon", bonus, f"ATK+{bonus}", COLOR_WEAPON)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Roguelike Dungeon")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_large = pygame.font.SysFont("consolas", 22)
        self.font_title = pygame.font.SysFont("consolas", 28, bold=True)
        self.tilemap = TileMap()
        self.player = None
        self.monsters = []
        self.items = []
        self.traps = []
        self.messages = []
        self.current_floor = 1
        self.state = "play"
        self.stair_pos = None
        self._generate_floor()

    def _generate_floor(self):
        self.tilemap.generate()
        self.monsters.clear()
        self.items.clear()
        self.traps.clear()
        start_room = 0
        px, py = self.tilemap.get_spawn_pos(start_room)
        if self.player is None:
            self.player = Player(px, py)
        else:
            self.player.x = px
            self.player.y = py
        self.stair_pos = self.tilemap.place_stairs()
        occupied = {(px, py), self.stair_pos}
        num_monsters = 2 + self.current_floor
        for _ in range(num_monsters):
            pos = self.tilemap.get_random_floor(occupied)
            if pos:
                m = create_monster(pos[0], pos[1], self.current_floor)
                self.monsters.append(m)
                occupied.add(pos)
        num_items = random.randint(2, 4 + self.current_floor // 2)
        for _ in range(num_items):
            pos = self.tilemap.get_random_floor(occupied)
            if pos:
                it = create_item(pos[0], pos[1], self.current_floor)
                self.items.append(it)
                occupied.add(pos)
        num_traps = 3 + self.current_floor
        for _ in range(num_traps):
            pos = self.tilemap.get_random_floor(occupied)
            if pos:
                t = Trap(pos[0], pos[1])
                self.traps.append(t)
                occupied.add(pos)
        self.tilemap.compute_fov(px, py)
        self._update_trap_reveal()
        self.add_msg(f"Floor {self.current_floor}")

    def add_msg(self, text):
        self.messages.append(text)
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    def _update_trap_reveal(self):
        for trap in self.traps:
            if not trap.revealed and self.tilemap.is_visible(trap.x, trap.y):
                trap.revealed = True

    def _check_trap(self, x, y):
        for trap in self.traps[:]:
            if trap.x == x and trap.y == y and not trap.triggered:
                trap.triggered = True
                dmg = trap.damage
                actual = max(1, dmg - self.player.defense)
                self.player.hp -= actual
                trap.revealed = True
                self.add_msg(f"Triggered a trap! -{actual} HP")
                if self.player.hp <= 0:
                    self.player.hp = 0
                    self.player.alive = False
                    self.state = "dead"
                self.traps.remove(trap)
                return True
        return False

    def try_move(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if not self.tilemap.is_floor(nx, ny):
            return
        blocker = self._monster_at(nx, ny)
        if blocker:
            self._player_attack(blocker)
            self.tilemap.compute_fov(self.player.x, self.player.y)
            self._update_trap_reveal()
            self._monster_turn()
            return
        self.player.x = nx
        self.player.y = ny
        self.tilemap.compute_fov(self.player.x, self.player.y)
        self._update_trap_reveal()
        self._check_trap(nx, ny)
        if self.state != "play":
            return
        self._check_pickup()
        self._check_stairs()
        self._monster_turn()

    def _check_stairs(self):
        if self.tilemap.tiles[self.player.y][self.player.x] == STAIRS:
            self.current_floor += 1
            self.player.floor_reached = self.current_floor
            self._generate_floor()

    def _check_pickup(self):
        for item in self.items[:]:
            if item.x == self.player.x and item.y == self.player.y:
                if item.kind == "potion":
                    old = self.player.hp
                    self.player.heal(item.value)
                    gained = self.player.hp - old
                    self.add_msg(f"Picked up {item.name}! +{gained}HP")
                elif item.kind == "weapon":
                    self.player.atk += item.value
                    self.add_msg(f"Picked up {item.name}!")
                self.player.pickup_log.append(item.name)
                if len(self.player.pickup_log) > 5:
                    self.player.pickup_log = self.player.pickup_log[-5:]
                self.items.remove(item)

    def _player_attack(self, target):
        dmg = self.player.atk
        actual = target.take_damage(dmg)
        self.add_msg(f"You hit {target.name} for {actual} dmg!")
        if not target.alive:
            self.monsters.remove(target)
            self.player.kills += 1
            self.add_msg(f"{target.name} defeated!")

    def try_attack(self):
        for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.player.x + dx, self.player.y + dy
            m = self._monster_at(nx, ny)
            if m:
                self._player_attack(m)
                self.tilemap.compute_fov(self.player.x, self.player.y)
                self._update_trap_reveal()
                self._monster_turn()
                return

    def _monster_at(self, x, y):
        for m in self.monsters:
            if m.alive and m.x == x and m.y == y:
                return m
        return None

    def _monster_turn(self):
        for m in self.monsters:
            if not m.alive:
                continue
            steps = m.speed
            for _ in range(steps):
                if not m.alive:
                    break
                self._monster_act(m)

    def _monster_act(self, m):
        if abs(m.x - self.player.x) + abs(m.y - self.player.y) == 1:
            dmg = m.atk
            actual = self.player.take_damage(dmg)
            self.add_msg(f"{m.name} hits you for {actual} dmg!")
            if not self.player.alive:
                self.state = "dead"
            return
        path = self._find_path(m, self.player)
        if path and len(path) > 1:
            nx, ny = path[1]
            if not self._monster_at(nx, ny) and self.tilemap.is_floor(nx, ny):
                m.x = nx
                m.y = ny

    def _find_path(self, start, target):
        sx, sy = start.x, start.y
        tx, ty = target.x, target.y
        if sx == tx and sy == ty:
            return [(sx, sy)]
        visited = {(sx, sy)}
        queue = deque()
        queue.append(((sx, sy), [(sx, sy)]))
        while queue:
            (cx, cy), path = queue.popleft()
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                if not self.tilemap.is_floor(nx, ny):
                    continue
                if self._monster_at(nx, ny):
                    continue
                new_path = path + [(nx, ny)]
                if nx == tx and ny == ty:
                    return new_path
                visited.add((nx, ny))
                if len(new_path) < 15:
                    queue.append(((nx, ny), new_path))
        return None

    def draw(self):
        self.screen.fill(COLOR_BG)
        for y in range(MAP_H):
            for x in range(MAP_W):
                rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                t = self.tilemap.tiles[y][x]
                visible = self.tilemap.is_visible(x, y)
                explored = self.tilemap.is_explored(x, y)
                if not explored:
                    pygame.draw.rect(self.screen, COLOR_BG, rect)
                    continue
                if visible:
                    wall_c, floor_c = COLOR_WALL, COLOR_FLOOR
                    wall_b, floor_b = (50, 50, 70), (35, 35, 45)
                    stairs_c = COLOR_STAIRS
                else:
                    wall_c, floor_c = COLOR_WALL_DIM, COLOR_FLOOR_DIM
                    wall_b, floor_b = (25, 25, 35), (20, 20, 28)
                    stairs_c = COLOR_STAIRS_DIM
                if t == WALL:
                    pygame.draw.rect(self.screen, wall_c, rect)
                    pygame.draw.rect(self.screen, wall_b, rect, 1)
                elif t == FLOOR:
                    pygame.draw.rect(self.screen, floor_c, rect)
                    pygame.draw.rect(self.screen, floor_b, rect, 1)
                elif t == STAIRS:
                    pygame.draw.rect(self.screen, floor_c, rect)
                    inner = rect.inflate(-8, -8)
                    pygame.draw.rect(self.screen, stairs_c, inner)
                    if visible:
                        pygame.draw.polygon(self.screen, (220, 200, 80),
                                            [inner.midtop, inner.midright, inner.midbottom])
        for trap in self.traps:
            if trap.revealed and (self.tilemap.is_visible(trap.x, trap.y) or self.tilemap.is_explored(trap.x, trap.y)):
                rect = pygame.Rect(trap.x * TILE + 4, trap.y * TILE + 4, TILE - 8, TILE - 8)
                c = COLOR_TRAP if self.tilemap.is_visible(trap.x, trap.y) else dim_color(COLOR_TRAP)
                pygame.draw.circle(self.screen, c, rect.center, TILE // 2 - 6)
                pygame.draw.rect(self.screen, (60, 20, 60), rect, 1, border_radius=4)
                cx, cy = rect.center
                pygame.draw.line(self.screen, (255, 220, 100),
                                 (cx - 6, cy - 6), (cx + 6, cy + 6), 2)
                pygame.draw.line(self.screen, (255, 220, 100),
                                 (cx + 6, cy - 6), (cx - 6, cy + 6), 2)
        for item in self.items:
            if not self.tilemap.is_visible(item.x, item.y):
                continue
            rect = pygame.Rect(item.x * TILE + 6, item.y * TILE + 6, TILE - 12, TILE - 12)
            if item.kind == "potion":
                pygame.draw.ellipse(self.screen, item.color, rect)
                pygame.draw.rect(self.screen, (180, 180, 180),
                                 (rect.centerx - 2, rect.top - 4, 4, 6))
            else:
                pygame.draw.polygon(self.screen, item.color,
                                    [rect.midtop, rect.bottomright, rect.bottomleft])
        for m in self.monsters:
            if not self.tilemap.is_visible(m.x, m.y):
                continue
            rect = pygame.Rect(m.x * TILE + 2, m.y * TILE + 2, TILE - 4, TILE - 4)
            pygame.draw.rect(self.screen, m.color, rect, border_radius=4)
            eye_y = rect.y + 10
            pygame.draw.circle(self.screen, (0, 0, 0), (rect.x + 9, eye_y), 3)
            pygame.draw.circle(self.screen, (0, 0, 0), (rect.x + TILE - 13, eye_y), 3)
            pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + 9, eye_y), 1)
            pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + TILE - 13, eye_y), 1)
        px, py = self.player.x, self.player.y
        rect = pygame.Rect(px * TILE + 2, py * TILE + 2, TILE - 4, TILE - 4)
        pygame.draw.rect(self.screen, COLOR_PLAYER, rect, border_radius=6)
        eye_y = rect.y + 11
        pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + 9, eye_y), 4)
        pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + TILE - 13, eye_y), 4)
        pygame.draw.circle(self.screen, (30, 30, 30), (rect.x + 9, eye_y), 2)
        pygame.draw.circle(self.screen, (30, 30, 30), (rect.x + TILE - 13, eye_y), 2)
        self._draw_panel()
        if self.state == "dead":
            self._draw_death_screen()
        pygame.display.flip()

    def _draw_panel(self):
        panel_x = MAP_W * TILE
        panel_rect = pygame.Rect(panel_x, 0, PANEL_W, WIN_H)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, (60, 60, 80), (panel_x, 0), (panel_x, WIN_H), 2)
        y = 12
        title = self.font_large.render("STATUS", True, COLOR_TEXT)
        self.screen.blit(title, (panel_x + 10, y))
        y += 35
        floor_text = self.font.render(f"Floor: {self.current_floor}", True, COLOR_STAIRS)
        self.screen.blit(floor_text, (panel_x + 10, y))
        y += 25
        hp_label = self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, COLOR_TEXT)
        self.screen.blit(hp_label, (panel_x + 10, y))
        y += 20
        bar_w = PANEL_W - 30
        bar_h = 14
        pygame.draw.rect(self.screen, COLOR_HP_BAR_BG, (panel_x + 10, y, bar_w, bar_h))
        if self.player.max_hp > 0:
            fill = int(bar_w * self.player.hp / self.player.max_hp)
            pygame.draw.rect(self.screen, COLOR_HP_BAR, (panel_x + 10, y, fill, bar_h))
        pygame.draw.rect(self.screen, (100, 40, 40), (panel_x + 10, y, bar_w, bar_h), 1)
        y += 25
        atk_text = self.font.render(f"ATK: {self.player.atk}", True, COLOR_WEAPON)
        self.screen.blit(atk_text, (panel_x + 10, y))
        y += 20
        def_text = self.font.render(f"DEF: {self.player.defense}", True, (100, 160, 255))
        self.screen.blit(def_text, (panel_x + 10, y))
        y += 30
        pygame.draw.line(self.screen, (60, 60, 80), (panel_x + 10, y), (panel_x + PANEL_W - 10, y))
        y += 10
        inv_title = self.font.render("Recent Items:", True, COLOR_TEXT)
        self.screen.blit(inv_title, (panel_x + 10, y))
        y += 20
        for name in self.player.pickup_log[-5:]:
            item_text = self.font.render(f" {name}", True, COLOR_MSG)
            self.screen.blit(item_text, (panel_x + 10, y))
            y += 18
        y = WIN_H - 160
        pygame.draw.line(self.screen, (60, 60, 80), (panel_x + 10, y), (panel_x + PANEL_W - 10, y))
        y += 8
        msg_title = self.font.render("Messages:", True, COLOR_TEXT)
        self.screen.blit(msg_title, (panel_x + 10, y))
        y += 20
        for msg in self.messages[-6:]:
            msg_text = self.font.render(msg[:22], True, COLOR_MSG)
            self.screen.blit(msg_text, (panel_x + 10, y))
            y += 18

    def _draw_death_screen(self):
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        cx, cy = WIN_W // 2, WIN_H // 2
        box_w, box_h = 320, 220
        box = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
        pygame.draw.rect(self.screen, (30, 15, 15), box, border_radius=10)
        pygame.draw.rect(self.screen, (180, 40, 40), box, 3, border_radius=10)
        title = self.font_title.render("YOU DIED", True, (220, 50, 50))
        tr = title.get_rect(center=(cx, cy - 70))
        self.screen.blit(title, tr)
        stats = [
            f"Floor Reached: {self.player.floor_reached}",
            f"Monsters Killed: {self.player.kills}",
            f"Final ATK: {self.player.atk}",
        ]
        sy = cy - 20
        for s in stats:
            text = self.font.render(s, True, COLOR_TEXT)
            rect = text.get_rect(center=(cx, sy))
            self.screen.blit(text, rect)
            sy += 28
        restart = self.font.render("Press R to Restart", True, (180, 180, 180))
        rr = restart.get_rect(center=(cx, cy + 75))
        self.screen.blit(restart, rr)

    def restart(self):
        self.current_floor = 1
        self.player = None
        self.messages.clear()
        self.state = "play"
        self._generate_floor()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == "dead":
                        if event.key == pygame.K_r:
                            self.restart()
                        continue
                    if self.state == "play":
                        if event.key == pygame.K_w:
                            self.try_move(0, -1)
                        elif event.key == pygame.K_s:
                            self.try_move(0, 1)
                        elif event.key == pygame.K_a:
                            self.try_move(-1, 0)
                        elif event.key == pygame.K_d:
                            self.try_move(1, 0)
                        elif event.key == pygame.K_SPACE:
                            self.try_attack()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
