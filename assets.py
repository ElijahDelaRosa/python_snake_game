import pygame
import os
import sys
from PIL import Image, ImageSequence
from typing import List, Tuple, Optional, Dict, Any
from config import GRAPHICS_DIR, SOUND_DIR, FONT_DIR, SNAKE_GRAPHICS_COORDS, DEFAULT_SNAKE_COLOR, SNAKE_TILE_SIZE, SNAKE_SPRITE_SHEET, APPLE_TILE_COORDS, CELL_SIZE_DEFAULT

pygame.mixer.pre_init(44100, -16, 2, 512) # Initialize mixer with common parameters
pygame.init() # Ensure pygame is initialized for font and image loading

# --- Asset Loading Cache ---
_image_cache = {}
_font_cache = {}
_sound_cache = {}
_tileset_cache = {}
_snake_sprite_sheet_cache = {}

# Default volume setting
DEFAULT_VOLUME = 0.7

def load_sound(filename: str) -> pygame.mixer.Sound:
    """Loads a sound file. Uses caching."""
    if filename in _sound_cache:
        return _sound_cache[filename]
    try:
        sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, filename))
        _sound_cache[filename] = sound
        return sound
    except pygame.error as e:
        print(f"Error loading sound {filename}: {e}")
        # Create a silent sound as a fallback
        buffer = pygame.sndarray.array(pygame.Surface((1, 1)))
        silent_sound = pygame.sndarray.make_sound(buffer)
        _sound_cache[filename] = silent_sound
        return silent_sound
    except FileNotFoundError:
        print(f"Error: Sound file not found: {filename}")
        # Create a silent sound as a fallback
        buffer = pygame.sndarray.array(pygame.Surface((1, 1)))
        silent_sound = pygame.sndarray.make_sound(buffer)
        _sound_cache[filename] = silent_sound
        return silent_sound

# Sound Manager for controlling all game sounds
class SoundManager:
    def __init__(self):
        self.volume = DEFAULT_VOLUME
        self.music_loaded = False
        self.sounds = {}
        self.music_paused = False
        
        # Load common sounds
        self.load_common_sounds()
        
    def load_common_sounds(self):
        # Load sound effects
        self.sounds["crunch"] = load_sound("crunch.wav")
        self.sounds["vomit"] = load_sound("vomit.mp3")
        self.sounds["game_over"] = load_sound("game-over.wav")
        self.sounds["game_start"] = load_sound("game-start.mp3")
        self.sounds["level_finished"] = load_sound("level-finished.wav")
        self.sounds["menu_button"] = load_sound("menu-button.mp3")
        
        # Set initial volumes
        self.set_volume(self.volume)
    
    def set_volume(self, volume: float):
        """Set volume for all sound effects (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        
        # Set music volume
        pygame.mixer.music.set_volume(self.volume)
        
        # Set sound effect volumes
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def play_sound(self, sound_name: str):
        """Play a sound by name"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
    
    def play_music(self, filename: str = "bg-music.mp3", loop: bool = True):
        """Start playing background music"""
        try:
            music_path = os.path.join(SOUND_DIR, filename)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.volume)
            if loop:
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            else:
                pygame.mixer.music.play()
            self.music_loaded = True
        except Exception as e:
            print(f"Error loading music {filename}: {e}")
            self.music_loaded = False
    
    def stop_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
    
    def pause_music(self):
        """Pause background music"""
        if self.music_loaded and not self.music_paused:
            pygame.mixer.music.pause()
            self.music_paused = True
    
    def unpause_music(self):
        """Resume background music"""
        if self.music_loaded and self.music_paused:
            pygame.mixer.music.unpause()
            self.music_paused = False
    
    def fade_out_music(self, time_ms: int = 1000):
        """Fade out music over time_ms milliseconds"""
        pygame.mixer.music.fadeout(time_ms)

# Global sound manager instance
sound_manager = SoundManager()

