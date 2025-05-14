import pygame
import os
from pygame.math import Vector2

# --- Base Game Setup ---
# FIXED Window Dimensions
FIXED_SCREEN_WIDTH = 1000  # Total window width (game area + HUD)
FIXED_SCREEN_HEIGHT = 800 # Total window height
HUD_WIDTH = 150           # Width of the HUD on the right side

CELL_NUMBER_DEFAULT = 20 # Default, will change with difficulty
CELL_SIZE_DEFAULT = 30   # Default cell size in pixels

# --- Audio Settings ---
DEFAULT_VOLUME = 0.7     # Default volume level (0.0 to 1.0)
VOLUME_STEP = 0.1        # Volume increment/decrement step

# --- Colors ---
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_ORANGE = (255, 165, 0)
COLOR_DARK_GREEN = (56, 74, 12)
COLOR_LIGHT_GREEN = (167, 209, 61)
COLOR_GRASS_1 = (175, 215, 70)
COLOR_GRASS_2 = (167, 209, 61)
COLOR_BUTTON_NORMAL = (56, 74, 12)
COLOR_BUTTON_HOVER = (76, 94, 32)
COLOR_BUTTON_HIGHLIGHT = (86, 124, 42)
COLOR_BUTTON_HIGHLIGHT_HOVER = (106, 144, 62)
COLOR_BUTTON_BACK_NORMAL = (150, 30, 30)
COLOR_BUTTON_BACK_HOVER = (170, 50, 50)
COLOR_TEXT_INPUT_INACTIVE = (100, 100, 100)
COLOR_TEXT_INPUT_ACTIVE = (0, 120, 215)
COLOR_SCORE_TEXT = (56, 74, 12)
COLOR_BRIGHT_SCORE_TEXT = (180, 230, 120)  # Even brighter green for HUD text
COLOR_HUD_BG = (40, 50, 10)

# --- File Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHICS_DIR = os.path.join(BASE_DIR, "Graphics")
SOUND_DIR = os.path.join(BASE_DIR, "Sound")
FONT_DIR = os.path.join(BASE_DIR, "Font")
DATABASE_DIR = os.path.join(BASE_DIR, "Database")
DB_FILE = os.path.join(DATABASE_DIR, "players_names.db")

# --- Game Settings ---
DEFAULT_PLAYER_NAME = "Player"

# --- Difficulty Settings ---
# speed: snake update interval (ms)
# obstacle_speed: wall change interval (ms) / or speed of moving obstacles if implemented
# apple_total_life: total time good apple exists before expiring (ms)
# apple_warning_time: time before expiry when apple turns yellow (ms)
# cell_number: grid size

DIFFICULTY_SETTINGS = {
    "Easy": {
        "base_speed": 250,  # Snake moves slower
        "obstacle_speed_factor": 1.2, # Obstacles (wall changes) are slower
        "apple_expiry_enabled": False,
        "apple_total_life": float('inf'), # Effectively no expiry
        "apple_warning_time": float('inf'),
        "poison_apple_life": 5000,  # 5 seconds for poisonous apples
        "cell_number": 20,
    },
    "Moderate": {
        "base_speed": 200, # Normal speed
        "obstacle_speed_factor": 1.0, # Normal obstacle speed
        "apple_expiry_enabled": True,
        "apple_total_life": 15000, # 15 seconds
        "apple_warning_time": 5000,  # Warn 5 seconds before expiry
        "poison_apple_life": 3500,  # 3.5 seconds for poisonous apples
        "cell_number": 25,
    },
    "Hard": {
        "base_speed": 150, # Snake moves faster
        "obstacle_speed_factor": 0.8, # Obstacles (wall changes) are faster
        "apple_expiry_enabled": True,
        "apple_total_life": 10000, # 10 seconds
        "apple_warning_time": 3000,  # Warn 3 seconds before expiry
        "poison_apple_life": 2000,  # 2 seconds for poisonous apples
        "cell_number": 30,
    }
}
DEFAULT_DIFFICULTY = "Moderate"

