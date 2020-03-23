import arcade
import time
import math as maths
import copy
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
ANGLE_SPEED = 5
BOOM_SOUND = arcade.load_sound("explode.wav")

class Entity:
        def __init__(self, position, speed, heading, is_explosive=True):
            self.position = position
            self.speed = speed
            self.heading = heading
            self.is_explosive = is_explosive
            self.exploded = False
        def update(self, delta_time, entities):
            self.position[0] = self.position[0] + self.speed * maths.sin(maths.radians(self.heading)) * delta_time
            self.position[1] = self.position[1] + self.speed * maths.cos(maths.radians(self.heading)) * delta_time

            for entity in entities:
                if entity is not self and entity.is_explosive and self.is_explosive and not self.exploded and not entity.exploded and calculate_distance(tuple(self.position), tuple(entity.position)) < 20:
                    try: entity.explode(entities)
                    except ValueError: pass
                    try: self.explode(entities)
                    except ValueError: pass
                    entities.append(Explosion(self.position))
                    arcade.play_sound(BOOM_SOUND)
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
        self.sprite.angle = - 1 * self.heading

        if self.torpedo_time > 0:
            self.torpedo_time -= delta_time
        elif self.torpedo_time < 0:
            self.torpedo_time = 0
    def draw(self, player):
        screen_coords = player.game_coords_to_screen(tuple(self.position))

        if screen_coords != None:
            self.sprite.center_x, self.sprite.center_y = screen_coords
            self.sprite.center_x += 3.5
        self.sprite.draw()
    def fire_torpedo(self, entities):
        if self.torpedo_time == 0:
            self.torpedo_time = 5
            entities.append(Torpedo(copy.copy(self.position), copy.copy(self.speed) + 40, copy.copy(self.heading)))


class Enemy(Sub):
    def __init__(self, position=[0, 0], speed=0, heading=360):
        super().__init__(position, speed, heading)
        self.sprite = arcade.Sprite("bad_sub.png", 0.1)
        self.pinged = False
        self.offset_x = random.randint(self.speed - 40, 40-self.speed) * 3
        self.offset_y = random.randint(self.speed - 40, 40-self.speed) * 3

    def draw(self, player):

        range = calculate_distance(tuple(self.position), tuple(player.position))
        screen_coords = player.game_coords_to_screen(tuple(self.position))

        if screen_coords != None:

            if player.ping_time * 5 + 10 >= range:
                if not self.pinged:
                    arcade.play_sound(self.ping_sound)
                    self.pinged = True
                    self.offset_x = random.randint(self.speed - 40, 40-self.speed) * 3
                    self.offset_y = random.randint(self.speed - 40, 40-self.speed) * 3

                self.sprite.center_x, self.sprite.center_y = screen_coords
                self.sprite.draw()
            else:
                x, y = screen_coords
                arcade.draw_circle_filled(x + self.offset_x, y + self.offset_y, (40 - self.speed) * 6, (255, 255, 255, self.speed * 255 // 40 + 1), (41 - self.speed))
    def update(self, delta_time, entities):
        super().update(delta_time, entities)
        angle = 180 + maths.degrees(maths.atan2(self.position[0] - entities[0].position[0], self.position[1] - entities[0].position[1]))
        self.heading = angle if angle > 0 else angle + 360

class Player(Sub):
    def __init__(self, position=[0, 0], speed=0, heading=360, trails = []):
        super().__init__(position, speed, heading)
        self.trails = trails
        self.sprite = arcade.Sprite("sub.png", 0.1)
        self.sprite.center_x, self.sprite.center_y = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.ping_time = 0
    def get_pretty_speed(self):
        if self.speed == -10:
            return "Astern Slow"
        elif self.speed == 0:
            return "All Stop"
        elif self.speed == 10:
            return "Ahead Slow"
        elif self.speed == 20:
            return "Ahead Standard"
        elif self.speed == 30:
            return "Ahead Flank"
        else:
            return "ERROR"
    def game_coords_to_screen(self, coords):
        if calculate_distance(coords, self.position) < 290:
            x, y = coords
            x += SCREEN_WIDTH // 2 - self.position[0]
            y += SCREEN_HEIGHT // 2 - self.position[1]
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
                arcade.draw_circle_outline(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.ping_time * 5, arcade.color.WHITE , 10)
        else:
            arcade.draw_text("Game Over", SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 30, arcade.color.WHITE, 90)

    def explode(self, entities):
        self.exploded = True
        self.speed = 0
        self.explosion_time = 0
def calculate_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return maths.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

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
        super().__init__(position, speed, heading, False)
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

class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height):
        super().__init__(width, height, "Sub Hunter")
        #arcade.set_title("test")
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        self.CENTRE = (self.width // 2, self.height // 2)

        self.player = Player()
        self.entities = [self.player, Enemy([200, 300]), Enemy([175, 350], 10, 270)]

    def on_draw(self):
        """ Render the screen. """
        arcade.start_render()

        #Draws Background
        arcade.draw_circle_filled(self.CENTRE[0], self.CENTRE[1], 290, arcade.color.NAVY_BLUE, 20)

        #Draws Edge of Sonar Display
        arcade.draw_circle_outline(self.CENTRE[0], self.CENTRE[1], 290, arcade.color.DARK_OLIVE_GREEN, 10)

        #Draws all entities
        for entity in reversed(self.entities):
                try:
                    entity.draw(self.player)
                except Exception as e:
                    print(e)

        #Draws informative text
        arcade.draw_text("Vessel Location:\nX: {:.2f}\nY: {:.2f}\nHeading: {}\nSpeed: {}"
                .format(self.player.position[0] // 10, self.player.position[1] // 10,
                    self.player.heading, self.player.get_pretty_speed()),
                10 , self.height - 70, arcade.color.WHITE, 12)

        if self.player.torpedo_time <= 0:
            text = "Torpedo Ready [Enter]"
        else:
            text = "Loading Torpedo ({:.1f})".format(self.player.torpedo_time)

        arcade.draw_text(text, 20, 20, arcade.color.WHITE, 12)

    def update(self, delta_time):

        #Updates entities
        for entity in self.entities:
            if self.player.ping_time <= 1:
                entity.pinged = False
            entity.update(delta_time, self.entities)


    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        # Rotate left/right
        if key == arcade.key.LEFT:
            self.player.change_angle = -1 * ANGLE_SPEED
        elif key == arcade.key.RIGHT:
            self.player.change_angle = ANGLE_SPEED
        elif key == arcade.key.SPACE:
            self.player.ping_time = 1
        elif key == arcade.key.UP:
            self.player.speed = self.player.speed + 10 if self.player.speed < 30 else 30
        elif key == arcade.key.DOWN:
            self.player.speed = self.player.speed - 10 if self.player.speed > -10 else -10
        elif key == arcade.key.ENTER:
            self.player.fire_torpedo(self.entities)
    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_angle = 0


def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.setup()
    #arcade.schedule(game.on_draw, 1 / 80)
    arcade.run()


if __name__ == "__main__":
    main()