def load_image(filename: str, alpha: bool = True, scale: Optional[Tuple[int, int]] = None) -> pygame.Surface:
    """Loads an image, optionally converts alpha and scales. Uses caching."""
    cache_key = (filename, alpha, scale)
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    try:
        image = pygame.image.load(os.path.join(GRAPHICS_DIR, filename))
        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
        if scale:
            image = pygame.transform.scale(image, scale)
        _image_cache[cache_key] = image
        return image
    except pygame.error as e:
        print(f"Error loading image {filename}: {e}")
        sys.exit()
    except FileNotFoundError:
        print(f"Error: Graphics file not found: {filename}")
        # Return a placeholder surface or exit
        placeholder = pygame.Surface(scale if scale else (CELL_SIZE_DEFAULT, CELL_SIZE_DEFAULT))
        placeholder.fill((255,0,0)) # Bright red to indicate missing asset
        if scale: placeholder = pygame.transform.scale(placeholder, scale)
        _image_cache[cache_key] = placeholder # Cache placeholder to avoid repeated errors
        return placeholder # Or sys.exit()

def load_font(filename: str, size: int) -> pygame.font.Font:
    """Loads a font file. Uses caching."""
    cache_key = (filename, size)
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    try:
        font = pygame.font.Font(os.path.join(FONT_DIR, filename), size)
        _font_cache[cache_key] = font
        return font
    except pygame.error as e:
        print(f"Error loading font {filename}: {e}")
        sys.exit()
    except FileNotFoundError:
        print(f"Error: Font file not found: {filename}")
        # Fallback to default pygame font
        font = pygame.font.SysFont(pygame.font.get_default_font(), size)
        _font_cache[cache_key] = font
        return font


def load_gif_frames(filename: str, scale: Tuple[int, int]) -> List[pygame.Surface]:
    """Loads frames from a GIF, scales them, and converts to Pygame surfaces."""
    # GIF loading can be memory intensive, consider if caching is needed or if it's loaded once.
    try:
        with Image.open(os.path.join(GRAPHICS_DIR, filename)) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                frame_rgba = frame.convert("RGBA")
                pygame_frame = pygame.image.fromstring(
                    frame_rgba.tobytes(), frame_rgba.size, "RGBA"
                ).convert_alpha()
                scaled_frame = pygame.transform.scale(pygame_frame, scale)
                frames.append(scaled_frame)
            if not frames: # Handle empty GIF
                 placeholder = pygame.Surface(scale)
                 placeholder.fill((50,50,50))
                 frames.append(placeholder)
            return frames
    except FileNotFoundError:
        print(f"Error: GIF file not found: {filename}")
        placeholder = pygame.Surface(scale)
        placeholder.fill((50,50,50)) # Grey placeholder
        return [placeholder]
    except Exception as e:
        print(f"Error processing GIF {filename}: {e}")
        sys.exit()


class Tileset:
    def __init__(self, filename: str, tile_width: int, tile_height: int, scale_to_cell_size: int):
        self.filename = filename
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.scale_to_size = (scale_to_cell_size, scale_to_cell_size)
        self._cache = {}

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

    def get_tile(self, tile_x: int, tile_y: int) -> Optional[pygame.Surface]:
        """Extracts and scales a single tile from the tileset. Uses caching."""
        if not (0 <= tile_x < self.cols and 0 <= tile_y < self.rows):
            print(f"Warning: Tile coordinates ({tile_x}, {tile_y}) for {self.filename} out of bounds.")
            placeholder = pygame.Surface(self.scale_to_size)
            placeholder.fill( (255,0,255) ) # Magenta placeholder for bad tile
            return placeholder

        cache_key = (tile_x, tile_y)
        if cache_key in self._cache:
            return self._cache[cache_key]

        rect = pygame.Rect(tile_x * self.tile_width, tile_y * self.tile_height,
                           self.tile_width, self.tile_height)
        tile_image = self.image.subsurface(rect)
        scaled_tile = pygame.transform.scale(tile_image, self.scale_to_size)
        self._cache[cache_key] = scaled_tile
        return scaled_tile

def get_tileset(filename: str, tile_width: int, tile_height: int, scale_to_cell_size: int) -> Tileset:
    """Gets a Tileset instance, uses caching for the Tileset object itself."""
    cache_key = (filename, tile_width, tile_height, scale_to_cell_size)
    if cache_key not in _tileset_cache:
        _tileset_cache[cache_key] = Tileset(filename, tile_width, tile_height, scale_to_cell_size)
    return _tileset_cache[cache_key]


