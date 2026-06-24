import random
import pygame

from constants import (
    MAP_W, MAP_H, WALL, FLOOR, STAIRS, FOV_RADIUS,
)


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
