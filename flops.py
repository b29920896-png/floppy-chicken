"""
Flappy Bird with a leaderboard, unique player names, power-ups,
and a customizable bird color.

Controls:
    SPACE / mouse click ... flap (and start / restart)
    ENTER ................. confirm your name
    LEFT / RIGHT .......... choose your bird color (name screen)
    C ..................... change bird color (game over screen)
    N ..................... pick a new name (game over screen)
"""
import json
import os
import random
import sys

import pygame

# ---------- Setup ----------
pygame.init()
WIDTH, HEIGHT = 400, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()
big_font = pygame.font.SysFont(None, 64)
mid_font = pygame.font.SysFont(None, 40)
small_font = pygame.font.SysFont(None, 30)
tiny_font = pygame.font.SysFont(None, 22)

# ---------- Settings you can tweak! ----------
GRAVITY = 0.5         # How fast the bird falls
FLAP_POWER = -8       # How high each flap lifts the bird (negative = up)
PIPE_SPEED = 3        # How fast pipes move left
PIPE_GAP = 160        # Size of the opening between pipes
PIPE_WIDTH = 60
PIPE_DISTANCE = 220   # Horizontal space between pipes
BIRD_X = 80           # The bird stays at this x position
BIRD_SIZE = 30
POWERUP_CHANCE = 0.3  # 0.3 = 30% of pipes carry a power-up
MAX_NAME_LENGTH = 12

# Bird colors you can pick from. Add your own: ("Name", (red, green, blue))
COLORS = [
    ("Yellow", (255, 215, 0)),
    ("Red", (230, 50, 50)),
    ("Blue", (60, 120, 255)),
    ("Green", (150, 230, 50)),
    ("Pink", (255, 130, 190)),
    ("Purple", (160, 90, 220)),
    ("Orange", (255, 150, 30)),
    ("White", (245, 245, 245)),
    ("Black", (40, 40, 40)),
]

# Power-ups: how long they last (seconds), their color, and a short icon
POWERUPS = {
    "shield": {"label": "Shield",    "seconds": 5, "color": (0, 120, 255), "icon": "S"},
    "slow":   {"label": "Slow-Mo",   "seconds": 6, "color": (160, 80, 220), "icon": "Z"},
    "double": {"label": "2x Points", "seconds": 8, "color": (255, 140, 0), "icon": "2x"},
}

# Colors (Red, Green, Blue)
SKY = (135, 206, 235)
GREEN = (60, 180, 75)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 40, 40)
HIGHLIGHT = (255, 215, 0)

# ---------- Leaderboard (saved in a file next to this script) ----------
SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")


def load_scores():
    """
    Read the leaderboard file.
    Returns a dict like {"Anna": {"score": 12, "color": 2}, ...}
    (Old files that only stored a number per player are converted.)
    """
    try:
        with open(SCORE_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}

    scores = {}
    for name, value in data.items():
        if isinstance(value, dict):
            scores[name] = {"score": int(value.get("score", 0)),
                            "color": int(value.get("color", 0)) % len(COLORS)}
        elif isinstance(value, int):
            scores[name] = {"score": value, "color": 0}
    return scores


def save_scores(scores):
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)


def name_taken(name, scores):
    """Names are not case-sensitive: 'Anna' and 'anna' count as the same."""
    return name.lower() in [existing.lower() for existing in scores]


def top_scores(scores, count=5):
    """The best players, highest score first (players with 0 are hidden)."""
    ranking = [(name, info["score"], info["color"])
               for name, info in scores.items() if info["score"] > 0]
    return sorted(ranking, key=lambda item: item[1], reverse=True)[:count]


# ---------- Game helpers ----------
def new_pipe():
    """Make a pipe at the right edge. Some pipes carry a power-up in the gap."""
    powerup = None
    if random.random() < POWERUP_CHANCE:
        powerup = random.choice(list(POWERUPS))
    return {"x": WIDTH, "gap_y": random.randint(150, HEIGHT - 150),
            "scored": False, "powerup": powerup}


def reset_game():
    """Return fresh starting values for a new round."""
    bird_y = HEIGHT // 2
    velocity = 0
    pipes = [new_pipe()]
    score = 0
    effects = {}  # Active power-ups, like {"shield": 240} (frames left)
    return bird_y, velocity, pipes, score, effects


def powerup_rect(pipe):
    """The invisible box around a power-up, used to detect pickups."""
    center_x = int(pipe["x"]) + PIPE_WIDTH // 2
    return pygame.Rect(center_x - 14, pipe["gap_y"] - 14, 28, 28)


# ---------- Drawing helpers ----------
def draw_text(text, font, color, center):
    image = font.render(text, True, color)
    screen.blit(image, image.get_rect(center=center))