# --- Level Definitions ---
# target_score: score needed to pass the level
# num_apples: how many apples on screen at a time for this level
# num_obstacles: how many wall segments for this level
# apple_spawn_delay: time in ms between apple spawns (if one is eaten/despawns)
LEVEL_CONFIG = {
    "Easy": [
        {"level": 1, "target_score": 5,  "num_apples": 1, "num_obstacles": 0, "apple_spawn_delay": 500},
        {"level": 2, "target_score": 10, "num_apples": 1, "num_obstacles": 3, "apple_spawn_delay": 500},
        {"level": 3, "target_score": 15, "num_apples": 2, "num_obstacles": 5, "apple_spawn_delay": 700},
        {"level": 4, "target_score": 20, "num_apples": 2, "num_obstacles": 7, "apple_spawn_delay": 700},
        {"level": 5, "target_score": 25, "num_apples": 3, "num_obstacles": 10, "apple_spawn_delay": 1000},
    ],
    "Moderate": [
        {"level": 1, "target_score": 10, "num_apples": 1, "num_obstacles": 0, "apple_spawn_delay": 500},
        {"level": 2, "target_score": 20, "num_apples": 1, "num_obstacles": 3, "apple_spawn_delay": 500},
        {"level": 3, "target_score": 30, "num_apples": 2, "num_obstacles": 5, "apple_spawn_delay": 700},
        {"level": 4, "target_score": 40, "num_apples": 2, "num_obstacles": 7, "apple_spawn_delay": 700},
        {"level": 5, "target_score": 50, "num_apples": 3, "num_obstacles": 10, "apple_spawn_delay": 1000},
    ],
    "Hard": [
        {"level": 1, "target_score": 15, "num_apples": 1, "num_obstacles": 0, "apple_spawn_delay": 500},
        {"level": 2, "target_score": 25, "num_apples": 1, "num_obstacles": 3, "apple_spawn_delay": 500},
        {"level": 3, "target_score": 40, "num_apples": 2, "num_obstacles": 5, "apple_spawn_delay": 600},
        {"level": 4, "target_score": 55, "num_apples": 2, "num_obstacles": 7, "apple_spawn_delay": 600},
        {"level": 5, "target_score": 70, "num_apples": 3, "num_obstacles": 10, "apple_spawn_delay": 800},
    ],
}

# --- Game State Enum ---
from enum import Enum, auto
class GameState(Enum):
    NAME_INPUT = auto()
    WELCOME = auto()
    MAIN_MENU = auto()
    OPTIONS_MENU = auto()
    CHANGE_NAME = auto()
    DIFFICULTY_SELECT = auto()
    LEVEL_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_TRANSITION = auto()
    GAME_OVER = auto()
    GAME_COMPLETED = auto()
    QUITTING = auto()

# --- Background Tile Definitions for Levels (using world_tileset.png) ---
# (tile_col, tile_row) from the tileset image. Assumed 16x16 tiles.
# You might need to adjust these coordinates by inspecting world_tileset.png
LEVEL_BG_TILES = {
    # Each level can have a primary fill tile and an alternative for checkerboard
    1: {"primary": (0, 0), "secondary": (1, 0), "fill_color": (175, 215, 70)}, # Grass
    2: {"primary": (0, 1), "secondary": (1, 1), "fill_color": (220, 200, 150)}, # Sand
    3: {"primary": (3, 1), "secondary": (4, 1), "fill_color": (210, 150, 170)}, # Pink stone
    4: {"primary": (8, 0), "secondary": (7, 0), "fill_color": (150, 150, 160)}, # Grey stone
    5: {"primary": (4, 0), "secondary": (5, 0), "fill_color": (160, 190, 220)}, # Blue/Ice
}
# Default fill color if tiles are missing or for gaps
DEFAULT_BG_FILL_COLOR = COLOR_DARK_GREEN

# --- Snake Sprite Definitions (from Snake.png) ---
# These are VERY LIKELY to need adjustment. (x, y, width, height) in Snake.png
# Assuming a 16px grid for Snake.png and picking the GREEN snake.
# Example: (col * 16, row * 16, 16, 16)
SNAKE_SPRITE_SHEET = "Snake.png"
SNAKE_TILE_SIZE = 16 # Base size of a tile in Snake.png

