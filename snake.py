import pygame
import sys
import random
import time
import sqlite3
import os
from pygame.math import Vector2
from PIL import Image, ImageSequence
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum, auto

# --- Constants ---
CELL_SIZE = 40
CELL_NUMBER = 20
SCREEN_WIDTH = CELL_NUMBER * CELL_SIZE
SCREEN_HEIGHT = CELL_NUMBER * CELL_SIZE

# Colors (Consider defining more if needed)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_DARK_GREEN = (56, 74, 12)
COLOR_LIGHT_GREEN = (167, 209, 61)
COLOR_GRASS_1 = (175, 215, 70) # Main background
COLOR_GRASS_2 = (167, 209, 61) # Checkered grass
COLOR_BUTTON_NORMAL = (56, 74, 12)
COLOR_BUTTON_HOVER = (76, 94, 32)
COLOR_BUTTON_BACK_NORMAL = (150, 30, 30)
COLOR_BUTTON_BACK_HOVER = (170, 50, 50)
COLOR_TEXT_INPUT_INACTIVE = (100, 100, 100)
COLOR_TEXT_INPUT_ACTIVE = (0, 120, 215)
COLOR_SCORE_TEXT = (56, 74, 12)

# File Paths (Ensure these directories/files exist)
GRAPHICS_DIR = "Graphics"
SOUND_DIR = "Sound"
FONT_DIR = "Font"
DATABASE_DIR = "Database"
DB_FILE = os.path.join(DATABASE_DIR, "players_names.db")

# Game Settings
DEFAULT_DIFFICULTY = "Medium"
LEVELS = {
    "Easy": [
        {"level": 1, "target": 5, "bonus": 5},
        {"level": 2, "target": 10, "bonus": 10},
        {"level": 3, "target": 15, "bonus": 15},
        {"level": 4, "target": 20, "bonus": 20},
        {"level": 5, "target": 25, "bonus": 25},
    ],
    "Medium": [
        {"level": 1, "target": 10, "bonus": 10},
        {"level": 2, "target": 20, "bonus": 15},
        {"level": 3, "target": 30, "bonus": 20},
        {"level": 4, "target": 40, "bonus": 25},
        {"level": 5, "target": 50, "bonus": 30},
    ],
    "Hard": [
        {"level": 1, "target": 15, "bonus": 15},
        {"level": 2, "target": 25, "bonus": 20},
        {"level": 3, "target": 40, "bonus": 25},
        {"level": 4, "target": 55, "bonus": 30},
        {"level": 5, "target": 70, "bonus": 35},
    ],
}

DIFFICULTY_SETTINGS = {
    "Easy": {
        "speed": 200, "wall_count": (3, 5), "wall_change_time": float('inf'),
        "apple_poison_time": float('inf')
    },
    "Medium": {
        "speed": 150, "wall_count": (5, 7), "wall_change_time": 10000,
        "apple_poison_time": 10000
    },
    "Hard": {
        "speed": 100, "wall_count": (7, 9), "wall_change_time": 5000,
        "apple_poison_time": 5000
    }
}

# Game State Enum
class GameState(Enum):
    NAME_INPUT = auto()
    WELCOME = auto()
    MAIN_MENU = auto()
    OPTIONS_MENU = auto() # Added
    CHANGE_NAME = auto() # Added
    DIFFICULTY_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto() # Added
    LEVEL_TRANSITION = auto()
    GAME_OVER = auto()
    GAME_COMPLETED = auto()
    QUITTING = auto()

# --- Asset Loading Helpers ---
def load_image(filename: str, alpha: bool = True, scale: Optional[Tuple[int, int]] = None) -> pygame.Surface:
    """Loads an image, optionally converts alpha and scales."""
    try:
        image = pygame.image.load(os.path.join(GRAPHICS_DIR, filename))
        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except pygame.error as e:
        print(f"Error loading image {filename}: {e}")
        sys.exit()
    except FileNotFoundError:
        print(f"Error: Graphics file not found: {filename}")
        sys.exit()

def load_sound(filename: str) -> pygame.mixer.Sound:
    """Loads a sound file."""
    try:
        return pygame.mixer.Sound(os.path.join(SOUND_DIR, filename))
    except pygame.error as e:
        print(f"Error loading sound {filename}: {e}")
        sys.exit()
    except FileNotFoundError:
        print(f"Error: Sound file not found: {filename}")
        sys.exit()

def load_font(filename: str, size: int) -> pygame.font.Font:
    """Loads a font file."""
    try:
        return pygame.font.Font(os.path.join(FONT_DIR, filename), size)
    except pygame.error as e:
        print(f"Error loading font {filename}: {e}")
        sys.exit()
    except FileNotFoundError:
        print(f"Error: Font file not found: {filename}")
        sys.exit()

def load_gif_frames(filename: str, scale: Tuple[int, int]) -> List[pygame.Surface]:
    """Loads frames from a GIF, scales them, and converts to Pygame surfaces."""
    try:
        with Image.open(os.path.join(GRAPHICS_DIR, filename)) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                # Convert frame to RGBA to handle transparency properly
                frame_rgba = frame.convert("RGBA")
                pygame_frame = pygame.image.fromstring(
                    frame_rgba.tobytes(), frame_rgba.size, "RGBA"
                )
                scaled_frame = pygame.transform.scale(pygame_frame, scale)
                frames.append(scaled_frame)
            return frames
    except FileNotFoundError:
        print(f"Error: GIF file not found: {filename}")
        sys.exit()
    except Exception as e:
        print(f"Error processing GIF {filename}: {e}")
        sys.exit()


