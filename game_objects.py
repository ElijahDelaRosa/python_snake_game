import pygame
import random
from pygame.math import Vector2
from typing import List, Tuple, Optional, Dict, Any
from assets import load_sound, load_snake_sprites, load_apple_sprites, get_tileset, load_image
from config import (DEFAULT_SNAKE_COLOR, POISON_APPLE_CHANCE,
                    LEVEL_BG_TILES, DEFAULT_BG_FILL_COLOR,
                    APPLE_VISUAL_SCALE_FACTOR) # Added APPLE_VISUAL_SCALE_FACTOR

# Enum for Apple State
class AppleState:
    GOOD = "good"
    WARNING = "warning" # About to expire or turn poisonous
    POISONOUS = "poisonous"
    EXPIRED = "expired" # For internal handling if it just despawns


class Snake:
    def __init__(self, cell_size: int, cell_number: int, initial_pos: Vector2 = Vector2(5,10), color: str = DEFAULT_SNAKE_COLOR):
        self.cell_size = cell_size
        self.cell_number = cell_number # Keep track of grid size
        self.initial_pos = initial_pos
        self.body: List[Vector2] = []
        self.direction: Vector2 = Vector2(0, 0) # Start stationary
        self.new_block: bool = False
        self.color = color # Store the selected color
        
        self.sprites = load_snake_sprites(self.cell_size, self.color) # Use stored color
        self.head_sprite = self.sprites['head_right'] # Default
        self.tail_sprite = self.sprites['tail_left']  # Default

        self.reset()

    def reset(self):
        # Start with 3 segments: head, body1, body2. Assuming horizontal start, head to the right.
        # initial_pos is the head. Segments are to its left.
        head_pos = self.initial_pos.copy()
        body1_pos = Vector2(head_pos.x - 1, head_pos.y)
        body2_pos = Vector2(head_pos.x - 2, head_pos.y)
        self.body = [head_pos, body1_pos, body2_pos]

        self.direction = Vector2(0, 0) # Start stationary, will be set by GameController
        self.new_block = False # Ensure this is reset
        self.update_head_graphics()
        self.update_tail_graphics() # Also update tail for the initial 3 segments

    def draw(self, surface: pygame.Surface):
        # Draw body segments first (leave out head and tail for now)
        for i, segment in enumerate(self.body):
            x_pos = int(segment.x * self.cell_size)
            y_pos = int(segment.y * self.cell_size)
            rect = pygame.Rect(x_pos, y_pos, self.cell_size, self.cell_size)

            if 0 < i < len(self.body) - 1:
                # For middle segments, determine which body sprite to use based on
                # the positions of the segments before and after it
                prev_block = self.body[i + 1] - self.body[i]
                next_block = self.body[i - 1] - self.body[i]
                
                if prev_block.x == next_block.x: # Vertical line
                    surface.blit(self.sprites['body_vertical'], rect)
                elif prev_block.y == next_block.y: # Horizontal line
                    surface.blit(self.sprites['body_horizontal'], rect)
                else: # Corner
                    # Determine which corner sprite to use
                    if prev_block.x == 1 and next_block.y == -1 or prev_block.y == -1 and next_block.x == 1:
                        # bottom-left corner
                        surface.blit(self.sprites['body_tl'], rect)
                    elif prev_block.x == -1 and next_block.y == -1 or prev_block.y == -1 and next_block.x == -1:
                        # bottom-right corner
                        surface.blit(self.sprites['body_tr'], rect)
                    elif prev_block.x == 1 and next_block.y == 1 or prev_block.y == 1 and next_block.x == 1:
                        # top-left corner
                        surface.blit(self.sprites['body_bl'], rect)
                    elif prev_block.x == -1 and next_block.y == 1 or prev_block.y == 1 and next_block.x == -1:
                        # top-right corner
                        surface.blit(self.sprites['body_br'], rect)

        # Draw head
        head_rect = pygame.Rect(
            self.body[0].x * self.cell_size,
            self.body[0].y * self.cell_size,
            self.cell_size, self.cell_size
        )
        surface.blit(self.head_sprite, head_rect)

        # Draw tail (only if snake has more than one segment)
        if len(self.body) > 1:
            tail_rect = pygame.Rect(
                self.body[-1].x * self.cell_size,
                self.body[-1].y * self.cell_size,
                self.cell_size, self.cell_size
            )
            self.update_tail_graphics()
            surface.blit(self.tail_sprite, tail_rect)

    def update_head_graphics(self):
        # Update the head sprite based on current direction
        if len(self.body) == 1: return # If we only have one segment (the head)
        
        head_relation = self.body[0] - self.body[1]
        
        if head_relation == Vector2(1, 0): self.head_sprite = self.sprites['head_right']
        elif head_relation == Vector2(-1, 0): self.head_sprite = self.sprites['head_left']
        elif head_relation == Vector2(0, 1): self.head_sprite = self.sprites['head_down']
        elif head_relation == Vector2(0, -1): self.head_sprite = self.sprites['head_up']

    def update_tail_graphics(self):
        # Update the tail sprite based on position relative to the second-to-last segment
        if len(self.body) < 2: return # Cannot determine tail if less than 2 segments
        
        tail_relation = self.body[-2] - self.body[-1]
        
        if tail_relation == Vector2(1, 0): self.tail_sprite = self.sprites['tail_left']
        elif tail_relation == Vector2(-1, 0): self.tail_sprite = self.sprites['tail_right']
        elif tail_relation == Vector2(0, 1): self.tail_sprite = self.sprites['tail_up']
        elif tail_relation == Vector2(0, -1): self.tail_sprite = self.sprites['tail_down']

    def move(self):
        # If the snake isn't moving, don't do anything
        if self.direction == Vector2(0, 0):
            return

        # Copy the body segments except the last one (the tail)
        body_segments = self.body[:-1] if not self.new_block else self.body[:]
        
        # Insert new head position at the beginning
        new_head = self.body[0] + self.direction
        body_segments.insert(0, new_head)
        
        # Update the body
        self.body = body_segments
        self.new_block = False
        self.update_head_graphics()

    def grow(self):
        # Set flag to indicate that a new block should be added on next move
        self.new_block = True

    def shrink(self):
        # Remove the last segment (tail) if snake is longer than 1 segment
        if len(self.body) > 1:
            self.body.pop()
            return True
        return False  # Cannot shrink further

    def change_direction(self, direction: Vector2):
        # Only change direction if it's not the exact opposite of current direction
        # This prevents the snake from reversing into itself
        if len(self.body) > 1:
            if direction + self.direction != Vector2(0, 0):
                self.direction = direction
        else:
            # If the snake is just a head, it can go any direction
            self.direction = direction

    def check_bounds_collision(self) -> bool:
        """Check if the snake's head is outside the boundary"""
        head = self.body[0]
        return (
            head.x < 0 or head.x >= self.cell_number or
            head.y < 0 or head.y >= self.cell_number
        )

    def check_collision_with_self(self) -> bool:
        """Check if the snake's head collides with its body"""
        # Skip the first element (the head)
        # If the head position is in the rest of the body, collision occurred
        head = self.body[0]
        return any(segment == head for segment in self.body[1:])

    def get_head_pos(self) -> Vector2:
        return self.body[0] if self.body else self.initial_pos


