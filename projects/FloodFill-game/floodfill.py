import pygame as pg
import random
from settings import *

class RenderMod():
    def __init__(self):
        pg.init()

        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.clock = pg.time.Clock()

    def rect(self, color, position_x, position_y, width, height):
        pg.draw.rect(self.screen, color, pg.Rect(position_x, position_y, width, height))

render = RenderMod()

def main():
    running = True
    
    horizontal_squares = SCREEN_SIZE[0] // SQUARE_DIM
    vertical_squares = SCREEN_SIZE[1] // SQUARE_DIM

    grid = []
    for x in range(horizontal_squares):
        col = []
        for y in range(vertical_squares):
            col.append(random.choice(COLORS))
        grid.append(col)

    while running: 
        for events in pg.event.get(): # kill game
            if (events.type == pg.QUIT) or (events.type == pg.KEYDOWN and events.key == pg.K_ESCAPE):
                running = False

        # hi
        for x in range(horizontal_squares):
            for y in range(vertical_squares): 
                render.rect(grid[x][y], x * SQUARE_DIM, y * SQUARE_DIM, RECT_WIDTH, RECT_HEIGHT)

        pg.display.flip()
        render.clock.tick(REFRESH_RATE)

    pg.quit()

if __name__ == "__main__":
    main()