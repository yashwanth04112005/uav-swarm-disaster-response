import random

EMPTY = 0
OBSTACLE = 1
HAZARD = 2
SURVIVOR = 3


class DisasterMap:

    def __init__(self, width, height):

        self.width = width
        self.height = height

        self.grid = [
            [EMPTY for _ in range(width)]
            for _ in range(height)
        ]

    def generate(self):

        for y in range(self.height):
            for x in range(self.width):

                r = random.random()

                if r < 0.10:
                    self.grid[y][x] = OBSTACLE

                elif r < 0.15:
                    self.grid[y][x] = HAZARD

        self.place_survivors(5)

    def place_survivors(self, count):

        placed = 0

        while placed < count:

            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)

            if self.grid[y][x] == EMPTY:

                self.grid[y][x] = SURVIVOR

                placed += 1