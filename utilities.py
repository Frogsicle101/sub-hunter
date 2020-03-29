"""
This file contains various helper functions used in the submarine game.
"""
def calculate_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** (1 / 2)
