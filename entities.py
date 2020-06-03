"""
This file contains code for all entities in the submarine game
(Subs, Torpedoes, Trails etc)
"""

import arcade
import random
import math as maths
from copy import copy

from utilities import calculate_distance

PATROL_RADIUS = 500


class Entity:
        def __init__(self, position=[0, 0], speed=0, heading=360, acceleration=0, thrust=0, is_explosive=True):
            self.position = position
            self.speed = speed
            self.acceleration = acceleration
            self.heading = heading
            self.is_explosive = is_explosive
            self.thrust = thrust

            self.exploded = False
            self.boom_sound = arcade.load_sound("explode.wav")
            self.drag_coefficent = 0.01

        def update(self, delta_time, entities):
            self.acceleration = (self.thrust / 10) - self.speed * self.drag_coefficent

            self.speed += self.acceleration

            self.position[0] += self.speed * maths.sin(maths.radians(self.heading)) * delta_time
            self.position[1] += self.speed * maths.cos(maths.radians(self.heading)) * delta_time

            for entity in entities:

                both_explosive = entity.is_explosive and self.is_explosive
                both_not_exploded = not self.exploded and not entity.exploded
                close_enough = calculate_distance(tuple(self.position), tuple(entity.position)) < 20
                if entity is not self and both_explosive and both_not_exploded and close_enough:

                    try: entity.explode(entities)
                    except ValueError: pass
                    try: self.explode(entities)
                    except ValueError: pass
                    entities.append(Explosion(self.position))
                    arcade.play_sound(self.boom_sound)
        def explode(self, entities):
            self.speed = 0
            self.exploded = True
            entities.remove(self)
class Sub(Entity):
    def __init__(self, position=[0, 0], speed=0, heading=360):
        super().__init__(position, speed, heading)
        self.ping_sound = arcade.load_sound("ping.wav")
        self.torpedo_time = 0
        self.change_angle = 0

    def update(self, delta_time, entities):
        super().update(delta_time, entities)
        if self.heading + self.change_angle > 360:
            self.heading += self.change_angle - 360
        elif self.heading + self.change_angle < 1:
            self.heading += self.change_angle + 360
        else:
            self.heading += self.change_angle
        self.sprite.angle = -1 * self.heading

        if self.torpedo_time > 0:
            self.torpedo_time -= delta_time
        elif self.torpedo_time < 0:
            self.torpedo_time = 0
    def draw(self, player):
        screen_coords = player.game_coords_to_screen(tuple(self.position))

        if screen_coords != None:
            self.sprite.center_x, self.sprite.center_y = screen_coords
        self.sprite.draw()
    def fire_torpedo(self, entities):
        if self.torpedo_time == 0:
            self.torpedo_time = 5
            entities.append(Torpedo(copy(self.position), copy(self.speed) + 40, copy(self.heading)))


