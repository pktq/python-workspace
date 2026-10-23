import pygame as pg
import random

WIDTH, HEIGHT, CELL = 1280, 720, 20
HORIZONTAL, VERTICAL = WIDTH // CELL, HEIGHT // CELL
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

        self.screen = pg.display.set_mode((WIDTH, HEIGHT))

    def rect(self, pack: rect_data):
        pg.draw.rect(self.screen, pack.color, pg.Rect(pack.x, pack.y, pack.width, pack.height))

render = render_module()

def new_grid_layout():
    final_grid = []

    for x in range(HORIZONTAL):
        column = []
        for y in range(VERTICAL):
            column.append(rect_data(random.choice(COLORS)[0], x * CELL, y * CELL, CELL, CELL))

        final_grid.append(column)

    return final_grid

def scan(square_grid_snapshot, old, x, y):
    queue = []

    directions = [
        {"x": x, "y": y + 1}, # up
        {"x": x + 1, "y": y}, # right
        {"x": x, "y": y - 1}, # down
        {"x": x - 1, "y": y}, # left
    ]

    for pkt in directions:
        p_x, p_y = pkt["x"], pkt["y"]
        if (p_x < 0 or p_y < 0) or (p_x >= len(square_grid_snapshot) or p_y >= len(square_grid_snapshot[0])):
            continue

        if square_grid_snapshot[p_x][p_y].color == old:
            queue.append({"x": p_x, "y": p_y})

    return queue

def color_fill(square_grid_snapshot, target_color_index):
    old = square_grid_snapshot[0][0].color # [x][y]
    target = COLORS[target_color_index][0]

    if old == target: # early skip
        return square_grid_snapshot

    queue = [{"x": 0, "y": 0}]
    confirmed = {(0, 0)}

    while len(queue) != 0:
        pkt = queue.pop(0)
        square_grid_snapshot[pkt["x"]][pkt["y"]].color = target

        surrounding = scan(square_grid_snapshot, old, pkt["x"], pkt["y"])

        for surr in surrounding:
            key = (surr["x"], surr["y"])
            if key not in confirmed:
                confirmed.add(key)
                queue.append(surr)
    
    if len(confirmed) == (HORIZONTAL * VERTICAL):
        print("done")

    return square_grid_snapshot

def draw(square_grid, color_index):
    for column in square_grid:
        for cell in column:
            render.rect(cell)
            
    render.pg.display.set_caption(f"Flood Fill | Color: {COLORS[color_index][1]}")
    pg.display.flip()
    return square_grid 

class player:
    def __init__(self):
        self.square_grid = new_grid_layout()
        self.square_grid_snapshot = self.square_grid
        self.color_index = 0
        self.square_grid[0][0].color = (0, 0, 0)

        self.step_count = 0

def mains():
    running = True
    game = player()

    square_grid_snapshot = game.square_grid
    game.square_grid[0][0].color = (0, 0, 0) # start pos start as black

    draw(game.square_grid, game.color_index)
    while running: 
        for events in pg.event.get(): 
            if (events.type == pg.QUIT) or (events.type == pg.KEYDOWN and events.key == pg.K_ESCAPE): # kill game
                running = False
            elif events.type == pg.KEYDOWN:
                match events.key:
                    case pg.K_1: game.color_index = 0
                    case pg.K_2: game.color_index = 1
                    case pg.K_3: game.color_index = 2
                    case pg.K_4: game.color_index = 3
                
                square_grid_snapshot = draw(color_fill(square_grid_snapshot, game.color_index), game.color_index)

    pg.quit()

def new_game():
    square_grid = new_grid_layout()
    square_grid_snapshot = square_grid
    color_index = 0
    steps = 0

    square_grid[0][0].color = (0, 0, 0)

def main():
    pg.init()
    running = True
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    while running:
        for events in pg.event.get():
            if (events.type == pg.QUIT) or (events.type == pg.KEYDOWN and events.key == pg.K_ESCAPE): # kill game
                running = False
            if events.ket == pg.K_r:
                new_game()

    pg.quit()

if __name__ == "__main__":
    main()