def load_snake_sprites(cell_size: int, snake_color: str = DEFAULT_SNAKE_COLOR) -> Dict[str, pygame.Surface]:
    """Loads all snake part sprites from Snake.png for a given color and scales them."""
    if SNAKE_SPRITE_SHEET not in _snake_sprite_sheet_cache:
        try:
            _snake_sprite_sheet_cache[SNAKE_SPRITE_SHEET] = pygame.image.load(
                os.path.join(GRAPHICS_DIR, SNAKE_SPRITE_SHEET)).convert_alpha()
        except pygame.error as e:
            print(f"Fatal: Error loading snake sprite sheet {SNAKE_SPRITE_SHEET}: {e}")
            sys.exit()
        except FileNotFoundError:
            print(f"Fatal: Snake sprite sheet not found: {SNAKE_SPRITE_SHEET}")
            sys.exit()

    sheet = _snake_sprite_sheet_cache[SNAKE_SPRITE_SHEET]
    sprites = {}
    coords_dict = SNAKE_GRAPHICS_COORDS.get(snake_color)

    if not coords_dict:
        print(f"Fatal: Snake color '{snake_color}' not found in SNAKE_GRAPHICS_COORDS.")
        sys.exit()

    for part_name, rect_coords in coords_dict.items():
        try:
            sprite_image = sheet.subsurface(rect_coords)
            sprites[part_name] = pygame.transform.scale(sprite_image, (cell_size, cell_size))
        except ValueError as e: # Often from subsurface rect being out of bounds
            print(f"Error creating subsurface for snake part '{part_name}' with coords {rect_coords}: {e}")
            print(f"Ensure '{SNAKE_SPRITE_SHEET}' contains this part for color '{snake_color}' at the specified coordinates.")
            print("Using a placeholder for this part.")
            placeholder = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
            placeholder.fill((0,0,0,0)) # Transparent placeholder
            pygame.draw.rect(placeholder, (255,0,0), placeholder.get_rect(),1) # Red outline
            sprites[part_name] = placeholder

    # Ensure all standard parts are present, even if as placeholders
    standard_parts = [
        "head_up", "head_down", "head_left", "head_right",
        "tail_up", "tail_down", "tail_left", "tail_right",
        "body_vertical", "body_horizontal",
        "body_tr", "body_tl", "body_br", "body_bl"
    ]
    for part in standard_parts:
        if part not in sprites:
            print(f"Warning: Snake part '{part}' for color '{snake_color}' is missing from SNAKE_GRAPHICS_COORDS. Using placeholder.")
            placeholder = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
            placeholder.fill((0,0,0,0))
            pygame.draw.rect(placeholder, (255,0,255), placeholder.get_rect(),1) # Magenta outline for completely missing
            sprites[part] = placeholder
            
    return sprites


def load_apple_sprites(cell_size: int) -> Dict[str, pygame.Surface]:
    """Loads apple sprites from the Snake."""
    if SNAKE_SPRITE_SHEET not in _snake_sprite_sheet_cache:
        try:
            _snake_sprite_sheet_cache[SNAKE_SPRITE_SHEET] = pygame.image.load(
                os.path.join(GRAPHICS_DIR, SNAKE_SPRITE_SHEET)).convert_alpha()
        except pygame.error as e:
            print(f"Fatal: Error loading snake sprite sheet {SNAKE_SPRITE_SHEET}: {e}")
            sys.exit()
        except FileNotFoundError:
            print(f"Fatal: Snake sprite sheet not found: {SNAKE_SPRITE_SHEET}")
            sys.exit()

    sheet = _snake_sprite_sheet_cache[SNAKE_SPRITE_SHEET]
    apple_sprites = {}

    for apple_type, rect_coords in APPLE_TILE_COORDS.items():
        try:
            # Extract the apple sprite from the Snake.png sheet
            sprite_image = sheet.subsurface(rect_coords)
            # Scale it to cell size
            apple_sprites[apple_type] = pygame.transform.scale(sprite_image, (cell_size, cell_size))
        except ValueError as e:
            print(f"Error creating subsurface for apple '{apple_type}' with coords {rect_coords}: {e}")
            print(f"Ensure '{SNAKE_SPRITE_SHEET}' contains this sprite at the specified coordinates.")
            print("Using a placeholder for this apple type.")
            # Create a colored placeholder for missing apple sprites
            placeholder = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
            color = {"good": (255,0,0), "warning": (255,255,0), "poisonous": (0,255,0)}.get(apple_type, (128,128,128))
            pygame.draw.circle(placeholder, color, (cell_size//2, cell_size//2), cell_size//2)
            apple_sprites[apple_type] = placeholder
            
    return apple_sprites

# Pre-load common sounds (optional, but can reduce first-play lag)
# CRUNCH_SOUND = load_sound("crunch.wav")