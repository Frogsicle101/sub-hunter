import arcade
import time
import math as maths
import copy
import random

from entities import Enemy, Player

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
ANGLE_SPEED = 5



class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height):
        super().__init__(width, height, "Sub Hunter")
        #arcade.set_title("test")
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        self.CENTRE = (self.width // 2, self.height // 2)

        self.player = Player((self.CENTRE))
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
