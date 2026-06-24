import pygame
import sys
import random
from collections import deque

from constants import WIN_W, WIN_H, FPS, STAIRS
from map_generator import TileMap, Trap
from entities import Player, create_monster, create_item
from renderer import Renderer


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Roguelike Dungeon")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
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
        self.renderer.render_all(
            self.tilemap, self.player, self.monsters,
            self.items, self.traps, self.current_floor,
            self.messages, self.state,
        )

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