def draw_bird(x, y, color):
    """Draw the bird at (x, y) in the given color."""
    pygame.draw.circle(screen, color, (x, y), BIRD_SIZE // 2)
    pygame.draw.circle(screen, BLACK, (x, y), BIRD_SIZE // 2, 2)       # outline
    beak = [(x + 12, y - 1), (x + 22, y + 3), (x + 12, y + 7)]
    pygame.draw.polygon(screen, (255, 120, 0), beak)                   # beak
    pygame.draw.polygon(screen, BLACK, beak, 1)
    pygame.draw.circle(screen, WHITE, (x + 5, y - 4), 5)               # eye
    pygame.draw.circle(screen, BLACK, (x + 7, y - 4), 2)               # pupil


def draw_leaderboard(top_y, highlight=None):
    """Show the top 5 players. The player named in `highlight` is yellow."""
    draw_text("Top Players", mid_font, WHITE, (WIDTH // 2, top_y))
    ranking = top_scores(scores)
    if not ranking:
        draw_text("No scores yet", small_font, WHITE, (WIDTH // 2, top_y + 40))
        return
    for i, (name, best, bird_color) in enumerate(ranking):
        text_color = HIGHLIGHT if name == highlight else WHITE
        y = top_y + 30 + i * 30
        # A small dot in the player's bird color
        pygame.draw.circle(screen, COLORS[bird_color][1], (60, y + 9), 7)
        pygame.draw.circle(screen, BLACK, (60, y + 9), 7, 1)
        name_image = small_font.render(f"{i + 1}. {name}", True, text_color)
        score_image = small_font.render(str(best), True, text_color)
        screen.blit(name_image, (76, y))
        screen.blit(score_image, score_image.get_rect(topright=(WIDTH - 60, y)))


def draw_name_screen():
    screen.fill(SKY)
    draw_text("Flappy Bird", big_font, WHITE, (WIDTH // 2, 55))
    draw_text("Enter your name:", small_font, WHITE, (WIDTH // 2, 110))

    # The text box
    box = pygame.Rect(70, 130, WIDTH - 140, 45)
    pygame.draw.rect(screen, WHITE, box, border_radius=6)
    cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
    draw_text(typed_name + cursor, mid_font, BLACK, box.center)

    draw_text("Press ENTER to continue", tiny_font, WHITE, (WIDTH // 2, 195))
    if message:
        draw_text(message, small_font, RED, (WIDTH // 2, 222))

    # Bird color picker
    draw_text("<", mid_font, WHITE, (WIDTH // 2 - 65, 275))
    draw_text(">", mid_font, WHITE, (WIDTH // 2 + 65, 275))
    draw_bird(WIDTH // 2, 275, COLORS[color_index][1])
    draw_text(COLORS[color_index][0], small_font, WHITE, (WIDTH // 2, 310))
    draw_text("LEFT / RIGHT: change bird color", tiny_font, WHITE, (WIDTH // 2, 332))

    draw_leaderboard(375)


# ---------- Main game ----------
scores = load_scores()
state = "name"        # "name" -> "ready" -> "play" -> "over"
typed_name = ""       # What the player is typing right now
player_name = ""      # The confirmed name
message = ""          # Error message on the name screen
color_index = 0       # Which color in COLORS the bird uses
new_best = False
over_delay = 0        # Short pause after dying so you don't restart by accident
bird_y, velocity, pipes, score, effects = reset_game()

while True:
    # 1. Handle input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if state == "name":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    candidate = typed_name.strip()
                    if not candidate:
                        message = "Please type a name."
                    elif name_taken(candidate, scores):
                        message = "That name is already taken!"
                    else:
                        player_name = candidate
                        scores[player_name] = {"score": 0, "color": color_index}  # Reserve it
                        save_scores(scores)
                        message = ""
                        bird_y, velocity, pipes, score, effects = reset_game()
                        state = "ready"
                elif event.key == pygame.K_LEFT:
                    color_index = (color_index - 1) % len(COLORS)
                elif event.key == pygame.K_RIGHT:
                    color_index = (color_index + 1) % len(COLORS)
                elif event.key == pygame.K_BACKSPACE:
                    typed_name = typed_name[:-1]
                    message = ""
                elif len(event.unicode) == 1 and len(typed_name) < MAX_NAME_LENGTH:
                    if event.unicode.isalnum() or event.unicode in " _-":
                        typed_name += event.unicode
                        message = ""
        else:
            flap = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) \
                or event.type == pygame.MOUSEBUTTONDOWN

            if state == "ready" and flap:
                state = "play"
                velocity = FLAP_POWER
            elif state == "play" and flap:
                velocity = FLAP_POWER
            elif state == "over" and over_delay == 0:
                if flap:
                    bird_y, velocity, pipes, score, effects = reset_game()
                    state = "ready"
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                    typed_name = ""
                    message = ""
                    state = "name"
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                    color_index = (color_index + 1) % len(COLORS)
                    scores[player_name]["color"] = color_index
                    save_scores(scores)

    # 2. Update the game (only while playing)
    if over_delay > 0:
        over_delay -= 1

    if state == "play":
        # Slow-Mo makes the pipes move at half speed
        speed = PIPE_SPEED * (0.5 if "slow" in effects else 1)

        velocity += GRAVITY
        bird_y += velocity

        for pipe in pipes:
            pipe["x"] -= speed

        # Add a new pipe when the last one has moved far enough
        if pipes[-1]["x"] < WIDTH - PIPE_DISTANCE:
            pipes.append(new_pipe())

        # Remove pipes that went off the screen
        if pipes[0]["x"] < -PIPE_WIDTH:
            pipes.pop(0)

        shielded = "shield" in effects
        crashed = False
        bird_rect = pygame.Rect(BIRD_X - BIRD_SIZE // 2, int(bird_y) - BIRD_SIZE // 2,
                                BIRD_SIZE, BIRD_SIZE)

        # Ceiling and ground: the shield makes you bounce instead of crash
        if bird_y < 0 or bird_y > HEIGHT:
            if shielded:
                bird_y = max(0, min(HEIGHT, bird_y))
                velocity = 0
            else:
                crashed = True

        for pipe in pipes:
            x = int(pipe["x"])
            top_pipe = pygame.Rect(x, 0, PIPE_WIDTH, pipe["gap_y"] - PIPE_GAP // 2)
            bottom_pipe = pygame.Rect(x, pipe["gap_y"] + PIPE_GAP // 2, PIPE_WIDTH, HEIGHT)
            if not shielded and (bird_rect.colliderect(top_pipe)
                                 or bird_rect.colliderect(bottom_pipe)):
                crashed = True

            # Pick up a power-up
            if pipe["powerup"] and bird_rect.colliderect(powerup_rect(pipe)):
                kind = pipe["powerup"]
                effects[kind] = POWERUPS[kind]["seconds"] * FPS
                pipe["powerup"] = None

            # Score a point when the bird passes a pipe
            if not pipe["scored"] and pipe["x"] + PIPE_WIDTH < BIRD_X:
                pipe["scored"] = True
                score += 2 if "double" in effects else 1

        # Count down the active power-ups
        for kind in list(effects):
            effects[kind] -= 1
            if effects[kind] <= 0:
                del effects[kind]

        if crashed:
            state = "over"
            over_delay = 30  # About half a second
            new_best = score > scores[player_name]["score"]
            if new_best:
                scores[player_name]["score"] = score
                save_scores(scores)

    # 3. Draw everything
    if state == "name":
        draw_name_screen()
    else:
        screen.fill(SKY)

        for pipe in pipes:
            x = int(pipe["x"])
            pygame.draw.rect(screen, GREEN, (x, 0, PIPE_WIDTH, pipe["gap_y"] - PIPE_GAP // 2))
            pygame.draw.rect(screen, GREEN, (x, pipe["gap_y"] + PIPE_GAP // 2,
                                             PIPE_WIDTH, HEIGHT))
            if pipe["powerup"]:
                info = POWERUPS[pipe["powerup"]]
                center = powerup_rect(pipe).center
                pygame.draw.circle(screen, info["color"], center, 14)
                pygame.draw.circle(screen, WHITE, center, 14, 2)
                draw_text(info["icon"], tiny_font, WHITE, center)

        # The bird, in the player's chosen color
        draw_bird(BIRD_X, int(bird_y), COLORS[color_index][1])

        # Shield bubble (it flickers when it's about to run out)
        if "shield" in effects:
            frames_left = effects["shield"]
            if frames_left > 90 or (frames_left // 6) % 2 == 0:
                pygame.draw.circle(screen, POWERUPS["shield"]["color"],
                                   (BIRD_X, int(bird_y)), BIRD_SIZE // 2 + 7, 3)

        # Score, player name, and active power-ups
        draw_text(str(score), big_font, WHITE, (WIDTH // 2, 50))
        screen.blit(tiny_font.render(player_name, True, WHITE), (10, 10))
        for i, (kind, frames_left) in enumerate(effects.items()):
            info = POWERUPS[kind]
            text = f"{info['label']} {frames_left / FPS:.1f}s"
            screen.blit(small_font.render(text, True, info["color"]), (10, 40 + i * 26))

        if state == "ready":
            draw_text("Press SPACE to start", small_font, WHITE, (WIDTH // 2, HEIGHT // 2 + 60))

        if state == "over":
            panel = pygame.Surface((340, 440), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 150))
            screen.blit(panel, (30, 80))
            draw_text("Game Over", big_font, WHITE, (WIDTH // 2, 125))
            draw_text(f"Score: {score}", mid_font, WHITE, (WIDTH // 2, 175))
            if new_best:
                draw_text("New personal best!", small_font, HIGHLIGHT, (WIDTH // 2, 208))
            else:
                draw_text(f"Your best: {scores[player_name]['score']}", small_font, WHITE,
                          (WIDTH // 2, 208))
            draw_leaderboard(255, highlight=player_name)
            draw_text("SPACE: play again   N: new name", tiny_font, WHITE, (WIDTH // 2, 470))
            draw_text("C: change bird color", tiny_font, WHITE, (WIDTH // 2, 495))

    pygame.display.flip()
    clock.tick(FPS)