class Fruit:
    def __init__(self, cell_size: int, cell_number: int, difficulty_settings: dict):
        self.cell_size = cell_size
        self.cell_number = cell_number
        self.pos: Vector2 = Vector2(-1, -1) # Initial off-screen position
        
        self.apple_sprites = load_apple_sprites(cell_size)
        self.image = self.apple_sprites[AppleState.GOOD] # Default
        
        self.state = AppleState.GOOD
        self.spawn_time = 0
        self.time_to_live = difficulty_settings.get("apple_total_life", float('inf'))
        self.time_to_warn = difficulty_settings.get("apple_warning_time", float('inf'))
        self.expiry_enabled = difficulty_settings.get("apple_expiry_enabled", False)
        self.is_active = False # Becomes active once randomized
        self.poison_time_to_live = difficulty_settings.get("poison_apple_life", 3000)  # Get from difficulty settings, default 3s

    def draw(self, screen: pygame.Surface):
        if not self.is_active:
            return
        
        # Calculate the target size for drawing the apple
        target_width = int(self.cell_size * APPLE_VISUAL_SCALE_FACTOR)
        target_height = int(self.cell_size * APPLE_VISUAL_SCALE_FACTOR)

        # Scale the current apple image (self.image is already cell_size)
        scaled_apple_image = pygame.transform.scale(self.image, (target_width, target_height))

        # Calculate the top-left position to center the scaled image over the original cell
        # Original cell top-left would be (self.pos.x * self.cell_size, self.pos.y * self.cell_size)
        # Original cell center_x = self.pos.x * self.cell_size + self.cell_size / 2
        # Original cell center_y = self.pos.y * self.cell_size + self.cell_size / 2
        
        # Top-left for the new scaled image to be centered at the original cell's center
        draw_x = (self.pos.x * self.cell_size + self.cell_size / 2) - target_width / 2
        draw_y = (self.pos.y * self.cell_size + self.cell_size / 2) - target_height / 2
        
        screen.blit(scaled_apple_image, (int(draw_x), int(draw_y)))

    def update_state(self, current_time: pygame.time.Clock):
        if not self.is_active:
            return

        elapsed_time = current_time - self.spawn_time
        
        # Special handling for poisonous apples to expire after their poisonous duration
        if self.state == AppleState.POISONOUS and elapsed_time >= self.poison_time_to_live:
            self.set_state(AppleState.EXPIRED)
            return
            
        # Normal expiry logic for good apples
        if not self.expiry_enabled:
            return

        if self.state == AppleState.GOOD and elapsed_time >= (self.time_to_live - self.time_to_warn):
            self.set_state(AppleState.WARNING)
        elif self.state == AppleState.WARNING and elapsed_time >= self.time_to_live:
            # Instead of expiring, turn warning apples into poisonous ones
            self.set_state(AppleState.POISONOUS)
            # Reset the timer for the poisonous duration
            self.spawn_time = current_time

    def set_state(self, new_state: AppleState):
        self.state = new_state
        self.image = self.apple_sprites.get(new_state, self.apple_sprites[AppleState.GOOD])
        if new_state == AppleState.GOOD or new_state == AppleState.POISONOUS:
            self.spawn_time = pygame.time.get_ticks() # Reset timer when it becomes good or poisonous

    def randomize(self, snake_body: List[Vector2], wall_positions: List[Vector2], other_apple_pos: List[Vector2]):
        occupied_positions = snake_body + wall_positions + other_apple_pos
        possible_positions = []
        for r in range(self.cell_number):
            for c in range(self.cell_number):
                pos = Vector2(c,r)
                if pos not in occupied_positions:
                    possible_positions.append(pos)
        
        if not possible_positions:
            self.is_active = False # Cannot place apple
            self.pos = Vector2(-1,-1)
            return

        self.pos = random.choice(possible_positions)
        self.is_active = True

        # Determine if it should be poisonous (only if not already set by expiry)
        if random.random() < POISON_APPLE_CHANCE:
            self.set_state(AppleState.POISONOUS)
        else:
            self.set_state(AppleState.GOOD) # Resets spawn_time


