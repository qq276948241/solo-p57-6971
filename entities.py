import random

from constants import (
    COLOR_PLAYER, COLOR_SLIME, COLOR_SKELETON, COLOR_BAT,
    COLOR_POTION, COLOR_WEAPON,
)


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