class Enemy(Sub):
    def __init__(self, position=[0, 0], speed=0, heading=360):
        super().__init__(position, speed, heading)
        self.sprite = arcade.Sprite("bad_sub.png", 0.1)
        self.pinged = False
        self.state = "patrol"
        self.thrust = random.randint(1, 2)
        self.target_heading = 360

        self.offset_x = random.randint(int(self.speed) - 40, 40 - int(self.speed)) * 3
        self.offset_y = random.randint(int(self.speed) - 40, 40 - int(self.speed)) * 3

        self.pick_target()



    def draw(self, player):
        range = calculate_distance(tuple(self.position), tuple(player.position))
        screen_coords = player.game_coords_to_screen(tuple(self.position))

        if screen_coords != None:

            if player.ping_time * 5 + 10 >= range:
                if not self.pinged:
                    arcade.play_sound(self.ping_sound)
                    self.pinged = True
                    self.offset_x = random.randint(int(self.speed) - 40, 40 - int(self.speed)) * 3
                    self.offset_y = random.randint(int(self.speed) - 40, 40 - int(self.speed)) * 3

                self.sprite.center_x, self.sprite.center_y = screen_coords
                self.sprite.draw()
            else:
                x, y = screen_coords
                arcade.draw_circle_filled(x + self.offset_x, y + self.offset_y, (40 - self.speed) * 6, (255, 255, 255, int(self.speed * 255 // 40 + 1)))
    def update(self, delta_time, entities):
        if abs(self.heading - self.target_heading) < 5:
            print("On target", end="")
            self.change_angle = 0
            target_x, target_y = self.target
            pos_x, pos_y = self.position
            self.target_heading = 180 + maths.degrees(maths.atan2(pos_x - target_x, pos_y - target_y))
            self.heading = self.target_heading
        elif self.heading > self.target_heading:
            self.change_angle = -5
        else:
            self.change_angle = 5

        super().update(delta_time, entities)
        if self.state == "patrol":
            self.patrol(delta_time)
    def patrol(self, delta_time):
        distance = calculate_distance(self.position, self.target)
        print(distance)
        if distance < 10:
            self.pick_target()
    def pick_target(self):
        x = random.randint(-PATROL_RADIUS, PATROL_RADIUS)
        y = random.randint(-PATROL_RADIUS, PATROL_RADIUS)

        self.target = [x, y]
        print("NEW TARGET {}".format(self.target))
        self.thrust = random.randint(1, 2)
        target_x, target_y = self.target
        pos_x, pos_y = self.position
        self.target_heading = 180 + maths.degrees(maths.atan2(pos_x - target_x, pos_y - target_y))


class Player(Sub):
    def __init__(self, centre_pos, position=[0, 0], speed=0, heading=360, trails = []):
        super().__init__(position, speed, heading)
        self.trails = trails
        self.sprite = arcade.Sprite("sub.png", 0.1)
        self.sprite.center_x, self.sprite.center_y = centre_pos
        self.ping_time = 0
    def get_pretty_speed(self):
        if self.thrust == -1:
            return "Astern Slow"
        elif self.thrust == 0:
            return "All Stop"
        elif self.thrust == 1:
            return "Ahead Slow"
        elif self.thrust == 2:
            return "Ahead Standard"
        elif self.thrust == 3:
            return "Ahead Flank"
        else:
            return "ERROR"
    def game_coords_to_screen(self, coords):
        if calculate_distance(coords, self.position) < 290:
            x, y = coords
            x += self.sprite.center_x - self.position[0]
            y += self.sprite.center_y - self.position[1]
            return (x, y)
        else:
            return None
    def display_trails(self):
        for trail in self.trails:
            trail.draw()

    def update(self, delta_time, entities):
        if not self.exploded:
            super().update(delta_time, entities)

            TRAIL_MAX_AGE = 5
            TRAIL_LENGTH = 10

            temp = []
            for trail in self.trails:
                trail.age += delta_time
                if trail.age < TRAIL_MAX_AGE:
                    temp.append(trail)
            self.trails = temp
            if self.speed > 0:
                try:
                    if len(self.trails) < TRAIL_LENGTH and self.trails[-1].age > TRAIL_MAX_AGE / TRAIL_LENGTH:
                        self.trails.append(Trail(self.position.copy(), self))
                except IndexError:
                    self.trails.append(Trail(self.position.copy(), self))

            if self.ping_time != 0:
                self.ping_time = self.ping_time + 1 if self.ping_time < 58 else 0
        else:
            self.explosion_time += delta_time
            if self.explosion_time > 3:
                arcade.close_window()
            for entity in entities:
                entity.pinged = True

    def draw(self, player):
        self.display_trails()

        if not self.exploded:
            super().draw(player)
            if self.ping_time > 0:
                arcade.draw_circle_outline(self.sprite.center_x, self.sprite.center_y, self.ping_time * 5, arcade.color.WHITE , 10)
        else:
            arcade.draw_text("Game Over", self.sprite.center_x - 250, self.sprite.center_y - 30, arcade.color.WHITE, 90)

    def explode(self, entities):
        self.exploded = True
        self.speed = 0
        self.explosion_time = 0

class Trail(Entity):
    def __init__(self, position, parent_ship, age=0):
        super().__init__(position, 0, 0, False)
        self.parent_ship = parent_ship
        self.age = age
    def draw(self):
        screen_coords = self.parent_ship.game_coords_to_screen(self.position)
        if screen_coords != None:
            x, y = screen_coords
            arcade.draw_circle_filled(x, y, 4, (255, 255, 255, 255 - maths.floor(self.age) * 25), 5)

class Torpedo(Entity):
    def __init__(self, position, speed, heading, lifetime=7, fuse_length=1):
        super().__init__(position, speed, heading, thrust=3, is_explosive=False)
        self.lifetime = lifetime
        self.age = 0
        self.fuse_length = fuse_length
        arcade.play_sound(arcade.load_sound("torpedo_launch.wav"))

    def update(self, delta_time, entities):
        super().update(delta_time, entities)

        self.age += delta_time

        if not self.is_explosive and self.age > self.fuse_length:
            self.is_explosive = True
        if self.age > self.lifetime:
            entities.remove(self)

    def draw(self, player):
        screen_coords = player.game_coords_to_screen(tuple(self.position))

        if screen_coords != None:
            x, y = screen_coords
            colour = arcade.color.GREEN if self.age < self.fuse_length else arcade.color.BLACK
            arcade.draw_circle_filled(x, y, 5, colour, 20)

class Explosion(Entity):
    def __init__(self, position):
        super().__init__(position, 0, 360)
        self.age = 0
    def update(self, delta_time, entities):
        super().update(delta_time, entities)
        if self.age > 3:
            entities.remove(self)
        else:
            self.age += delta_time
    def draw(self, player):
        screen_coords = player.game_coords_to_screen(tuple(self.position))
        if screen_coords != None:
            x, y = screen_coords
            arcade.draw_circle_filled(x, y, self.age * 5, arcade.color.RED , 10)