# --- Apple Tile Definitions (from world_tileset.png) ---
# (tile_col, tile_row)
APPLE_TILE_COORDS = {
    "good": pygame.Rect(0 * SNAKE_TILE_SIZE, 21 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),      # Red apple
    "warning": pygame.Rect(2 * SNAKE_TILE_SIZE, 21 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),   # Yellow apple (for expiring)
    "poisonous": pygame.Rect(1 * SNAKE_TILE_SIZE, 21 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Green apple
}
POISON_APPLE_CHANCE = 0.15 # 15% chance a new apple is poisonous (if not good/warning)
APPLE_VISUAL_SCALE_FACTOR = 1.4 # Apples will be drawn 20% larger than cell_size

# Coordinates for GREEN snake parts (approximate, PLEASE VERIFY AND ADJUST)
# Format: pygame.Rect(x, y, width, height)
# These might need to be larger than SNAKE_TILE_SIZE if a part spans multiple tiles.
# For simplicity, assuming single 16x16 tiles for now, scaled up later.
SNAKE_GRAPHICS_COORDS = {
    "yellow": {
        "head_up":    pygame.Rect(6 * SNAKE_TILE_SIZE, 3 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),
        "head_down":  pygame.Rect(6 * SNAKE_TILE_SIZE, 5 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Might need to rotate head_up or find specific sprite
        "head_right": pygame.Rect(6 * SNAKE_TILE_SIZE, 6 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),
        "head_left":  pygame.Rect(6 * SNAKE_TILE_SIZE, 4 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),

        "tail_up":    pygame.Rect(8 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_down":  pygame.Rect(6 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_right": pygame.Rect(7 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_left":  pygame.Rect(9 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx

        "body_vertical": pygame.Rect(0 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "body_horizontal": pygame.Rect(1 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx

        "body_tr": pygame.Rect(2 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Top-Right Turn
        "body_tl": pygame.Rect(3 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Top-Left Turn (might be body_bl looking)
        "body_br": pygame.Rect(4 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Bottom-Right Turn
        "body_bl": pygame.Rect(5 * SNAKE_TILE_SIZE, 2 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Bottom-Left Turn
    },
    "green": {
        "head_up":    pygame.Rect(6 * SNAKE_TILE_SIZE, 10 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),
        "head_down":  pygame.Rect(6 * SNAKE_TILE_SIZE, 12 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),
        "head_right": pygame.Rect(6 * SNAKE_TILE_SIZE, 13 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),
        "head_left":  pygame.Rect(6 * SNAKE_TILE_SIZE, 11 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),

        "tail_up":    pygame.Rect(8 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_down":  pygame.Rect(6 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_right": pygame.Rect(7 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_left":  pygame.Rect(9 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx

        "body_vertical": pygame.Rect(0 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "body_horizontal": pygame.Rect(1 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx

        "body_tr": pygame.Rect(2 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Top-Right Turn
        "body_tl": pygame.Rect(3 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Top-Left Turn (might be body_bl looking)
        "body_br": pygame.Rect(4 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Bottom-Right Turn
        "body_bl": pygame.Rect(5 * SNAKE_TILE_SIZE, 9 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Bottom-Left Turn
    },
    "blue": {
        "head_up":    pygame.Rect(6 * SNAKE_TILE_SIZE, 17 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),
        "head_down":  pygame.Rect(6 * SNAKE_TILE_SIZE, 19 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Might need to rotate head_up or find specific sprite
        "head_right": pygame.Rect(6 * SNAKE_TILE_SIZE, 20 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),
        "head_left":  pygame.Rect(6 * SNAKE_TILE_SIZE, 18 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE),

        "tail_up":    pygame.Rect(8 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_down":  pygame.Rect(6 * SNAKE_TILE_SIZE, 16* SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_right": pygame.Rect(7 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "tail_left":  pygame.Rect(9 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx

        "body_vertical": pygame.Rect(0 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx
        "body_horizontal": pygame.Rect(1 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Approx

        "body_tr": pygame.Rect(2 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Top-Right Turn
        "body_tl": pygame.Rect(3 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Top-Left Turn (might be body_bl looking)
        "body_br": pygame.Rect(4 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Bottom-Right Turn
        "body_bl": pygame.Rect(5 * SNAKE_TILE_SIZE, 16 * SNAKE_TILE_SIZE, SNAKE_TILE_SIZE, SNAKE_TILE_SIZE), # Bottom-Left Turn
    }
    # Add "yellow", "blue" if you want to support other snake colors from the sheet
}
SNAKE_COLORS_AVAILABLE = list(SNAKE_GRAPHICS_COORDS.keys()) # Define available colors
DEFAULT_SNAKE_COLOR = "green"