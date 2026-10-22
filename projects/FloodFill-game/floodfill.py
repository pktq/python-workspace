import pygame as pg
import random

# settings
SCREEN_SIZE = (1280, 720)

RECT_WIDTH = 40
RECT_HEIGHT = 40
SQUARE_DIM = 40

COLORS = [
    [(250, 0, 0), "red"],
    [(0, 250, 0), "green"],
    [(0, 0, 250), "blue"],
    [(250, 250, 0), "yellow"],
]

# floodfill
class rect_data:
    def __init__(self, color, x, y, width, height):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class render_module():
    def __init__(self):
        pg.init()

        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.clock = pg.time.Clock()

    def window_name(self, string):
        pg.display.set_caption(string)

    def rect(self, pack: rect_data):
        pg.draw.rect(self.screen, pack.color, pg.Rect(pack.x, pack.y, pack.width, pack.height))

render = render_module()
    
horizontal_squares = SCREEN_SIZE[0] // SQUARE_DIM
vertical_squares = SCREEN_SIZE[1] // SQUARE_DIM

def new_grid_layout():
    final_grid = []

    for x in range(horizontal_squares):
        column = []
        for y in range(vertical_squares):
            column.append(rect_data(random.choice(COLORS)[0], x * SQUARE_DIM, y * SQUARE_DIM, SQUARE_DIM, SQUARE_DIM))

        final_grid.append(column)

    return final_grid

def color_fill(square_grid_snapshot, target_color_index):
    start = square_grid_snapshot[0][0] # [x][y]
    target = COLORS[target_color_index][0]
    print(f"Start: {start.color}")
    print(f"Target: {target}")

    return square_grid_snapshot

def draw(square_grid):
    for column in square_grid:
        for cell in column:
            render.rect(cell)
            
    pg.display.flip()
    return square_grid 

def main():
    running = True
    square_grid = new_grid_layout()
    square_grid_snapshot = square_grid

    draw(square_grid)
    while running: 
        for events in pg.event.get(): 
            if (events.type == pg.QUIT) or (events.type == pg.KEYDOWN and events.key == pg.K_ESCAPE): # kill game
                running = False
            elif events.type == pg.KEYDOWN:
                match events.key:
                    case pg.K_1: player_color_index = 0
                    case pg.K_2: player_color_index = 1
                    case pg.K_3: player_color_index = 2
                    case pg.K_4: player_color_index = 3
                
                render.window_name(f"Flood Fill | Color: {COLORS[player_color_index][1]}")
                square_grid_snapshot = draw(color_fill(square_grid_snapshot, player_color_index))

    pg.quit()

if __name__ == "__main__":
    main()