# --- Database Class ---
class PlayerDatabase:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self._initialize_db()

    def _execute(self, query: str, params: tuple = ()):
        """Executes a query with connection handling."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            # Decide how to handle DB errors, maybe raise an exception
            return None # Or raise custom exception

    def _initialize_db(self):
        create_table_query = """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                high_score INTEGER DEFAULT 0,
                difficulty TEXT,
                highest_level INTEGER DEFAULT 1,
                games_played INTEGER DEFAULT 0,
                last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self._execute(create_table_query)
        # Add an index on name for faster lookups
        self._execute("CREATE INDEX IF NOT EXISTS idx_player_name ON players (name);")


    def add_player(self, name: str) -> Optional[int]:
        """Add a new player or return existing player ID. Returns None on error."""
        name = name.strip()
        if not name:
            return None

        select_query = "SELECT id FROM players WHERE name = ?"
        insert_query = "INSERT OR IGNORE INTO players (name) VALUES (?)" # Use OR IGNORE for atomicity

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                # Try inserting first (handles new players)
                cursor.execute(insert_query, (name,))
                conn.commit()

                # Then select the ID (works for new and existing players)
                cursor.execute(select_query, (name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error in add_player: {e}")
            return None

    def update_player_name(self, player_id: int, new_name: str) -> bool:
        """Updates the name for a given player ID. Ensures uniqueness. Returns True on success."""
        new_name = new_name.strip()
        if not new_name or player_id is None:
            return False

        update_query = "UPDATE players SET name = ? WHERE id = ?"
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(update_query, (new_name, player_id))
                conn.commit()
                # Check if any row was actually updated
                return conn.total_changes > 0
        except sqlite3.IntegrityError:
            # This likely means the new name is already taken (due to UNIQUE constraint)
            print(f"Database IntegrityError: Name '{new_name}' might already exist.")
            return False
        except sqlite3.Error as e:
            print(f"Database error in update_player_name: {e}")
            return False

    def update_player_score(self, player_id: int, score: int, difficulty: str, level: int):
        update_query = """
            UPDATE players SET
            games_played = games_played + 1,
            last_played = CURRENT_TIMESTAMP,
            difficulty = ?,
            highest_level = MAX(highest_level, ?),
            high_score = MAX(high_score, ?)
            WHERE id = ?
        """
        self._execute(update_query, (difficulty, level, score, player_id))

    def get_top_players(self, limit: int = 10) -> List[Dict[str, Any]]:
        select_query = """
            SELECT name, high_score, difficulty, highest_level
            FROM players
            ORDER BY high_score DESC
            LIMIT ?
        """
        cursor = self._execute(select_query, (limit,))
        if cursor:
            top_players = [
                {"name": row[0], "high_score": row[1], "difficulty": row[2], "highest_level": row[3]}
                for row in cursor.fetchall()
            ]
            return top_players
        return []


# --- UI Element Classes ---
class TextInput:
    def __init__(self, x: int, y: int, width: int, height: int,
                 font: pygame.font.Font, max_chars: int = 20,
                 text_color=COLOR_BLACK, inactive_color=COLOR_TEXT_INPUT_INACTIVE,
                 active_color=COLOR_TEXT_INPUT_ACTIVE, bg_color=COLOR_WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.max_chars = max_chars
        self.text = ""
        self.active = False
        self.text_color = text_color
        self.color_inactive = inactive_color
        self.color_active = active_color
        self.bg_color = bg_color
        self.color = self.color_inactive
        self.cursor_visible = True
        self.cursor_timer = 0
        self.blink_speed = 500  # milliseconds

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handles events for the text input. Returns True if Enter key is pressed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
            # Reset cursor blink on activation
            if self.active:
                self.cursor_timer = pygame.time.get_ticks()
                self.cursor_visible = True

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True  # Signal submission
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < self.max_chars and event.unicode.isprintable():
                self.text += event.unicode
        return False

    def update(self):
        """Updates the cursor blinking state."""
        if self.active:
            current_time = pygame.time.get_ticks()
            if current_time - self.cursor_timer > self.blink_speed:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = current_time

    def draw(self, screen: pygame.Surface):
        """Draws the text input box."""
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2) # Border

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 5, self.rect.centery))
        screen.blit(text_surface, text_rect)

        if self.active and self.cursor_visible:
            cursor_pos_x = text_rect.right + 1 # Position cursor after text
            cursor_y1 = text_rect.top
            cursor_y2 = text_rect.bottom
            pygame.draw.line(screen, self.text_color, (cursor_pos_x, cursor_y1), (cursor_pos_x, cursor_y2), 2)

    def get_text(self) -> str:
        return self.text.strip()


