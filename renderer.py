import pygame

from constants import (
    TILE, MAP_W, MAP_H, PANEL_W, WIN_W, WIN_H,
    WALL, FLOOR, STAIRS,
    COLOR_BG, COLOR_WALL, COLOR_FLOOR, COLOR_WALL_DIM, COLOR_FLOOR_DIM,
    COLOR_STAIRS, COLOR_STAIRS_DIM, COLOR_PLAYER, COLOR_TRAP,
    COLOR_PANEL_BG, COLOR_TEXT, COLOR_HP_BAR_BG, COLOR_HP_BAR,
    COLOR_MSG, COLOR_WEAPON,
    dim_color,
)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_large = pygame.font.SysFont("consolas", 22)
        self.font_title = pygame.font.SysFont("consolas", 28, bold=True)

    def render_all(self, tilemap, player, monsters, items, traps,
                   current_floor, messages, state):
        self._draw_map(tilemap)
        self._draw_traps(tilemap, traps)
        self._draw_items(tilemap, items)
        self._draw_monsters(tilemap, monsters)
        self._draw_player(player)
        self._draw_panel(player, current_floor, messages)
        if state == "dead":
            self._draw_death_screen(player)
        pygame.display.flip()

    def _draw_map(self, tilemap):
        self.screen.fill(COLOR_BG)
        for y in range(MAP_H):
            for x in range(MAP_W):
                rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                t = tilemap.tiles[y][x]
                visible = tilemap.is_visible(x, y)
                explored = tilemap.is_explored(x, y)
                if not explored:
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

    def _draw_traps(self, tilemap, traps):
        for trap in traps:
            if not (trap.revealed and (tilemap.is_visible(trap.x, trap.y) or tilemap.is_explored(trap.x, trap.y))):
                continue
            rect = pygame.Rect(trap.x * TILE + 4, trap.y * TILE + 4, TILE - 8, TILE - 8)
            c = COLOR_TRAP if tilemap.is_visible(trap.x, trap.y) else dim_color(COLOR_TRAP)
            pygame.draw.circle(self.screen, c, rect.center, TILE // 2 - 6)
            pygame.draw.rect(self.screen, (60, 20, 60), rect, 1, border_radius=4)
            cx, cy = rect.center
            pygame.draw.line(self.screen, (255, 220, 100),
                             (cx - 6, cy - 6), (cx + 6, cy + 6), 2)
            pygame.draw.line(self.screen, (255, 220, 100),
                             (cx + 6, cy - 6), (cx - 6, cy + 6), 2)

    def _draw_items(self, tilemap, items):
        for item in items:
            if not tilemap.is_visible(item.x, item.y):
                continue
            rect = pygame.Rect(item.x * TILE + 6, item.y * TILE + 6, TILE - 12, TILE - 12)
            if item.kind == "potion":
                pygame.draw.ellipse(self.screen, item.color, rect)
                pygame.draw.rect(self.screen, (180, 180, 180),
                                 (rect.centerx - 2, rect.top - 4, 4, 6))
            else:
                pygame.draw.polygon(self.screen, item.color,
                                    [rect.midtop, rect.bottomright, rect.bottomleft])

    def _draw_monsters(self, tilemap, monsters):
        for m in monsters:
            if not tilemap.is_visible(m.x, m.y):
                continue
            rect = pygame.Rect(m.x * TILE + 2, m.y * TILE + 2, TILE - 4, TILE - 4)
            pygame.draw.rect(self.screen, m.color, rect, border_radius=4)
            eye_y = rect.y + 10
            pygame.draw.circle(self.screen, (0, 0, 0), (rect.x + 9, eye_y), 3)
            pygame.draw.circle(self.screen, (0, 0, 0), (rect.x + TILE - 13, eye_y), 3)
            pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + 9, eye_y), 1)
            pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + TILE - 13, eye_y), 1)

    def _draw_player(self, player):
        px, py = player.x, player.y
        rect = pygame.Rect(px * TILE + 2, py * TILE + 2, TILE - 4, TILE - 4)
        pygame.draw.rect(self.screen, COLOR_PLAYER, rect, border_radius=6)
        eye_y = rect.y + 11
        pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + 9, eye_y), 4)
        pygame.draw.circle(self.screen, (255, 255, 255), (rect.x + TILE - 13, eye_y), 4)
        pygame.draw.circle(self.screen, (30, 30, 30), (rect.x + 9, eye_y), 2)
        pygame.draw.circle(self.screen, (30, 30, 30), (rect.x + TILE - 13, eye_y), 2)

    def _draw_panel(self, player, current_floor, messages):
        panel_x = MAP_W * TILE
        panel_rect = pygame.Rect(panel_x, 0, PANEL_W, WIN_H)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, (60, 60, 80), (panel_x, 0), (panel_x, WIN_H), 2)
        y = 12
        title = self.font_large.render("STATUS", True, COLOR_TEXT)
        self.screen.blit(title, (panel_x + 10, y))
        y += 35
        floor_text = self.font.render(f"Floor: {current_floor}", True, COLOR_STAIRS)
        self.screen.blit(floor_text, (panel_x + 10, y))
        y += 25
        hp_label = self.font.render(f"HP: {player.hp}/{player.max_hp}", True, COLOR_TEXT)
        self.screen.blit(hp_label, (panel_x + 10, y))
        y += 20
        bar_w = PANEL_W - 30
        bar_h = 14
        pygame.draw.rect(self.screen, COLOR_HP_BAR_BG, (panel_x + 10, y, bar_w, bar_h))
        if player.max_hp > 0:
            fill = int(bar_w * player.hp / player.max_hp)
            pygame.draw.rect(self.screen, COLOR_HP_BAR, (panel_x + 10, y, fill, bar_h))
        pygame.draw.rect(self.screen, (100, 40, 40), (panel_x + 10, y, bar_w, bar_h), 1)
        y += 25
        atk_text = self.font.render(f"ATK: {player.atk}", True, COLOR_WEAPON)
        self.screen.blit(atk_text, (panel_x + 10, y))
        y += 20
        def_text = self.font.render(f"DEF: {player.defense}", True, (100, 160, 255))
        self.screen.blit(def_text, (panel_x + 10, y))
        y += 30
        pygame.draw.line(self.screen, (60, 60, 80), (panel_x + 10, y), (panel_x + PANEL_W - 10, y))
        y += 10
        inv_title = self.font.render("Recent Items:", True, COLOR_TEXT)
        self.screen.blit(inv_title, (panel_x + 10, y))
        y += 20
        for name in player.pickup_log[-5:]:
            item_text = self.font.render(f" {name}", True, COLOR_MSG)
            self.screen.blit(item_text, (panel_x + 10, y))
            y += 18
        y = WIN_H - 160
        pygame.draw.line(self.screen, (60, 60, 80), (panel_x + 10, y), (panel_x + PANEL_W - 10, y))
        y += 8
        msg_title = self.font.render("Messages:", True, COLOR_TEXT)
        self.screen.blit(msg_title, (panel_x + 10, y))
        y += 20
        for msg in messages[-6:]:
            msg_text = self.font.render(msg[:22], True, COLOR_MSG)
            self.screen.blit(msg_text, (panel_x + 10, y))
            y += 18

    def _draw_death_screen(self, player):
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
            f"Floor Reached: {player.floor_reached}",
            f"Monsters Killed: {player.kills}",
            f"Final ATK: {player.atk}",
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