class Wall:
    def __init__(self, cell_size: int, cell_number: int):
        self.cell_size = cell_size
        self.cell_number = cell_number
        self.positions: List[Vector2] = []
        
        # Use Snake.png instead of world_tileset.png
        self.snake_tileset = get_tileset("Snake.png", 16, 16, cell_size)
        
        # Store obstacle tile coordinates from Snake.png
        self.obstacle_tile_coords = [
            (9, 1),    # Stone
            (7, 8),    # Rubble
            (15, 1),   # Cactus
            (15, 8),   # Trees
        ]
        
        # Load tiles and scale them up by 30%
        original_tiles = [self.snake_tileset.get_tile(x, y) for x, y in self.obstacle_tile_coords]
        
        # Scale the tiles up by 30%
        self.tile_images = []
        scale_factor = 1.3  # 30% larger
        for tile in original_tiles:
            # Get original size
            orig_width = tile.get_width()
            orig_height = tile.get_height()
            
            # Calculate new size (30% larger)
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            
            # Scale the tile
            scaled_tile = pygame.transform.scale(tile, (new_width, new_height))
            self.tile_images.append(scaled_tile)
        
        # Dictionary to map each position to a specific tile index (using string keys)
        self.position_to_tile = {}
    
    # Helper to convert Vector2 to a string key
    def _pos_to_key(self, pos: Vector2) -> str:
        return f"{int(pos.x)},{int(pos.y)}"

    def generate(self, num_obstacles: int, snake_body: List[Vector2], fruit_positions: List[Vector2]):
        self.positions.clear()
        self.position_to_tile.clear()
        if num_obstacles == 0:
            return

        forbidden_cols_initial_snake = 5
        snake_head_margin = 3
        
        safe_zones_tuples = set()
        for fp in fruit_positions:
            safe_zones_tuples.add((int(fp.x), int(fp.y)))

        if snake_body:
            head = snake_body[0]
            for dx in range(-snake_head_margin, snake_head_margin + 1):
                for dy in range(-snake_head_margin, snake_head_margin + 1):
                    safe_zones_tuples.add((int(head.x + dx), int(head.y + dy)))
            for part in snake_body:
                safe_zones_tuples.add((int(part.x), int(part.y)))

        possible_positions = []
        for r in range(self.cell_number):
            for c in range(self.cell_number):
                if c < forbidden_cols_initial_snake and snake_body and any(int(s.x) < forbidden_cols_initial_snake for s in snake_body):
                    continue
                current_pos_tuple = (c, r)
                if current_pos_tuple not in safe_zones_tuples:
                    possible_positions.append(Vector2(c, r))
        
        random.shuffle(possible_positions)

        for _ in range(min(num_obstacles, len(possible_positions))):
            position = possible_positions.pop()
            self.positions.append(position)
            # Assign a random tile index to this position using string key
            self.position_to_tile[self._pos_to_key(position)] = random.randint(0, len(self.tile_images) - 1)

    def draw(self, screen: pygame.Surface):
        for pos in self.positions:
            # Get the specific tile for this position using string key
            tile_index = self.position_to_tile.get(self._pos_to_key(pos), 0)  # Default to first tile if not found
            
            # Get the tile image
            tile = self.tile_images[tile_index]
            
            # Calculate position considering the enlarged size
            tile_width, tile_height = tile.get_size()
            x_pos = int(pos.x * self.cell_size + (self.cell_size - tile_width) / 2)
            y_pos = int(pos.y * self.cell_size + (self.cell_size - tile_height) / 2)
            
            # Draw the tile at the adjusted position
            screen.blit(tile, (x_pos, y_pos))

    def check_collision(self, position: Vector2) -> bool:
        return position in self.positions