class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font,
                 color: Tuple[int, int, int], hover_color: Tuple[int, int, int],
                 text_color: Tuple[int, int, int] = COLOR_WHITE, border_radius: int = 12):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.is_hovered = False
        self._render_text() # Initial text rendering

    def _render_text(self):
        """Renders the text surface and centers it."""
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, screen: pygame.Surface):
        """Draws the button."""
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=self.border_radius)
        # Optional border
        pygame.draw.rect(screen, self.text_color, self.rect, 3, border_radius=self.border_radius)
        screen.blit(self.text_surf, self.text_rect)

    def check_hover(self, mouse_pos: Tuple[int, int]):
        """Updates the hover state based on mouse position."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Checks if the button was clicked in a MOUSEBUTTONDOWN event."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

class Tileset:
    def __init__(self, filename: str, tile_width: int, tile_height: int, scale_to: Tuple[int, int]):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.scale_to = scale_to
        try:
            self.image = pygame.image.load(os.path.join(GRAPHICS_DIR, filename)).convert_alpha()
        except pygame.error as e:
            print(f"Error loading tileset {filename}: {e}")
            sys.exit()
        except FileNotFoundError:
             print(f"Error: Tileset file not found: {filename}")
             sys.exit()

        self.cols = self.image.get_width() // tile_width
        self.rows = self.image.get_height() // tile_height
        self._cache = {} # Cache scaled tiles

    def get_tile(self, tile_x: int, tile_y: int) -> Optional[pygame.Surface]:
        """Extracts and scales a single tile from the tileset. Uses caching."""
        if not (0 <= tile_x < self.cols and 0 <= tile_y < self.rows):
            print(f"Warning: Tile coordinates ({tile_x}, {tile_y}) out of bounds.")
            return None

        cache_key = (tile_x, tile_y)
        if cache_key in self._cache:
            return self._cache[cache_key]

        rect = pygame.Rect(tile_x * self.tile_width, tile_y * self.tile_height,
                           self.tile_width, self.tile_height)
        tile_image = self.image.subsurface(rect)
        scaled_tile = pygame.transform.scale(tile_image, self.scale_to)
        self._cache[cache_key] = scaled_tile # Store in cache
        return scaled_tile

# --- Game Object Classes ---
class Snake:
    def __init__(self, cell_size: int):
        self.cell_size = cell_size
        self.body: List[Vector2] = []
        self.direction: Vector2 = Vector2(0, 0)
        self.new_block: bool = False
        self._load_assets()
        self.reset() # Initialize body and direction

    def _load_assets(self):
        scale = (self.cell_size, self.cell_size)
        self.head_up = load_image('head_up.png', scale=scale)
        self.head_down = load_image('head_down.png', scale=scale)
        self.head_right = load_image('head_right.png', scale=scale)
        self.head_left = load_image('head_left.png', scale=scale)

        self.tail_up = load_image('tail_up.png', scale=scale)
        self.tail_down = load_image('tail_down.png', scale=scale)
        self.tail_right = load_image('tail_right.png', scale=scale)
        self.tail_left = load_image('tail_left.png', scale=scale)

        self.body_vertical = load_image('body_vertical.png', scale=scale)
        self.body_horizontal = load_image('body_horizontal.png', scale=scale)

        self.body_tr = load_image('body_tr.png', scale=scale)
        self.body_tl = load_image('body_tl.png', scale=scale)
        self.body_br = load_image('body_br.png', scale=scale)
        self.body_bl = load_image('body_bl.png', scale=scale)

        self.crunch_sound = load_sound('crunch.wav')

    def draw(self, screen: pygame.Surface):
        self._update_head_graphics()
        self._update_tail_graphics()

        for index, block in enumerate(self.body):
            x_pos = int(block.x * self.cell_size)
            y_pos = int(block.y * self.cell_size)
            block_rect = pygame.Rect(x_pos, y_pos, self.cell_size, self.cell_size)

            if index == 0:
                screen.blit(self.head, block_rect)
            elif index == len(self.body) - 1:
                screen.blit(self.tail, block_rect)
            else:
                # Determine body part orientation
                prev_block_rel = self.body[index + 1] - block
                next_block_rel = self.body[index - 1] - block
                if prev_block_rel.x == next_block_rel.x: # Vertical
                    screen.blit(self.body_vertical, block_rect)
                elif prev_block_rel.y == next_block_rel.y: # Horizontal
                    screen.blit(self.body_horizontal, block_rect)
                else: # Corner piece
                    if (prev_block_rel.x == -1 and next_block_rel.y == -1) or \
                       (prev_block_rel.y == -1 and next_block_rel.x == -1):
                        screen.blit(self.body_tl, block_rect)
                    elif (prev_block_rel.x == -1 and next_block_rel.y == 1) or \
                         (prev_block_rel.y == 1 and next_block_rel.x == -1):
                        screen.blit(self.body_bl, block_rect)
                    elif (prev_block_rel.x == 1 and next_block_rel.y == -1) or \
                         (prev_block_rel.y == -1 and next_block_rel.x == 1):
                        screen.blit(self.body_tr, block_rect)
                    elif (prev_block_rel.x == 1 and next_block_rel.y == 1) or \
                         (prev_block_rel.y == 1 and next_block_rel.x == 1):
                        screen.blit(self.body_br, block_rect)

    def _update_head_graphics(self):
        if len(self.body) < 2: # Avoid index error if snake is very short
             self.head = self.head_right # Default
             return
        head_relation = self.body[1] - self.body[0]
        if head_relation == Vector2(1, 0): self.head = self.head_left
        elif head_relation == Vector2(-1, 0): self.head = self.head_right
        elif head_relation == Vector2(0, 1): self.head = self.head_up
        elif head_relation == Vector2(0, -1): self.head = self.head_down

    def _update_tail_graphics(self):
        if len(self.body) < 2:
             self.tail = self.tail_left # Default
             return
        tail_relation = self.body[-2] - self.body[-1]
        if tail_relation == Vector2(1, 0): self.tail = self.tail_left
        elif tail_relation == Vector2(-1, 0): self.tail = self.tail_right
        elif tail_relation == Vector2(0, 1): self.tail = self.tail_up
        elif tail_relation == Vector2(0, -1): self.tail = self.tail_down

    def move(self):
        if self.direction == Vector2(0, 0): # Don't move if no direction set (e.g., at start)
            return
        if self.new_block:
            body_copy = self.body[:] # Important: copy the list
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy
            self.new_block = False
        else:
            body_copy = self.body[:-1] # Copy all except the last element
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy

    def add_block(self):
        self.new_block = True

    def play_crunch_sound(self):
        self.crunch_sound.play()

    def reset(self):
        # Initial position and direction when game starts or resets
        self.body = [Vector2(5, 10), Vector2(4, 10), Vector2(3, 10)]
        self.direction = Vector2(0, 0) # Start stationary
        self.new_block = False
        self._update_head_graphics() # Set initial head/tail
        self._update_tail_graphics()


class Fruit:
    def __init__(self, cell_number: int, cell_size: int):
        self.cell_number = cell_number
        self.cell_size = cell_size
        self.pos = Vector2(0, 0) # Initial dummy position
        self.apple_image = load_image('apple.png', scale=(cell_size, cell_size))
        self.poison_apple_image = load_image('poison_apple.png', scale=(cell_size, cell_size))
        self.is_poisonous = False
        self.randomize([], []) # Initial placement

    def draw(self, screen: pygame.Surface):
        fruit_rect = pygame.Rect(
            int(self.pos.x * self.cell_size),
            int(self.pos.y * self.cell_size),
            self.cell_size, self.cell_size
        )
        image = self.poison_apple_image if self.is_poisonous else self.apple_image
        screen.blit(image, fruit_rect)

    def randomize(self, snake_body: List[Vector2], wall_positions: List[Vector2]):
        """Finds a new random position not occupied by the snake or walls."""
        while True:
            x = random.randint(0, self.cell_number - 1)
            y = random.randint(0, self.cell_number - 1)
            self.pos = Vector2(x, y)
            if self.pos not in snake_body and self.pos not in wall_positions:
                break
        self.is_poisonous = False # New fruit is never poisonous initially


class Wall:
    def __init__(self, cell_number: int, cell_size: int):
        self.cell_number = cell_number
        self.cell_size = cell_size
        self.positions: List[Vector2] = []
        self.image = load_image('wall.PNG', scale=(cell_size, cell_size))

    def generate(self, min_walls: int, max_walls: int, snake_body: List[Vector2], fruit_pos: Vector2):
        """Generates a new set of wall positions."""
        self.positions.clear()
        num_walls = random.randint(min_walls, max_walls)

        for _ in range(num_walls):
            wall_pos = self._get_unique_position(snake_body, fruit_pos)
            if wall_pos: # Check if a valid position was found
                 self.positions.append(wall_pos)

    def _get_unique_position(self, snake_body: List[Vector2], fruit_pos: Vector2) -> Optional[Vector2]:
        """Tries to find a unique position for a wall segment."""
        max_attempts = self.cell_number * self.cell_number # Max possible positions
        for _ in range(max_attempts):
            x = random.randint(0, self.cell_number - 1)
            y = random.randint(0, self.cell_number - 1)
            new_pos = Vector2(x, y)

            # Ensure wall is not too close to initial snake head or fruit
            is_near_snake_head = len(snake_body) > 0 and (new_pos - snake_body[0]).length() < 3
            is_near_fruit = (new_pos - fruit_pos).length() < 2

            if (new_pos not in snake_body and
                new_pos != fruit_pos and
                new_pos not in self.positions and
                not is_near_snake_head and
                not is_near_fruit):
                return new_pos
        print("Warning: Could not find unique position for wall segment after max attempts.")
        return None # Indicate failure to find a spot

    def draw(self, screen: pygame.Surface):
        """Draws all wall segments."""
        for pos in self.positions:
            wall_rect = pygame.Rect(
                int(pos.x * self.cell_size), int(pos.y * self.cell_size),
                self.cell_size, self.cell_size
            )
            screen.blit(self.image, wall_rect)


class LevelManager:
    def __init__(self, levels_data: Dict[str, List[Dict]]):
        self.levels_data = levels_data
        self.difficulty = DEFAULT_DIFFICULTY
        self.current_level_index = 0
        self.completed_levels: Dict[str, List[bool]] = {diff: [False] * len(levels) for diff, levels in levels_data.items()}

    def set_difficulty(self, difficulty: str):
        if difficulty in self.levels_data:
            self.difficulty = difficulty
            self.current_level_index = 0 # Reset level progress on difficulty change

    def get_current_level(self) -> Dict:
        return self.levels_data[self.difficulty][self.current_level_index]

    def get_level_number(self) -> int:
        return self.get_current_level()["level"]

    def get_target_score(self) -> int:
        return self.get_current_level()["target"]

    def is_level_complete(self, score: int) -> bool:
        return score >= self.get_target_score()

    def mark_level_complete(self):
        self.completed_levels[self.difficulty][self.current_level_index] = True

    def advance_level(self) -> bool:
        """Advances to the next level if possible. Returns True if successful, False if last level."""
        if self.current_level_index < len(self.levels_data[self.difficulty]) - 1:
            self.current_level_index += 1
            return True
        return False

    def reset_progress(self):
        """Resets level progress for the current difficulty."""
        self.current_level_index = 0
        self.completed_levels[self.difficulty] = [False] * len(self.levels_data[self.difficulty])

    def is_game_complete(self) -> bool:
        """Checks if the last level of the current difficulty is completed."""
        return self.current_level_index == len(self.levels_data[self.difficulty]) - 1 and \
               self.completed_levels[self.difficulty][self.current_level_index]


# --- Main Game Class ---
class Game:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        self.screen = screen
        self.clock = clock
        self.cell_size = CELL_SIZE
        self.cell_number = CELL_NUMBER

        # Fonts
        self.ui_font = load_font('dpcomic.ttf', 30)
        self.title_font = load_font('dpcomic.ttf', 50)
        self.score_font = load_font('PoetsenOne-Regular.ttf', 25)

        # Game Objects
        self.snake = Snake(self.cell_size)
        self.fruit = Fruit(self.cell_number, self.cell_size)
        self.wall = Wall(self.cell_number, self.cell_size)
        self.player_db = PlayerDatabase()
        self.level_manager = LevelManager(LEVELS)

        # Game State
        self.game_state = GameState.NAME_INPUT
        self.difficulty = DEFAULT_DIFFICULTY
        self.settings = DIFFICULTY_SETTINGS[self.difficulty]
        self.score = 0
        self.player_name = ""
        self.player_id: Optional[int] = None

        # Timers
        self.last_wall_change_time = 0
        self.last_apple_poison_time = 0
        self.state_transition_time = 0 # For delays like welcome screen, level transition
        self.welcome_duration = 2000
        self.level_transition_duration = 3000

        # Pygame Event Timer
        self.SCREEN_UPDATE = pygame.USEREVENT + 1 # Use +1 to avoid conflict with default USEREVENT
        self._update_game_timer()

        # --- Load Tileset ---
        self.world_tileset = Tileset(
             filename="world_tileset.png", # From uploaded file
             tile_width=16,  # Estimated tile size from image
             tile_height=16, # Estimated tile size from image
             scale_to=(self.cell_size, self.cell_size) # Scale to game cell size
        )

        # --- Define Level Background Tiles (Using tile X, Y coordinates) ---
        # Adjust these coordinates based on the actual tileset layout
        self.level_bg_tiles = {
            1: [(0, 0), (1, 0)],  # Level 1: Two types of grass tiles (top-left)
            2: [(0, 1), (1, 1)],  # Level 2: Two types of sand tiles
            3: [(3, 1), (4, 1)],  # Level 3: Two types of pink stone tiles
            4: [(6, 0), (7, 0)],  # Level 4: Two types of grey stone tiles
            5: [(4, 0), (5, 0)],  # Level 5: Two types of blue/ice tiles
            # Add more levels or default if needed
        }

        # Assets (Loaded here or within specific objects)
        # self.grass_image_1 = load_image("grass1.png", alpha=False, scale=(self.cell_size, self.cell_size))
        # self.grass_image_2 = load_image("grass2.png", alpha=False, scale=(self.cell_size, self.cell_size))
        self.main_menu_frames = load_gif_frames("main_menu_bg.gif", scale=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.current_frame_index = 0
        self.apple_score_icon = load_image('apple.png', scale=(self.score_font.get_height(), self.score_font.get_height()))


        # UI Elements (Initialize common ones)
        self._initialize_ui_elements()


    def _initialize_ui_elements(self):
        """Initializes UI elements used across different states."""
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        button_width = 200
        button_height = 60
        vertical_spacing = 20
        input_width = 300
        input_height = 50
        options_button_width = 250

        # Name Input
        self.name_input = TextInput(
            center_x - input_width // 2, center_y - input_height // 2,
            input_width, input_height, self.ui_font, 15
        )
        self.submit_name_button = Button(
            center_x - button_width // 2, center_y + 50,
            button_width, button_height, "SUBMIT", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )

        # Main Menu
        self.play_button = Button(
            center_x - button_width // 2, center_y - button_height - vertical_spacing // 2,
            button_width, button_height, "PLAY", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )
        self.options_button = Button(
            center_x - button_width // 2, center_y, # Center Y
            button_width, button_height, "OPTIONS", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )
        self.quit_button = Button(
            center_x - button_width // 2, center_y + button_height + vertical_spacing // 2,
            button_width, button_height, "QUIT", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )

        # --- Options Menu Buttons ---
        self.change_name_button = Button(
            center_x - options_button_width // 2, center_y - 30,
            options_button_width, button_height, "Change Player Name", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )
        # Use existing back_button design/colors maybe?
        self.options_back_button = Button(
            center_x - options_button_width // 2, center_y + button_height,
            options_button_width, button_height, "Back to Main Menu", self.ui_font,
            COLOR_BUTTON_BACK_NORMAL, COLOR_BUTTON_BACK_HOVER
        )

        # --- Change Name Screen Elements ---
        self.submit_new_name_button = Button(
            center_x - button_width // 2, center_y + 50,
            button_width, button_height, "SUBMIT", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )
        self.cancel_name_change_button = Button(
            center_x - button_width // 2, center_y + button_height + 50 + vertical_spacing,
            button_width, button_height, "CANCEL", self.ui_font,
            COLOR_BUTTON_BACK_NORMAL, COLOR_BUTTON_BACK_HOVER
        )

        # Difficulty Select
        diff_button_width = 160
        diff_button_height = 50
        diff_y_start = center_y - 60
        self.diff_buttons = [
            Button(
                center_x - diff_button_width // 2,
                diff_y_start + i * (diff_button_height + 15),
                diff_button_width, diff_button_height, diff, self.ui_font,
                COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
            ) for i, diff in enumerate(["Easy", "Medium", "Hard"])
        ]
        self.back_button = Button(
            center_x - diff_button_width // 2,
            diff_y_start + 3 * (diff_button_height + 15),
            diff_button_width, diff_button_height, "Back", self.ui_font,
            COLOR_BUTTON_BACK_NORMAL, COLOR_BUTTON_BACK_HOVER
        )

        # Game Over / Level Transition / Game Completed
        self.play_again_button = Button(
            center_x - button_width // 2, center_y + 20,
            button_width, button_height, "PLAY AGAIN", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )
        self.next_level_button = Button(
            center_x - button_width // 2, center_y + 30,
            button_width, button_height, "NEXT LEVEL", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )

        main_menu_y = center_y + 90 + vertical_spacing

        self.main_menu_button = Button(
            center_x - button_width // 2, main_menu_y, # Adjusted position
            button_width, button_height, "MAIN MENU", self.ui_font,
            COLOR_BUTTON_BACK_NORMAL, COLOR_BUTTON_BACK_HOVER
        )

        # Pause 
        self.resume_button = Button(
            center_x - button_width // 2, center_y - button_height // 2 - vertical_spacing // 2,
            button_width, button_height, "RESUME (ESC)", self.ui_font,
            COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER
        )
        self.pause_main_menu_button = Button(
            center_x - button_width // 2, center_y + button_height // 2 + vertical_spacing // 2,
            button_width, button_height, "MAIN MENU", self.ui_font,
            COLOR_BUTTON_BACK_NORMAL, COLOR_BUTTON_BACK_HOVER
        )

        # Title Text (Common for menus)
        self.title_surf = self.title_font.render("Snake Game", True, COLOR_WHITE)
        self.title_rect = self.title_surf.get_rect(center=(center_x, SCREEN_HEIGHT // 4))


    def _update_game_timer(self):
        """Sets the Pygame timer based on current difficulty."""
        pygame.time.set_timer(self.SCREEN_UPDATE, self.settings["speed"])

    def _change_state(self, new_state: GameState):
        """Changes the game state and resets necessary timers/flags."""
        print(f"Changing state from {self.game_state} to {new_state}") # Debugging
        self.game_state = new_state
        self.state_transition_time = pygame.time.get_ticks()
        # Reset things based on state change if needed
        if new_state == GameState.PLAYING:
            self.snake.direction = Vector2(1, 0) # Start moving right
            self.last_wall_change_time = pygame.time.get_ticks()
            self.last_apple_poison_time = pygame.time.get_ticks()
        elif new_state == GameState.MAIN_MENU:
            self.reset_game(reset_player=False) # Keep player logged in

    def run(self):
        """Main game loop."""
        while self.game_state != GameState.QUITTING:
            current_time = pygame.time.get_ticks()
            events = pygame.event.get()
            mouse_pos = pygame.mouse.get_pos()

            # --- Event Handling ---
            for event in events:
                if event.type == pygame.QUIT:
                    self._change_state(GameState.QUITTING)
                    break # Exit event loop

                # Handle events based on state
                if self.game_state == GameState.NAME_INPUT:
                    self._handle_name_input_events(event)
                elif self.game_state == GameState.MAIN_MENU:
                    self._handle_main_menu_events(event)
                elif self.game_state == GameState.OPTIONS_MENU:
                    self._handle_options_menu_events(event)
                elif self.game_state == GameState.CHANGE_NAME:
                    self._handle_change_name_events(event)
                elif self.game_state == GameState.DIFFICULTY_SELECT:
                    self._handle_difficulty_select_events(event)
                elif self.game_state == GameState.PLAYING:
                    self._handle_playing_events(event, current_time)
                elif self.game_state == GameState.PAUSED:
                    self._handle_paused_events(event)
                elif self.game_state == GameState.LEVEL_TRANSITION:
                    self._handle_level_transition_events(event)
                elif self.game_state == GameState.GAME_OVER:
                    self._handle_game_over_events(event)
                elif self.game_state == GameState.GAME_COMPLETED:
                    self._handle_game_completed_events(event)
                # Welcome state is timed, no direct user interaction needed in event loop

            if self.game_state == GameState.QUITTING:
                break

            # --- Updates based on state (outside event loop) ---
            if self.game_state == GameState.NAME_INPUT:
                self.name_input.update()
                self._update_button_hover(mouse_pos, [self.submit_name_button])
            elif self.game_state == GameState.WELCOME:
                if current_time - self.state_transition_time > self.welcome_duration:
                    self._change_state(GameState.MAIN_MENU)
            elif self.game_state == GameState.MAIN_MENU:
                self._update_button_hover(mouse_pos, [self.play_button, self.quit_button])
            elif self.game_state == GameState.OPTIONS_MENU:
                # Update hover state for options menu buttons
                self._update_button_hover(mouse_pos, [self.change_name_button, self.options_back_button])
            elif self.game_state == GameState.CHANGE_NAME:
                self.name_input.update() # Update cursor blink
                self._update_button_hover(mouse_pos, [self.submit_new_name_button, self.cancel_name_change_button])
            elif self.game_state == GameState.DIFFICULTY_SELECT:
                self._update_button_hover(mouse_pos, self.diff_buttons + [self.back_button])
            elif self.game_state == GameState.PAUSED:
                self._update_button_hover(mouse_pos, [self.resume_button, self.pause_main_menu_button])
            elif self.game_state == GameState.LEVEL_TRANSITION:
                self._update_button_hover(mouse_pos, [self.next_level_button, self.main_menu_button])
            elif self.game_state == GameState.GAME_OVER:
                self._update_button_hover(mouse_pos, [self.play_again_button, self.main_menu_button])
            elif self.game_state == GameState.GAME_COMPLETED:
                self._update_button_hover(mouse_pos, [self.main_menu_button])

            # --- Drawing ---
            self.screen.fill(COLOR_GRASS_1) # Default background

            if self.game_state in [GameState.NAME_INPUT, GameState.MAIN_MENU, GameState.DIFFICULTY_SELECT, GameState.WELCOME]:
                self._draw_menu_background()

            if self.game_state == GameState.NAME_INPUT:
                self._draw_name_input_state()
            elif self.game_state == GameState.WELCOME:
                self._draw_welcome_state()
            elif self.game_state == GameState.MAIN_MENU:
                self._draw_main_menu_state()
            elif self.game_state == GameState.OPTIONS_MENU:
                self._draw_options_menu_state()
            elif self.game_state == GameState.CHANGE_NAME:
                self._draw_change_name_state()
            elif self.game_state == GameState.DIFFICULTY_SELECT:
                self._draw_difficulty_select_state()
            elif self.game_state == GameState.PLAYING:
                self._draw_playing_state()
            elif self.game_state == GameState.PAUSED:
                self._draw_paused_state()
            elif self.game_state == GameState.LEVEL_TRANSITION:
                # Draw playing state underneath transition overlay
                self._draw_playing_state(draw_hud=False) # Maybe hide HUD
                self._draw_level_transition_state()
            elif self.game_state == GameState.GAME_OVER:
                # Draw playing state underneath game over overlay
                self._draw_playing_state(draw_hud=False) # Maybe hide HUD
                self._draw_game_over_state()
            elif self.game_state == GameState.GAME_COMPLETED:
                # Draw playing state underneath completion overlay
                self._draw_playing_state(draw_hud=False) # Maybe hide HUD
                self._draw_game_completed_state()

            # --- Display Update ---
            pygame.display.flip() # Use flip instead of update for full screen changes
            self.clock.tick(60) # Cap FPS

        # --- Quit Pygame ---
        pygame.quit()
        sys.exit()

    # --- State-Specific Event Handlers ---
    def _handle_name_input_events(self, event: pygame.event.Event):
        if self.name_input.handle_event(event): # Enter pressed in input
            self._submit_name()
        if self.submit_name_button.is_clicked(event):
            self._submit_name()

    def _handle_main_menu_events(self, event: pygame.event.Event):
        if self.play_button.is_clicked(event):
            self._change_state(GameState.DIFFICULTY_SELECT)
        elif self.options_button.is_clicked(event):
            self._change_state(GameState.OPTIONS_MENU)
        elif self.quit_button.is_clicked(event):
            self._change_state(GameState.QUITTING)

    def _handle_options_menu_events(self, event: pygame.event.Event):
        """Handles events for the OPTIONS_MENU state."""
        # Only allow changing name if logged in
        can_change_name = self.player_id is not None
        if can_change_name and self.change_name_button.is_clicked(event):
            # Clear the input box before showing it for the new name
            self.name_input.text = ""
            self._change_state(GameState.CHANGE_NAME)
        elif self.options_back_button.is_clicked(event):
            self._change_state(GameState.MAIN_MENU)

    def _handle_change_name_events(self, event: pygame.event.Event):
        """Handles events for the CHANGE_NAME state."""
        if self.name_input.handle_event(event): # Enter pressed
            self._try_update_player_name()
        elif self.submit_new_name_button.is_clicked(event):
            self._try_update_player_name()
        elif self.cancel_name_change_button.is_clicked(event):
            # Go back to options menu without changing name
            self._change_state(GameState.OPTIONS_MENU)

    def _handle_difficulty_select_events(self, event: pygame.event.Event):
        for i, button in enumerate(self.diff_buttons):
            if button.is_clicked(event):
                self.difficulty = ["Easy", "Medium", "Hard"][i]
                self.settings = DIFFICULTY_SETTINGS[self.difficulty]
                self.level_manager.set_difficulty(self.difficulty)
                self._update_game_timer()
                self.reset_game(reset_player=False) # Start new game with selected difficulty
                self._change_state(GameState.PLAYING)
                break
        if self.back_button.is_clicked(event):
            self._change_state(GameState.MAIN_MENU)

    def _handle_playing_events(self, event: pygame.event.Event, current_time: int):
        if event.type == self.SCREEN_UPDATE:
            self._update_game_logic(current_time)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._change_state(GameState.PAUSED)
                return
            if event.key == pygame.K_UP and self.snake.direction.y != 1:
                self.snake.direction = Vector2(0, -1)
            elif event.key == pygame.K_DOWN and self.snake.direction.y != -1:
                self.snake.direction = Vector2(0, 1)
            elif event.key == pygame.K_LEFT and self.snake.direction.x != 1:
                self.snake.direction = Vector2(-1, 0)
            elif event.key == pygame.K_RIGHT and self.snake.direction.x != -1:
                self.snake.direction = Vector2(1, 0)
            elif event.key == pygame.K_ESCAPE:
                # Option to pause or go to menu? For now, back to menu
                self._change_state(GameState.MAIN_MENU)
    
    def _handle_paused_events(self, event: pygame.event.Event):
        """Handles events during the PAUSED state."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._change_state(GameState.PLAYING) # Resume
        elif self.resume_button.is_clicked(event):
            self._change_state(GameState.PLAYING) # Resume
        elif self.pause_main_menu_button.is_clicked(event):
            self._change_state(GameState.MAIN_MENU)

    def _handle_level_transition_events(self, event: pygame.event.Event):
        if self.next_level_button.is_clicked(event):
            if self.level_manager.advance_level():
                self.reset_level()
                self._change_state(GameState.PLAYING)
            else:
                # Should have gone to GAME_COMPLETED state before this
                print("Error: Tried to advance beyond last level.")
                self._change_state(GameState.MAIN_MENU) # Fallback
        elif self.main_menu_button.is_clicked(event):
            self._change_state(GameState.MAIN_MENU)

    def _handle_game_over_events(self, event: pygame.event.Event):
        if self.play_again_button.is_clicked(event):
            self.reset_game(reset_player=False) # Keep player, reset game for current difficulty
            self._change_state(GameState.PLAYING)
        elif self.main_menu_button.is_clicked(event):
            self._change_state(GameState.MAIN_MENU)

    def _handle_game_completed_events(self, event: pygame.event.Event):
        if self.main_menu_button.is_clicked(event):
            self._change_state(GameState.MAIN_MENU)

    # --- State-Specific Drawing Methods ---

    def _draw_menu_background(self):
        """Draws the animated GIF background for menus."""
        frame = self.main_menu_frames[self.current_frame_index]
        self.screen.blit(frame, (0, 0))
        self.current_frame_index = (self.current_frame_index + 1) % len(self.main_menu_frames)
        # Draw Title on top
        self.screen.blit(self.title_surf, self.title_rect)


    def _draw_name_input_state(self):
        # Instructions
        inst_font = self.ui_font
        inst_text = inst_font.render("Enter Your Name:", True, COLOR_WHITE)
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(inst_text, inst_rect)
        # Input Box
        self.name_input.draw(self.screen)
        # Submit Button
        self.submit_name_button.draw(self.screen)

    def _draw_welcome_state(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Black overlay with alpha
        self.screen.blit(overlay, (0, 0))
        # Welcome Text
        welcome_text = self.title_font.render(f"Welcome, {self.player_name}!", True, COLOR_YELLOW)
        welcome_rect = welcome_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(welcome_text, welcome_rect)

    def _draw_main_menu_state(self):
        self._draw_menu_background()
        
        self.play_button.draw(self.screen)
        self.options_button.draw(self.screen)
        self.quit_button.draw(self.screen)

    def _draw_options_menu_state(self):
        """Draws the Options Menu screen."""
        self._draw_menu_background() # Reuse animated background

        # Display current player info
        if self.player_name:
            info_text = f"Current Player: {self.player_name}"
        else:
            info_text = "Not Logged In"
        info_surf = self.ui_font.render(info_text, True, COLOR_WHITE)
        info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(info_surf, info_rect)

        # Draw buttons
        # Maybe disable change name button if not logged in? (Visually)
        can_change_name = self.player_id is not None
        # Simple visual disable: change color (implementation depends on Button class)
        # For now, just draw it normally, event handler prevents action.
        self.change_name_button.draw(self.screen)
        self.options_back_button.draw(self.screen)

    def _draw_change_name_state(self):
        """Draws the screen for entering a new player name."""
        self._draw_menu_background()

        # Instructions
        inst_text = self.ui_font.render("Enter New Name:", True, COLOR_WHITE)
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(inst_text, inst_rect)

        # Input Box (reused from name_input)
        self.name_input.draw(self.screen)

        # Buttons
        self.submit_new_name_button.draw(self.screen)
        self.cancel_name_change_button.draw(self.screen)

    def _draw_difficulty_select_state(self):
        diff_text = self.ui_font.render("SELECT DIFFICULTY", True, COLOR_WHITE)
        diff_rect = diff_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(diff_text, diff_rect)
        for button in self.diff_buttons:
            button.draw(self.screen)
        self.back_button.draw(self.screen)

    def _draw_playing_state(self, draw_hud=True):
        # self._draw_grass()
        self._draw_level_background()
        self.wall.draw(self.screen)
        self.fruit.draw(self.screen)
        self.snake.draw(self.screen)
        if draw_hud:
            self._draw_score_hud()

    def _draw_paused_state(self):
        """Draws the PAUSED overlay and buttons."""
        # Draw the underlying playing state first
        self._draw_playing_state(draw_hud=True) # Keep HUD visible

        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Black overlay with alpha
        self.screen.blit(overlay, (0, 0))

        # Draw "PAUSED" text
        paused_text = self.title_font.render("PAUSED", True, COLOR_YELLOW)
        paused_rect = paused_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(paused_text, paused_rect)

        # Draw buttons
        self.resume_button.draw(self.screen)
        self.pause_main_menu_button.draw(self.screen) # Draw the dedicated pause menu button

    def _draw_level_transition_state(self):
        self._draw_overlay("LEVEL COMPLETE!", f"Level {self.level_manager.get_level_number()} Complete!", COLOR_YELLOW)

        current_level = self.level_manager.get_current_level()
        next_level_index = self.level_manager.current_level_index + 1
        if next_level_index < len(self.level_manager.levels_data[self.difficulty]):
            next_level = self.level_manager.levels_data[self.difficulty][next_level_index]
            next_level_text = self.ui_font.render(f"Next Level: {next_level['level']}", True, COLOR_WHITE)
            next_level_rect = next_level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            self.screen.blit(next_level_text, next_level_rect)

            target_text = self.ui_font.render(f"Target: {next_level['target']} points", True, COLOR_WHITE)
            target_rect = target_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(target_text, target_rect)

        self.next_level_button.draw(self.screen)
        self.main_menu_button.draw(self.screen)

    def _draw_game_over_state(self):
        self._draw_overlay("GAME OVER", f"Final Score: {self.score}", COLOR_RED)
        level_text = self.ui_font.render(f"Reached Level: {self.level_manager.get_level_number()}", True, COLOR_WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(level_text, level_rect)

        self.play_again_button.draw(self.screen)
        self.main_menu_button.draw(self.screen)

    def _draw_game_completed_state(self):
        self._draw_overlay("GAME COMPLETED!", f"Difficulty: {self.difficulty}", COLOR_YELLOW)

        score_text = self.ui_font.render(f"Final Score: {self.score}", True, COLOR_GREEN)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(score_text, score_rect)

        congrats_text = self.ui_font.render("Congratulations!", True, COLOR_WHITE)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(congrats_text, congrats_rect)

        self.main_menu_button.draw(self.screen)


    def _draw_overlay(self, title: str, message: str, title_color: Tuple[int,int,int]):
        """Helper to draw common overlay elements."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.title_font.render(title, True, title_color)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        self.screen.blit(title_surf, title_rect)

        msg_surf = self.ui_font.render(message, True, COLOR_WHITE)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 20))
        self.screen.blit(msg_surf, msg_rect)


    def _update_button_hover(self, mouse_pos: Tuple[int, int], buttons: List[Button]):
        """Updates the hover state for a list of buttons."""
        for button in buttons:
            button.check_hover(mouse_pos)

    # --- Game Logic ---
    def _submit_name(self):
        name = self.name_input.get_text()
        if name:
            self.player_name = name
            self.player_id = self.player_db.add_player(name)
            if self.player_id is not None:
                self._change_state(GameState.WELCOME)
            else:
                # Handle DB error - maybe show a message?
                print("Error adding player to database.")
                # For now, just go to menu without a player
                self.player_name = ""
                self.player_id = None
                self._change_state(GameState.MAIN_MENU)

        else:
            # Handle empty name? Maybe show message on screen?
            print("Player name cannot be empty.")

    def _try_update_player_name(self):
        """Attempts to update the player name in the DB and game state."""
        new_name = self.name_input.get_text()
        if new_name and self.player_id is not None:
            success = self.player_db.update_player_name(self.player_id, new_name)
            if success:
                print(f"Player name changed to {new_name}")
                self.player_name = new_name # Update game state
                # Optional: Show a success message briefly?
                self._change_state(GameState.OPTIONS_MENU) # Go back to options
            else:
                # Optional: Show error message (name taken, DB error)
                print(f"Failed to change name to {new_name}. Name might be taken.")
                # Stay on change name screen, maybe clear input or highlight error?
                self.name_input.text = "" # Clear input on failure
        elif not new_name:
            print("New name cannot be empty.")
        else:
            print("Cannot change name, no player logged in.") # Should not happen if button disabled
            self._change_state(GameState.OPTIONS_MENU)

    def _update_game_logic(self, current_time: int):
        """Updates snake movement, checks collisions, levels, etc."""
        self.snake.move()
        self._check_collisions()
        self._check_fail_conditions()

        # Update timed elements (poison apple, wall changes)
        if current_time - self.last_apple_poison_time > self.settings["apple_poison_time"]:
            if not self.fruit.is_poisonous: # Only turn poisonous if not already
                self.fruit.is_poisonous = True
                self.last_apple_poison_time = current_time # Reset timer only when it turns poisonous

        if current_time - self.last_wall_change_time > self.settings["wall_change_time"]:
            wall_range = self.settings["wall_count"]
            self.wall.generate(
                wall_range[0], wall_range[1],
                self.snake.body, self.fruit.pos
            )
            self.last_wall_change_time = current_time

        # Check for level completion AFTER checks (so game over takes priority)
        if self.game_state == GameState.PLAYING: # Only check if still playing
             if self.level_manager.is_level_complete(self.score):
                 self.level_manager.mark_level_complete()
                 if self.level_manager.is_game_complete():
                      self._trigger_game_completed()
                 else:
                      self._change_state(GameState.LEVEL_TRANSITION)

    def _check_collisions(self):
        """Checks for snake eating fruit."""
        if self.snake.body and self.fruit.pos == self.snake.body[0]:
            if self.fruit.is_poisonous:
                # Poison effect: reduce score, maybe slow down, lose a life?
                self.score = max(0, self.score - 1) # Prevent negative score
                # Optional: Add a negative sound effect
                self.fruit.randomize(self.snake.body, self.wall.positions) # Respawn non-poisonous
                self.last_apple_poison_time = pygame.time.get_ticks() # Reset poison timer
            else:
                # Eat normal fruit
                self.score += 1
                self.snake.add_block()
                self.snake.play_crunch_sound()
                self.fruit.randomize(self.snake.body, self.wall.positions)
                self.last_apple_poison_time = pygame.time.get_ticks() # Reset poison timer

    def _check_fail_conditions(self):
        """Checks for game over conditions (wall, edge, self-collision)."""
        if not self.snake.body: return # Skip if snake body is empty

        head = self.snake.body[0]

        # Hit edge
        if not (0 <= head.x < self.cell_number and 0 <= head.y < self.cell_number):
            self._trigger_game_over()
            return

        # Hit wall
        if head in self.wall.positions:
            self._trigger_game_over()
            return

        # Hit self
        if head in self.snake.body[1:]:
            self._trigger_game_over()
            return

    def _trigger_game_over(self):
        """Handles actions when game over occurs."""
        print("Game Over triggered!")
        if self.player_id is not None:
            self.player_db.update_player_score(
                self.player_id, self.score, self.difficulty,
                self.level_manager.get_level_number()
            )
        self._change_state(GameState.GAME_OVER)
        # Optional: Play game over sound

    def _trigger_game_completed(self):
         """Handles actions when the game is completed."""
         print("Game Completed triggered!")
         if self.player_id is not None:
            # Update score one last time for the final level
            self.player_db.update_player_score(
                self.player_id, self.score, self.difficulty,
                self.level_manager.get_level_number()
            )
         self._change_state(GameState.GAME_COMPLETED)
         # Optional: Play victory sound


    def reset_game(self, reset_player: bool = True):
        """Resets the game to its initial state for the current difficulty."""
        self.score = 0
        self.snake.reset()
        self.level_manager.reset_progress()
        self._generate_initial_walls()
        self.fruit.randomize(self.snake.body, self.wall.positions)
        self.last_wall_change_time = pygame.time.get_ticks()
        self.last_apple_poison_time = pygame.time.get_ticks()
        if reset_player:
            self.player_name = ""
            self.player_id = None

    def reset_level(self):
        """Resets elements for the start of a new level, keeping score."""
        # Keep current score!
        self.snake.reset() # Reset position, keep length potentially? (No, reset fully)
        self._generate_initial_walls() # New walls for new level
        self.fruit.randomize(self.snake.body, self.wall.positions)
        self.last_wall_change_time = pygame.time.get_ticks()
        self.last_apple_poison_time = pygame.time.get_ticks()
        # Reset snake direction needs to happen in _change_state to Playing

    def _generate_initial_walls(self):
         wall_range = self.settings["wall_count"]
         self.wall.generate(
             wall_range[0], wall_range[1],
             self.snake.body, self.fruit.pos # Pass initial positions
         )

    def _draw_level_background(self):
        """Draws the background using tiles specific to the current level."""
        current_level_num = self.level_manager.get_level_number()

        # Get the tile coordinates for the current level, default to level 1 if level > 5
        tile_coords = self.level_bg_tiles.get(current_level_num, self.level_bg_tiles[1])

        # Get the actual tile surfaces from the tileset
        tile1 = self.world_tileset.get_tile(tile_coords[0][0], tile_coords[0][1])
        tile2 = self.world_tileset.get_tile(tile_coords[1][0], tile_coords[1][1])

        if not tile1 or not tile2: # Fallback if tiles couldn't be loaded
            self.screen.fill(COLOR_GRASS_1) # Simple fallback color
            print(f"Warning: Could not load background tiles for level {current_level_num}. Using fallback.")
            return

        # Draw checkered pattern using the selected tiles
        for row in range(self.cell_number):
            for col in range(self.cell_number):
                bg_rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
                tile_image = tile1 if (row + col) % 2 == 0 else tile2
                self.screen.blit(tile_image, bg_rect)

    # --- Drawing Helpers ---
    # def _draw_grass(self):
    #     """Draws the checkered grass background."""
    #     for row in range(self.cell_number):
    #         for col in range(self.cell_number):
    #             grass_rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
    #             image = self.grass_image_1 if (row + col) % 2 == 0 else self.grass_image_2
    #             self.screen.blit(image, grass_rect)

    def _draw_score_hud(self):
        """Draws the score, level, target, progress bar, and player name."""
        margin = 15
        line_height = 35
        bg_padding = 5
        progress_width = 200
        progress_height = 20

        # Level Text
        level_text = f"Level: {self.level_manager.get_level_number()}"
        level_surf = self.score_font.render(level_text, True, COLOR_SCORE_TEXT)
        level_rect = level_surf.get_rect(topleft=(margin, margin))
        self._draw_hud_element_background(level_rect, bg_padding)
        self.screen.blit(level_surf, level_rect)

        # Target Text
        target_score = self.level_manager.get_target_score()
        target_text = f"Target: {target_score}"
        target_surf = self.score_font.render(target_text, True, COLOR_SCORE_TEXT)
        target_rect = target_surf.get_rect(topleft=(margin, level_rect.bottom + margin // 2))
        self._draw_hud_element_background(target_rect, bg_padding)
        self.screen.blit(target_surf, target_rect)

        # Progress Bar
        progress = min(1.0, self.score / target_score) if target_score > 0 else 0
        progress_bar_rect = pygame.Rect(margin, target_rect.bottom + margin, progress_width, progress_height)
        pygame.draw.rect(self.screen, COLOR_TEXT_INPUT_INACTIVE, progress_bar_rect) # Background
        filled_width = int(progress_width * progress)
        pygame.draw.rect(self.screen, COLOR_GREEN, (progress_bar_rect.x, progress_bar_rect.y, filled_width, progress_height)) # Filled part
        pygame.draw.rect(self.screen, COLOR_SCORE_TEXT, progress_bar_rect, 2) # Border

         # Player Name
        if self.player_name:
            player_text = f"Player: {self.player_name}"
            player_surf = self.score_font.render(player_text, True, COLOR_SCORE_TEXT)
            player_rect = player_surf.get_rect(topleft=(margin, progress_bar_rect.bottom + margin))
            self._draw_hud_element_background(player_rect, bg_padding)
            self.screen.blit(player_surf, player_rect)

        # Score Text (Top Right)
        score_text = str(self.score)
        score_surf = self.score_font.render(score_text, True, COLOR_SCORE_TEXT)
        score_rect = score_surf.get_rect(topright=(SCREEN_WIDTH - margin, margin))
        # Apple Icon next to score
        apple_rect = self.apple_score_icon.get_rect(midright=(score_rect.left - 5, score_rect.centery))
        # Background for score + icon
        score_bg_rect = pygame.Rect(
            apple_rect.left - bg_padding,
            apple_rect.top - bg_padding,
            apple_rect.width + score_rect.width + 5 + 2 * bg_padding,
            apple_rect.height + 2 * bg_padding
        )
        pygame.draw.rect(self.screen, COLOR_LIGHT_GREEN, score_bg_rect, border_radius=5)
        self.screen.blit(self.apple_score_icon, apple_rect)
        self.screen.blit(score_surf, score_rect)
        pygame.draw.rect(self.screen, COLOR_SCORE_TEXT, score_bg_rect, 2, border_radius=5)


    def _draw_hud_element_background(self, text_rect: pygame.Rect, padding: int):
         """Draws a simple background behind a HUD text element."""
         bg_rect = text_rect.inflate(padding * 2, padding * 2)
         pygame.draw.rect(self.screen, COLOR_LIGHT_GREEN, bg_rect, border_radius=5)
         pygame.draw.rect(self.screen, COLOR_SCORE_TEXT, bg_rect, 2, border_radius=5) # Border


# --- Main Execution ---
if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init() # Initialize mixer for sound

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Improved Snake Game")
    clock = pygame.time.Clock()

    game = Game(screen, clock)
    game.run() # Start the main game loop