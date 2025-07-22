import curses
import random

# Configuration
HEIGHT = 20
WIDTH = 60

SNAKE_CHAR = '#'
FOOD_CHAR = '*'

UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

DIRECTIONS = {
    curses.KEY_UP: UP,
    curses.KEY_DOWN: DOWN,
    curses.KEY_LEFT: LEFT,
    curses.KEY_RIGHT: RIGHT,
}


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(150)

    snake = [(HEIGHT // 2, WIDTH // 2 + i) for i in range(3)]
    direction = LEFT

    food = None
    score = 0

    while True:
        if food is None:
            food = (random.randint(1, HEIGHT - 2), random.randint(1, WIDTH - 2))
            while food in snake:
                food = (random.randint(1, HEIGHT - 2), random.randint(1, WIDTH - 2))

        # Input handling
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key in DIRECTIONS:
            new_direction = DIRECTIONS[key]
            # Prevent reversing direction
            if (new_direction[0] != -direction[0] or new_direction[1] != -direction[1]):
                direction = new_direction

        # Move snake
        head_y, head_x = snake[0]
        delta_y, delta_x = direction
        new_head = (head_y + delta_y, head_x + delta_x)

        # Collision detection
        if (new_head[0] in (0, HEIGHT - 1) or
                new_head[1] in (0, WIDTH - 1) or
                new_head in snake):
            msg = f"Game Over! Score: {score}"
            stdscr.nodelay(False)
            stdscr.clear()
            stdscr.addstr(HEIGHT // 2, (WIDTH - len(msg)) // 2, msg)
            stdscr.refresh()
            stdscr.getch()
            break

        snake.insert(0, new_head)
        if new_head == food:
            score += 1
            food = None
        else:
            snake.pop()

        # Render
        stdscr.clear()
        stdscr.border()
        for y, x in snake:
            stdscr.addch(y, x, SNAKE_CHAR)
        if food:
            stdscr.addch(food[0], food[1], FOOD_CHAR)
        stdscr.addstr(0, 2, f" Score: {score} ")
        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)