# Background Manager
class Background:
    def __init__(self, cell_size: int, cell_number: int, world_tileset_name="world_tileset.png"):
        self.cell_size = cell_size
        self.cell_number = cell_number
        self.tileset = get_tileset(world_tileset_name, 16, 16, cell_size)
        self.current_level_tiles = None
        self.fill_color = DEFAULT_BG_FILL_COLOR

    def set_level_background(self, level_number: int):
        level_bg_data = LEVEL_BG_TILES.get(level_number, LEVEL_BG_TILES.get(1)) # Default to level 1 style
        if level_bg_data:
            primary_coord = level_bg_data["primary"]
            secondary_coord = level_bg_data["secondary"]
            self.current_level_tiles = {
                "primary": self.tileset.get_tile(primary_coord[0], primary_coord[1]),
                "secondary": self.tileset.get_tile(secondary_coord[0], secondary_coord[1]),
            }
            self.fill_color = level_bg_data.get("fill_color", DEFAULT_BG_FILL_COLOR)
        else:
            self.current_level_tiles = None # Fallback to solid color
            self.fill_color = DEFAULT_BG_FILL_COLOR


    def draw(self, screen: pygame.Surface):
        if self.current_level_tiles and self.current_level_tiles["primary"] and self.current_level_tiles["secondary"]:
            tile1 = self.current_level_tiles["primary"]
            tile2 = self.current_level_tiles["secondary"]
            for row in range(self.cell_number):
                for col in range(self.cell_number):
                    bg_rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
                    tile_image = tile1 if (row + col) % 2 == 0 else tile2
                    screen.blit(tile_image, bg_rect)
        else:
            # Fallback: fill with a color that complements or a default
            # screen.fill(self.fill_color) # This fills the whole screen. We need to draw this first.
            # This draw method is for the game area, main.py or game_controller should handle overall screen fill
            
            # If drawing a specific game area background:
            game_area_rect = pygame.Rect(0, 0, self.cell_number * self.cell_size, self.cell_number * self.cell_size) # Assuming game area starts at 0,0
            pygame.draw.rect(screen, self.fill_color, game_area_rect)