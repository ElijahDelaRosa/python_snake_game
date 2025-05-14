import pygame
import sys
import time # For state transition delays, though pygame.time.get_ticks() is mostly used
from pygame.math import Vector2
from typing import List, Tuple, Optional, Dict, Any

from config import (
    GameState, DEFAULT_DIFFICULTY, DIFFICULTY_SETTINGS, LEVEL_CONFIG, FIXED_SCREEN_WIDTH, FIXED_SCREEN_HEIGHT, HUD_WIDTH,
    COLOR_WHITE, COLOR_BLACK, COLOR_RED, COLOR_YELLOW, COLOR_GREEN, COLOR_GRASS_1, COLOR_GRASS_2, COLOR_DARK_GREEN,
    COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER, COLOR_BUTTON_BACK_NORMAL, COLOR_BUTTON_BACK_HOVER,
    COLOR_BUTTON_HIGHLIGHT, COLOR_BUTTON_HIGHLIGHT_HOVER,
    COLOR_SCORE_TEXT, COLOR_LIGHT_GREEN, DEFAULT_PLAYER_NAME, COLOR_HUD_BG, DEFAULT_VOLUME, VOLUME_STEP,
    SNAKE_COLORS_AVAILABLE, DEFAULT_SNAKE_COLOR, COLOR_BRIGHT_SCORE_TEXT
)
from assets import (
    load_font, load_gif_frames, load_image, get_tileset, load_apple_sprites, sound_manager
)
from database import PlayerDatabase
from ui_elements import TextInput, Button, Slider
from game_objects import Snake, Fruit, Wall, Background, AppleState # AppleState for clarity
from level_manager import LevelManager


class GameController:
    def __init__(self):
        self.difficulty = DEFAULT_DIFFICULTY
        self.current_difficulty_settings = DIFFICULTY_SETTINGS[self.difficulty]
        self.selected_difficulty_for_level_select = None # Added for level selection
        # self.cell_number is set in _setup_game_instance based on difficulty

        # Initialize screen dimensions (fixed)
        self.screen_width = FIXED_SCREEN_WIDTH
        self.screen_height = FIXED_SCREEN_HEIGHT
        self.game_area_width = self.screen_width - HUD_WIDTH
        self.game_area_height = self.screen_height

        # self.cell_size will be calculated in _setup_game_instance
        # self.game_surface_width and self.game_surface_height also in _setup_game_instance
        # self.game_area_offset_x and self.game_area_offset_y also in _setup_game_instance

        # Initialize pygame screen
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Snake Game")

        # Define HUD rectangle (game_area_rect will be defined after cell_size is known)
        self.hud_area_rect = pygame.Rect(
            self.game_area_width,
            0,
            HUD_WIDTH,
            self.screen_height
        )

        # Initialize game state and components
        self.clock = pygame.time.Clock()
        self.game_state = GameState.NAME_INPUT
        self.player_db = PlayerDatabase()
        self.level_manager = LevelManager(LEVEL_CONFIG)
        self.player_name = DEFAULT_PLAYER_NAME
        self.player_id = None
        self.volume = DEFAULT_VOLUME
        self.snake_color = DEFAULT_SNAKE_COLOR # Added snake_color attribute
        self.selected_color_index_name_input = SNAKE_COLORS_AVAILABLE.index(DEFAULT_SNAKE_COLOR) # For name input UI

        # Initialize timers that might be accessed by setup/reset methods
        self.last_wall_change_time = 0
        self.last_apple_spawn_time = {} # Initialize an empty dictionary
        self.state_transition_time = 0
        self.welcome_duration = 2000  # ms
        self.level_transition_duration = 1500 # ms

        # Initialize SCREEN_UPDATE event type *before* _setup_game_instance is called,
        # because _setup_game_instance calls _update_game_timer which uses it.
        self.SCREEN_UPDATE = pygame.USEREVENT + 1

        # Initialize fonts
        try:
            self.hud_font = load_font("dpcomic.ttf", 30)
            self.title_font = load_font("dpcomic.ttf", 50)
            self.score_font = load_font("dpcomic.ttf", 25) # Needed by _setup_game_instance for apple_score_icon
            self.small_font = load_font("dpcomic.ttf", 18)
            self.ui_font = load_font("dpcomic.ttf", 35)    # For UI elements
        except Exception as e:
            print(f"Error loading fonts: {e}")
            self.hud_font = pygame.font.SysFont("arial", 24)
            self.title_font = pygame.font.SysFont("arial", 40)
            self.score_font = pygame.font.SysFont("arial", 20)
            self.small_font = pygame.font.SysFont("arial", 16)
            self.ui_font = pygame.font.SysFont("arial", 30)

        # Initialize UI elements (needs fonts, screen_width, screen_height)
        self._initialize_ui_elements()

        # Initialize game elements, cell_size, game_area_rect etc.
        # This also sets self.cell_number based on current_difficulty_settings
        self._setup_game_instance() # This will also set self.score = 0

        # Initialize menu animation
        self.current_menu_frame_index = 0
        try:
            self.main_menu_frames = load_gif_frames("main_menu_bg.gif",
                                                scale=(self.screen_width, self.screen_height))
        except Exception as e: # General exception for GIF loading
            print(f"Error loading main menu GIF: {e}")
            placeholder = pygame.Surface((self.screen_width, self.screen_height))
            placeholder.fill(COLOR_DARK_GREEN)
            self.main_menu_frames = [placeholder]

        # Initialize sound
        sound_manager.set_volume(self.volume)
        # Start background music
        sound_manager.play_music()

        # Note: self._update_game_timer() is now called at the end of _setup_game_instance()

    def _calculate_dynamic_dimensions(self):
        """
        Calculates cell_size, game surface dimensions, and game area offsets
        based on the current self.cell_number and fixed game area dimensions.
        Updates self.game_area_rect.
        This method is called when cell_number changes (e.g., due to difficulty change).
        """
        if not isinstance(self.cell_number, int) or self.cell_number <= 0:
            print(f"Warning: Invalid cell_number ({self.cell_number}). Defaulting to 20.")
            self.cell_number = 20 # Fallback to a sensible default

        # Prevent division by zero if game_area_width/height is zero for some reason
        if self.game_area_width <= 0 or self.game_area_height <= 0:
            print(f"Warning: game_area_width ({self.game_area_width}) or game_area_height ({self.game_area_height}) is non-positive. Cannot calculate cell_size.")
            self.cell_size = 10 # Arbitrary fallback
            self.game_surface_width = self.cell_number * self.cell_size
            self.game_surface_height = self.cell_number * self.cell_size
            self.game_area_offset_x = 0
            self.game_area_offset_y = 0
            self.game_area_rect = pygame.Rect(0,0,0,0)
            return

        max_cell_width = self.game_area_width // self.cell_number
        max_cell_height = self.game_area_height // self.cell_number
        self.cell_size = min(max_cell_width, max_cell_height)

        if self.cell_size <= 0:
            print(f"Warning: Calculated cell_size is non-positive ({self.cell_size}). game_area_width={self.game_area_width}, game_area_height={self.game_area_height}, cell_number={self.cell_number}. Using fallback cell_size=10.")
            self.cell_size = 10 

        self.game_surface_width = self.cell_number * self.cell_size
        self.game_surface_height = self.cell_number * self.cell_size

        self.game_area_offset_x = (self.game_area_width - self.game_surface_width) // 2
        self.game_area_offset_y = (self.game_area_height - self.game_surface_height) // 2
        
        self.game_area_rect = pygame.Rect(
            self.game_area_offset_x,
            self.game_area_offset_y,
            self.game_surface_width,
            self.game_surface_height
        )
        # print(f"Dynamic dimensions calculated: cell_number={self.cell_number}, cell_size={self.cell_size}")

    def _setup_game_instance(self):
        """Initializes or re-initializes game objects based on current difficulty."""
        self.cell_number = self.current_difficulty_settings["cell_number"]
        
        self._calculate_dynamic_dimensions() 

        self.world_tileset = get_tileset("world_tileset.png", 16, 16, self.cell_size)
        self.apple_sprites = load_apple_sprites(self.cell_size)
        self.apple_score_icon = None
        if hasattr(self, 'score_font') and self.score_font and "good" in self.apple_sprites:
             self.apple_score_icon = pygame.transform.scale(self.apple_sprites["good"], (self.score_font.get_height(), self.score_font.get_height()))
        else:
            print("Warning: score_font or apple_sprites not ready for apple_score_icon in _setup_game_instance")
            self.apple_score_icon = None


        self.background = Background(self.cell_size, self.cell_number)

        initial_snake_pos = Vector2(self.cell_number // 4, self.cell_number // 2)
        self.snake = Snake(self.cell_size, self.cell_number, initial_pos=initial_snake_pos, color=self.snake_color)
        
        self.apples = []
        self.wall = Wall(self.cell_size, self.cell_number)

        self.score = 0
        self._reset_level_state()
        self._update_game_timer()

    def _initialize_ui_elements(self):
        """Create UI elements for menus"""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        button_width = 250
        button_height = 60
        button_spacing = 20  # Define button_spacing
        back_button_size = (120, 50) # Define back_button_size
        input_field_height = 50
        small_button_width = 120 # For color cycling
        text_label_y_offset = 40 # Offset for "Color:" label
        color_selector_y_offset = text_label_y_offset + 35 # Offset for color buttons/text

        # Name input elements
        self.name_input = TextInput(
            center_x - 150, center_y - input_field_height - 50, # Moved up
            300, input_field_height, self.ui_font
        )

        # Snake Color Selection UI for Name Input
        self.prev_color_button_name_input = Button(
            center_x - small_button_width - 70, # Positioned to the left of color display
            center_y + color_selector_y_offset - 50,
            small_button_width, button_height - 10, "<", self.ui_font,
            action=lambda: self._cycle_snake_color_name_input(-1)
        )
        self.next_color_button_name_input = Button(
            center_x + 70, # Positioned to the right of color display
            center_y + color_selector_y_offset - 50,
            small_button_width, button_height - 10, ">", self.ui_font,
            action=lambda: self._cycle_snake_color_name_input(1)
        )

        self.name_confirm_button = Button(
            center_x - 100, center_y + button_height + color_selector_y_offset - 30, # Moved down
            200, 50, "Confirm", self.ui_font,
            action=lambda: self._handle_name_confirmation()
        )

        # Main menu buttons
        self.play_button = Button(
            center_x - button_width // 2, center_y - 120,
            button_width, button_height, "Play", self.ui_font,
            action=lambda: self._go_to_level_select()
        )

        self.options_button = Button(
            center_x - button_width // 2, center_y,
            button_width, button_height, "Options", self.ui_font,
            action=lambda: self._change_state(GameState.OPTIONS_MENU)
        )

        self.quit_button = Button(
            center_x - button_width // 2, center_y + 120,
            button_width, button_height, "Quit Game", self.ui_font,
            action=lambda: self._change_state(GameState.QUITTING)
        )

        # Options menu buttons
        self.difficulty_buttons = {}
        for i, difficulty in enumerate(DIFFICULTY_SETTINGS):
            self.difficulty_buttons[difficulty] = Button(
                center_x - button_width // 2, center_y - 150 + i * (button_height + 15),
                button_width, button_height, difficulty, self.ui_font,
                color=(30, 100, 30) if difficulty == self.difficulty else COLOR_BUTTON_NORMAL,
                action=lambda diff=difficulty: self._select_difficulty(diff)
            )

        # Volume control slider in options menu - position it below all difficulty buttons
        last_difficulty_button_y = center_y - 150 + (len(DIFFICULTY_SETTINGS) - 1) * (button_height + 15)
        self.volume_slider = Slider(
            center_x - button_width // 2, last_difficulty_button_y + button_height + 30,
            button_width, button_height // 2, 0.0, 1.0, self.volume,
            "Volume", self.ui_font,
            on_change=self._set_volume
        )
        
        # Change name button in options
        self.change_name_button = Button(
            center_x - button_width // 2, last_difficulty_button_y + button_height + 80,
            button_width, button_height, "Change Name", self.ui_font,
            action=lambda: self._go_to_change_name()
        )

        # Back buttons for various menus
        self.options_back_button = Button(
            50, self.screen_height - 70,
            back_button_size[0], back_button_size[1], "Back", self.ui_font, # Use back_button_size
            color=COLOR_BUTTON_BACK_NORMAL, hover_color=COLOR_BUTTON_BACK_HOVER,
            action=lambda: self._change_state(GameState.MAIN_MENU)
        )

        # Level select buttons
        # These will be created dynamically when entering level select menu
        # self.level_buttons will store lists of Button objects, keyed by difficulty string.
        self.level_buttons: Dict[str, List[Button]] = {} # Initialize as an empty dict
        # Keep track of the difficulty for which buttons were last generated
        self._last_difficulty_for_level_buttons: Optional[str] = None
        self._last_player_id_for_level_buttons: Optional[int] = None

        self.level_select_back_button = Button(
            50, self.screen_height - 70,
            back_button_size[0], back_button_size[1], "Back", self.ui_font, # Use back_button_size
            color=COLOR_BUTTON_BACK_NORMAL, hover_color=COLOR_BUTTON_BACK_HOVER,
            action=lambda: self._change_state(GameState.MAIN_MENU)
        )
        
        # Game over buttons
        self.retry_button = Button(
            center_x - button_width // 2, center_y,
            button_width, button_height, "Try Again", self.ui_font,
            action=lambda: self._retry_game()
        )

        self.game_over_main_menu_button = Button(
            center_x - button_width // 2, center_y + button_height + button_spacing, # Use button_spacing
            button_width, button_height, "Main Menu", self.ui_font,
            action=lambda: self._change_state(GameState.MAIN_MENU)
        )
        
        # Level transition buttons
        self.next_level_button = Button(
            center_x - button_width // 2, center_y + 80,
            button_width, button_height, "Next Level", self.ui_font,
            action=lambda: self._advance_to_next_level()
        )
        
        self.main_menu_return_button = Button(
            center_x - button_width // 2, center_y + button_height + 100,
            button_width, button_height, "Main Menu", self.ui_font,
            action=lambda: self._change_state(GameState.MAIN_MENU)
        )

        # Game UI buttons (pause, resume, etc)
        pause_button_size = (80, 40)
        self.pause_button = Button(
            self.screen_width - HUD_WIDTH + 20, 20,
            pause_button_size[0], pause_button_size[1], "Pause", self.small_font,
            action=lambda: self._toggle_pause()
        )

        self.resume_button = Button(
            center_x - button_width // 2, center_y - button_height - button_spacing,
            button_width, button_height, "Resume", self.ui_font,
            action=lambda: self._toggle_pause()
        )

        self.paused_main_menu_button = Button(
            center_x - button_width // 2, center_y + button_spacing,
            button_width, button_height, "Main Menu", self.ui_font,
            action=lambda: self._change_state(GameState.MAIN_MENU)
        )

        # Snake Color Selection UI for Options Menu
        self.options_color_buttons: Dict[str, Button] = {}
        color_button_y_start = self.change_name_button.rect.bottom + 30
        color_button_width_small = 100
        color_button_height_small = 40
        num_colors = len(SNAKE_COLORS_AVAILABLE)
        total_color_button_width = num_colors * color_button_width_small + (num_colors - 1) * 10 # 10px spacing
        start_x_color_buttons = center_x - total_color_button_width // 2

        for i, color_name in enumerate(SNAKE_COLORS_AVAILABLE):
            button_x = start_x_color_buttons + i * (color_button_width_small + 10)
            btn = Button(
                button_x, color_button_y_start,
                color_button_width_small, color_button_height_small, color_name.capitalize(), self.small_font, # Using small_font
                action=lambda c=color_name: self._select_snake_color(c)
            )
            self.options_color_buttons[color_name] = btn

    def _set_volume(self, volume: float):
        """Set volume for all game sounds"""
        self.volume = volume
        sound_manager.set_volume(volume)
        if self.player_id:
            self.player_db.update_player_volume(self.player_id, volume)
            
    def _handle_options_menu_events(self, event: pygame.event.Event):
        # Handle difficulty button clicks
        for difficulty, button in self.difficulty_buttons.items():
            if button.handle_event(event):
                sound_manager.play_sound("menu_button")
                return True

        # Handle volume slider
        if self.volume_slider.handle_event(event):
            return True

        # Handle change name button
        if self.change_name_button.handle_event(event):
            sound_manager.play_sound("menu_button")
            return True

        # Handle snake color buttons
        if event.type == pygame.MOUSEBUTTONDOWN:
            for color_name, button in self.options_color_buttons.items():
                if button.handle_event(event):
                    # _select_snake_color will play sound and update DB
                    return
        if self.options_back_button.handle_event(event): 
            sound_manager.play_sound("menu_button")
            return
        return False

    def _update_game_timer(self):
        pygame.time.set_timer(self.SCREEN_UPDATE, int(self.current_difficulty_settings["base_speed"]))

    def _change_state(self, new_state: GameState):
        """Handle transitions between game states with appropriate sounds"""
        old_state = self.game_state
        
        print(f"Changing state from {self.game_state} to {new_state}")
        self.game_state = new_state
        self.state_transition_time = pygame.time.get_ticks()
        
        # Play appropriate transition sound
        self._play_transition_sound(old_state, new_state)
        
        # Special state handling
        if new_state == GameState.PLAYING:
            if self.snake: 
                self.snake.direction = Vector2(1, 0) # Start moving
            self.last_wall_change_time = pygame.time.get_ticks()
            
        elif new_state == GameState.MAIN_MENU:
            # No full reset if coming from options or game over, just ensure music/timers are right for menu
            pass
        elif new_state == GameState.NAME_INPUT:
            self.name_input.set_text("") # Clear input field
        elif new_state == GameState.CHANGE_NAME:
            current_name = self.player_db.get_player_data(self.player_id)["name"] if self.player_id else ""
            self.new_name_input.set_text(current_name)


    def _reset_level_state(self):
        """Resets elements for the start of a new level or game, keeping score if advancing level."""
        if self.snake: self.snake.reset()
        
        # Apples
        self.apples.clear()
        self.last_apple_spawn_time.clear()
        self._spawn_initial_apples()

        # Walls
        if self.wall:
            num_obstacles = self.level_manager.get_num_obstacles()
            apple_current_positions = [apple.pos for apple in self.apples if apple.is_active]
            self.wall.generate(num_obstacles, self.snake.body if self.snake else [], apple_current_positions)
        
        if self.background:
            self.background.set_level_background(self.level_manager.get_level_number())

        self.last_wall_change_time = pygame.time.get_ticks()
        if self.snake: self.snake.direction = Vector2(0,0) # Will be set to (1,0) when PLAYING state entered

    def _full_game_reset(self, reset_player_too=False, keep_current_level_index=False):
        """Resets the entire game state for a new game (e.g., after game over and play again)."""
        # Remember the current level index if we need to preserve it
        current_level_idx = self.level_manager.current_level_index if keep_current_level_index else 0
        
        if not keep_current_level_index:
            self.level_manager.reset_progress() # Reset to level 1 (index 0) of the current difficulty
        
        # Ensure difficulty in level_manager matches the game controller's current difficulty for this reset
        self.level_manager.set_difficulty(self.difficulty) # This will reset current_level_index to 0
        
        # Restore the level index if needed
        if keep_current_level_index:
            self.level_manager.current_level_index = current_level_idx
            
        self.current_difficulty_settings = DIFFICULTY_SETTINGS[self.difficulty]
        
        # _setup_game_instance re-initializes snake, walls, apples, bg, score, and calls _reset_level_state.
        # _reset_level_state will use the level_manager.current_level_index (which is now correctly set or preserved).
        self._setup_game_instance() 
        # self.score = 0 # score is already reset within _setup_game_instance -> _reset_level_state or directly in _setup_game_instance

        if reset_player_too:
            self.player_name = DEFAULT_PLAYER_NAME
            self.player_id = None
            self._change_state(GameState.NAME_INPUT) # Go back to name input
        else:
            # If not resetting player, but difficulty might have changed.
             self._update_game_timer() # Update speed if difficulty changed


    def _play_again(self):
        self._full_game_reset(reset_player_too=False, keep_current_level_index=False)
        self._change_state(GameState.PLAYING)

    def _advance_to_next_level(self):
        completed_level_number = self.level_manager.get_level_number()
        if self.level_manager.advance_level():
            if self.player_id is not None:
                self.player_db.unlock_next_level(self.player_id, self.difficulty, completed_level_number)
            self._reset_level_state() 
            if self.background: self.background.set_level_background(self.level_manager.get_level_number())
            self._change_state(GameState.PLAYING)
        else: 
            if self.player_id is not None: # Game completed for this difficulty
                self.player_db.unlock_next_level(self.player_id, self.difficulty, completed_level_number) # Unlock final level if structure allows
            self._trigger_game_completed()

    def _select_difficulty(self, difficulty: str):
        """Set the difficulty without changing the state - just update UI and settings"""
        # Update settings instead of redirecting to level selection
        self.difficulty = difficulty
        self.current_difficulty_settings = DIFFICULTY_SETTINGS[difficulty]
        
        # Update button colors to show the selected difficulty
        for diff, button in self.difficulty_buttons.items():
            if diff == self.difficulty:
                button.color = (30, 100, 30)  # Highlight selected difficulty
            else:
                button.color = COLOR_BUTTON_NORMAL
        
        # Update the game timer to reflect new difficulty
        self._update_game_timer()
        
        # Store difficulty preference in database if player exists
        if self.player_id:
            self.player_db.update_player_difficulty(self.player_id, difficulty)
            
        # Play feedback sound
        sound_manager.play_sound("menu_button")

    def _start_level(self, level_index: int):
        if self.selected_difficulty_for_level_select is None:
            self._change_state(GameState.DIFFICULTY_SELECT) 
            return

        self.difficulty = self.selected_difficulty_for_level_select
        self.current_difficulty_settings = DIFFICULTY_SETTINGS[self.difficulty]
        
        self.level_manager.set_difficulty(self.difficulty)
        
        self.level_manager.current_level_index = level_index 
        
        self._full_game_reset(reset_player_too=False, keep_current_level_index=True)
        
        self._change_state(GameState.PLAYING)

    def run(self):
        while self.game_state != GameState.QUITTING:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._change_state(GameState.QUITTING)
                    break
                self._handle_current_state_events(event)
            if self.game_state == GameState.QUITTING: break

            self._update_current_state_logic(current_time)
            self._update_hover_states(mouse_pos)
            self._draw_current_state(current_time)

            pygame.display.flip()
            self.clock.tick(60) # Target 60 FPS for animations, game logic tied to SCREEN_UPDATE timer

        pygame.quit()
        sys.exit()

    def _handle_current_state_events(self, event):
        # Universal key presses (like ESC for pause if in PLAYING)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.game_state == GameState.PLAYING:
                self._change_state(GameState.PAUSED)
                return # Consume event

        # State-specific event handling
        if self.game_state == GameState.NAME_INPUT:
            if self.name_input.handle_event(event): 
                # If enter is pressed in text input, consider it a confirm
                self._handle_name_confirmation()
                return
            if self.name_confirm_button.handle_event(event): 
                sound_manager.play_sound("menu_button")
                # _handle_name_confirmation is called by button's action
                return
            if self.prev_color_button_name_input.handle_event(event):
                # Action handles sound and logic
                return
            if self.next_color_button_name_input.handle_event(event):
                # Action handles sound and logic
                return
        elif self.game_state == GameState.MAIN_MENU:
            if self.play_button.handle_event(event): 
                sound_manager.play_sound("menu_button")
                return
            if self.options_button.handle_event(event): 
                sound_manager.play_sound("menu_button")
                return
            if self.quit_button.handle_event(event):
                sound_manager.play_sound("menu_button")
                return
        elif self.game_state == GameState.OPTIONS_MENU:
            # Handle difficulty buttons
            for button in self.difficulty_buttons.values():
                if button.handle_event(event):
                    sound_manager.play_sound("menu_button")
                    return
            # Handle volume slider
            if self.volume_slider.handle_event(event):
                return
            # Handle change name button
            if self.change_name_button.handle_event(event):
                sound_manager.play_sound("menu_button")
                return
            # Handle snake color buttons
            if event.type == pygame.MOUSEBUTTONDOWN:
                for color_name, button in self.options_color_buttons.items():
                    if button.handle_event(event):
                        # _select_snake_color will play sound and update DB
                        return
            if self.options_back_button.handle_event(event): 
                sound_manager.play_sound("menu_button")
                return
        elif self.game_state == GameState.CHANGE_NAME:
            if self.new_name_input.handle_event(event):
                self._try_update_player_name()
                return
            if self.submit_new_name_button.handle_event(event):
                sound_manager.play_sound("menu_button")
                return
            if self.cancel_name_change_button.handle_event(event):
                sound_manager.play_sound("menu_button")
                return
        elif self.game_state == GameState.LEVEL_SELECT:
            # Handle level selection buttons using current_buttons
            if hasattr(self, 'current_buttons'):
                for button in self.current_buttons:
                    if button and hasattr(button, 'handle_event') and button.handle_event(event):
                        sound_manager.play_sound("menu_button")
                        return
        elif self.game_state == GameState.PLAYING:
            self._handle_playing_events(event) # This one is different, handles key presses and SCREEN_UPDATE
        elif self.game_state == GameState.PAUSED:
            if self.resume_button.handle_event(event): 
                sound_manager.play_sound("menu_button")
                return
            if self.paused_main_menu_button.handle_event(event): 
                sound_manager.play_sound("menu_button")
                return
        elif self.game_state == GameState.LEVEL_TRANSITION:
            if pygame.time.get_ticks() - self.state_transition_time > self.level_transition_duration:
                if self.next_level_button.handle_event(event): 
                    sound_manager.play_sound("menu_button")
                    return
                if self.main_menu_return_button.handle_event(event): 
                    sound_manager.play_sound("menu_button")
                    return
        elif self.game_state == GameState.GAME_OVER:
            if self.retry_button.handle_event(event): 
                sound_manager.play_sound("menu_button")
                return
            if self.game_over_main_menu_button.handle_event(event): # Corrected button
                sound_manager.play_sound("menu_button")
                return


    def _update_current_state_logic(self, current_time: int):
        if self.game_state == GameState.NAME_INPUT:
            self.name_input.update()
        elif self.game_state == GameState.CHANGE_NAME:
            self.new_name_input.update()
        elif self.game_state == GameState.WELCOME:
            if current_time - self.state_transition_time > self.welcome_duration:
                self._change_state(GameState.MAIN_MENU)
        elif self.game_state == GameState.PLAYING:
            # Game logic updates are tied to SCREEN_UPDATE event in _handle_playing_events
            # But apple state updates (visual expiry) can happen per frame
            for apple in self.apples:
                if apple.is_active:
                    apple.update_state(current_time)
                    if apple.state == AppleState.EXPIRED:
                        self._handle_apple_despawn(apple)
        
        # Animate menu background
        menu_states_for_gif_update = [
            GameState.NAME_INPUT, GameState.MAIN_MENU, 
            GameState.OPTIONS_MENU, GameState.DIFFICULTY_SELECT, 
            GameState.LEVEL_SELECT,
            GameState.CHANGE_NAME, GameState.WELCOME
        ]
        if self.game_state in menu_states_for_gif_update:
            self.current_menu_frame_index = (self.current_menu_frame_index + 1) % len(self.main_menu_frames)


    def _update_hover_states(self, mouse_pos):
        """Update button hover states based on mouse position"""
        # Update hover states for buttons based on the current state
        if self.game_state == GameState.NAME_INPUT:
            self.name_confirm_button.check_hover(mouse_pos)
            self.prev_color_button_name_input.check_hover(mouse_pos)
            self.next_color_button_name_input.check_hover(mouse_pos)
        elif self.game_state == GameState.MAIN_MENU:
            self.play_button.check_hover(mouse_pos)
            self.options_button.check_hover(mouse_pos)
            self.quit_button.check_hover(mouse_pos)
        elif self.game_state == GameState.OPTIONS_MENU:
            for button in self.difficulty_buttons.values():
                button.check_hover(mouse_pos)
            self.volume_slider.check_hover(mouse_pos)
            self.change_name_button.check_hover(mouse_pos)
            for button in self.options_color_buttons.values(): # Add hover for color buttons
                button.check_hover(mouse_pos)
            self.options_back_button.check_hover(mouse_pos)
        elif self.game_state == GameState.CHANGE_NAME:
            # TextInput objects don't have check_hover method
            self.submit_new_name_button.check_hover(mouse_pos)
            self.cancel_name_change_button.check_hover(mouse_pos)
        elif self.game_state == GameState.LEVEL_SELECT:
            # Update hover for all active buttons (stored in current_buttons)
            if hasattr(self, 'current_buttons'):
                for button in self.current_buttons:
                    if button and hasattr(button, 'check_hover'):
                        button.check_hover(mouse_pos)
        elif self.game_state == GameState.PAUSED:
            self.resume_button.check_hover(mouse_pos)
            self.paused_main_menu_button.check_hover(mouse_pos)
        elif self.game_state == GameState.GAME_OVER:
            self.retry_button.check_hover(mouse_pos)
            self.game_over_main_menu_button.check_hover(mouse_pos) # Corrected button
        elif self.game_state == GameState.LEVEL_TRANSITION:
            if pygame.time.get_ticks() - self.state_transition_time > self.level_transition_duration:
                self.next_level_button.check_hover(mouse_pos)
                self.main_menu_return_button.check_hover(mouse_pos)

    # --- State Drawing ---
    def _draw_current_state(self, current_time: int):
        """Draw the current game state"""
        # First, draw the base background for all states
        if hasattr(self, 'main_menu_frames') and self.main_menu_frames and self.game_state not in [GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER, GameState.LEVEL_TRANSITION]:
            # Animated menu background for main menu and related states
            self.screen.blit(self.main_menu_frames[self.current_menu_frame_index], (0, 0))
        else:
            self.screen.fill(COLOR_DARK_GREEN)

        # Draw title text for all non-playing states
        if self.game_state != GameState.PLAYING and self.game_state != GameState.PAUSED and self.game_state != GameState.LEVEL_TRANSITION and self.game_state != GameState.GAME_OVER:
            title_surf = self.title_font.render("SNAKE GAME", True, COLOR_WHITE)
            title_rect = title_surf.get_rect(center=(self.screen_width // 2, 80))
            self.screen.blit(title_surf, title_rect)

        # Draw state-specific content
        if self.game_state == GameState.NAME_INPUT:
            self._draw_name_input_state()
        elif self.game_state == GameState.WELCOME:
            self._draw_welcome_state()
        elif self.game_state == GameState.MAIN_MENU:
            self._draw_main_menu_state()
        elif self.game_state == GameState.OPTIONS_MENU:
            self._draw_options_menu()
        elif self.game_state == GameState.CHANGE_NAME:
            self._draw_change_name_state()
        elif self.game_state == GameState.LEVEL_SELECT:
            self._draw_level_select_state()
        elif self.game_state == GameState.PLAYING:
            self._draw_playing_state()
        elif self.game_state == GameState.PAUSED:
            self._draw_paused_state()
        elif self.game_state == GameState.LEVEL_TRANSITION:
            self._draw_level_transition_state(current_time)
        elif self.game_state == GameState.GAME_OVER:
            self._draw_game_over_state()
        elif self.game_state == GameState.GAME_COMPLETED:
            self._draw_game_completed_state()


    def _draw_name_input_state(self):
        self._draw_centered_text("Enter Your Name:", self.ui_font, COLOR_WHITE, self.screen_width // 2, self.screen_height // 2 - 120) # Adjusted Y
        self.name_input.draw(self.screen)

        # Draw "Color:" label
        color_label_surf = self.small_font.render("Snake Color:", True, COLOR_WHITE)
        color_label_rect = color_label_surf.get_rect(center=(self.screen_width // 2, self.name_input.rect.bottom + 40)) # Adjusted Y
        self.screen.blit(color_label_surf, color_label_rect)

        # Draw color selection UI
        self.prev_color_button_name_input.draw(self.screen)
        self.next_color_button_name_input.draw(self.screen)

        # Display current color text
        color_text_surf = self.ui_font.render(self.snake_color.capitalize(), True, COLOR_WHITE)
        color_text_rect = color_text_surf.get_rect(center=(self.screen_width // 2, self.prev_color_button_name_input.rect.centery))
        self.screen.blit(color_text_surf, color_text_rect)
        
        self.name_confirm_button.draw(self.screen) # Adjusted Y implicitly by its definition

    def _draw_welcome_state(self):
        self._draw_overlay_message(f"Welcome, {self.player_name}!", title_font=self.title_font, y_offset_factor=0.5)

    def _draw_main_menu_state(self):
        self.play_button.draw(self.screen)
        self.options_button.draw(self.screen)
        self.quit_button.draw(self.screen)
        
    def _draw_options_menu(self):
        """Draw options menu"""
        # First, draw menu animation or background
        if hasattr(self, 'main_menu_frames') and self.main_menu_frames:
            self.screen.blit(self.main_menu_frames[self.current_menu_frame_index], (0, 0))
        else:
            self.screen.fill(COLOR_DARK_GREEN)

        # Draw title
        title_surf = self.title_font.render("Options", True, COLOR_WHITE)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)

        # Draw current difficulty setting
        current_difficulty_surf = self.ui_font.render(
            f"Current Difficulty: {self.difficulty}", True, COLOR_WHITE
        )
        current_difficulty_rect = current_difficulty_surf.get_rect(
            center=(self.screen_width // 2, 160)
        )
        self.screen.blit(current_difficulty_surf, current_difficulty_rect)

        # Draw difficulty buttons
        for button in self.difficulty_buttons.values():
            button.draw(self.screen)

        # Draw volume slider
        self.volume_slider.draw(self.screen)
        
        # Draw change name button
        self.change_name_button.draw(self.screen)

        # Draw Snake Color Selection UI
        color_label_surf = self.small_font.render("Snake Color:", True, COLOR_WHITE)
        color_label_rect = color_label_surf.get_rect(center=(self.screen_width // 2, self.change_name_button.rect.bottom + 15))
        self.screen.blit(color_label_surf, color_label_rect)
        
        for color_name, button in self.options_color_buttons.items():
            if color_name == self.snake_color:
                button.color = COLOR_BUTTON_HIGHLIGHT
                button.hover_color = COLOR_BUTTON_HIGHLIGHT_HOVER
                button.text_color = COLOR_BLACK
            else:
                button.color = COLOR_BUTTON_NORMAL
                button.hover_color = COLOR_BUTTON_HOVER
                button.text_color = COLOR_WHITE
            button._render_text()
            button.draw(self.screen)

        self.options_back_button.draw(self.screen)

    def _draw_change_name_state(self):
        self._draw_centered_text("Enter New Name:", self.ui_font, COLOR_WHITE, self.screen_width // 2, self.screen_height // 2 - 80)
        self.new_name_input.draw(self.screen)
        self.submit_new_name_button.draw(self.screen)
        self.cancel_name_change_button.draw(self.screen)
        self.current_buttons = [self.submit_new_name_button, self.cancel_name_change_button]


    def _draw_difficulty_select_state(self):
        self._draw_centered_text("SELECT DIFFICULTY", self.ui_font, COLOR_WHITE, self.screen_width // 2, int(self.screen_height // 3.8))
        for btn in self.difficulty_buttons.values(): btn.draw(self.screen)
        self.current_buttons = list(self.difficulty_buttons.values())

    def _draw_level_select_state(self):
        self._draw_centered_text(f"SELECT LEVEL ({self.selected_difficulty_for_level_select})", 
                                 self.ui_font, COLOR_WHITE, 
                                 self.screen_width // 2, int(self.screen_height // 4.2))
        
        self.current_buttons = []

        if self.player_id is None or self.selected_difficulty_for_level_select is None:
            self._draw_centered_text("Error: Player or difficulty not set.", self.ui_font, COLOR_RED, self.screen_width // 2, self.screen_height // 2)
            self.level_select_back_button.draw(self.screen)
            self.current_buttons.append(self.level_select_back_button)
            return

        difficulty_key = self.selected_difficulty_for_level_select

        regenerate_buttons = False
        if (difficulty_key not in self.level_buttons or 
            self._last_difficulty_for_level_buttons != difficulty_key or 
            self._last_player_id_for_level_buttons != self.player_id):
            regenerate_buttons = True
            self.level_buttons[difficulty_key] = []
            self._last_difficulty_for_level_buttons = difficulty_key
            self._last_player_id_for_level_buttons = self.player_id

        if regenerate_buttons:
            unlocked_level_for_difficulty = self.player_db.get_unlocked_level(self.player_id, difficulty_key)
            levels_for_current_difficulty = self.level_manager.get_levels_for_difficulty(difficulty_key)
            
            num_levels = len(levels_for_current_difficulty)
            if num_levels == 0:
                pass

            button_width, button_height = 120, 50
            spacing = 20
            total_width_of_buttons = num_levels * button_width + (num_levels - 1) * spacing
            start_x = (self.screen_width - total_width_of_buttons) // 2
            button_y = self.screen_height // 2 - button_height // 2

            for i, level_data in enumerate(levels_for_current_difficulty):
                level_num = level_data["level"]
                is_unlocked = level_num <= unlocked_level_for_difficulty
                
                btn_text = f"Lvl {level_num}"
                action = (lambda lvl_idx=i: self._start_level(lvl_idx)) if is_unlocked else None
                
                button_x_pos = start_x + i * (button_width + spacing)

                btn = Button(button_x_pos, button_y, button_width, button_height, btn_text, self.ui_font, 
                             action=action)
                
                if not is_unlocked:
                    btn.color = (100, 100, 100) 
                    btn.hover_color = (100,100,100)
                    btn.text_color = (150,150,150)
                    btn._render_text()
                
                self.level_buttons[difficulty_key].append(btn)

        for btn in self.level_buttons.get(difficulty_key, []):
            btn.draw(self.screen)
            self.current_buttons.append(btn)

        self.level_select_back_button.draw(self.screen)
        self.current_buttons.append(self.level_select_back_button)

    def _draw_playing_state(self):
        # Draw game area
        game_area_surface = pygame.Surface((self.game_surface_width, self.game_surface_height))
        
        if self.background: self.background.draw(game_area_surface)
        if self.wall: self.wall.draw(game_area_surface)
        for apple in self.apples:
            if apple.is_active:
                apple.draw(game_area_surface)
        if self.snake: self.snake.draw(game_area_surface)
        
        # Blit game area surface to main screen with offset to center it
        self.screen.blit(game_area_surface, (self.game_area_offset_x, self.game_area_offset_y))
        
        # Draw HUD on the right side
        self._draw_score_hud()

    def _draw_paused_state(self):
        self._draw_playing_state() # Draw game underneath
        self._draw_overlay_message("PAUSED", title_font=self.title_font, y_offset_factor=0.3)
        self.resume_button.draw(self.screen)
        self.paused_main_menu_button.draw(self.screen)


    def _draw_level_transition_state(self, current_time: int):
        self._draw_playing_state() # Draw semi-transparent game underneath
        title = f"Level {self.level_manager.get_level_number() -1} Complete!" if self.level_manager.current_level_index > 0 else "Get Ready!"
        self._draw_overlay_message(title, title_font=self.title_font, y_offset_factor=0.3)
        
        next_level_num = self.level_manager.get_level_number()
        next_target = self.level_manager.get_target_score()
        self._draw_centered_text(f"Next: Level {next_level_num}", self.ui_font, COLOR_WHITE, self.screen_width//2, self.screen_height//2 - 20)
        self._draw_centered_text(f"Target: {next_target} points", self.ui_font, COLOR_WHITE, self.screen_width//2, self.screen_height//2 + 20)

        if current_time - self.state_transition_time > self.level_transition_duration:
            self.next_level_button.draw(self.screen)
            self.main_menu_return_button.draw(self.screen) # Positioned by _initialize_ui_elements
            self.current_buttons = [self.next_level_button, self.main_menu_return_button]


    def _draw_game_over_state(self):
        self._draw_playing_state()
        self._draw_overlay_message("GAME OVER", color=COLOR_RED, title_font=self.title_font, y_offset_factor=0.3)
        self._draw_centered_text(f"Final Score: {self.score}", self.ui_font, COLOR_WHITE, self.screen_width//2, self.screen_height//2 - 20)
        self._draw_centered_text(f"Reached Level: {self.level_manager.get_level_number()}", self.ui_font, COLOR_WHITE, self.screen_width//2, self.screen_height//2 + 20)
        self.retry_button.draw(self.screen)
        self.game_over_main_menu_button.draw(self.screen)

    def _draw_game_completed_state(self):
        self._draw_playing_state()
        self._draw_overlay_message("VICTORY!", color=COLOR_YELLOW, title_font=self.title_font, y_offset_factor=0.3)
        self._draw_centered_text(f"You beat {self.difficulty} difficulty!", self.ui_font, COLOR_WHITE, self.screen_width//2, self.screen_height//2 - 20)
        self._draw_centered_text(f"Final Score: {self.score}", self.ui_font, COLOR_GREEN, self.screen_width//2, self.screen_height//2 + 20)
        self.main_menu_return_button.draw(self.screen)

    # --- HUD and Drawing Helpers ---
    def _draw_score_hud(self):
        hud_surface = pygame.Surface((HUD_WIDTH, self.screen_height), pygame.SRCALPHA)
        hud_surface.fill(COLOR_HUD_BG)

        text_color = COLOR_BRIGHT_SCORE_TEXT if self.game_state == GameState.PLAYING else COLOR_SCORE_TEXT

        margin = 10
        y_offset = margin
        
        player_text = f"Player: {self.player_name}"
        player_surf = self.small_font.render(player_text, True, text_color)
        hud_surface.blit(player_surf, (margin, y_offset))
        y_offset += player_surf.get_height() + 5

        level_text = f"Level: {self.level_manager.get_level_number()} ({self.difficulty})"
        level_surf = self.small_font.render(level_text, True, text_color)
        hud_surface.blit(level_surf, (margin, y_offset))
        y_offset += level_surf.get_height() + 5
        
        target_score = self.level_manager.get_target_score()
        target_text = f"Target: {target_score}"
        target_surf = self.small_font.render(target_text, True, text_color)
        hud_surface.blit(target_surf, (margin, y_offset))
        y_offset += target_surf.get_height() + 10

        score_str = str(self.score)
        score_surf = self.score_font.render(score_str, True, text_color)
        if self.apple_score_icon:
            icon_x = margin
            icon_y = y_offset + (score_surf.get_height() - self.apple_score_icon.get_height()) // 2
            hud_surface.blit(self.apple_score_icon, (icon_x, icon_y))
            score_x = icon_x + self.apple_score_icon.get_width() + 5
        else:
            score_x = margin
        hud_surface.blit(score_surf, (score_x, y_offset))

        self.screen.blit(hud_surface, (self.game_area_width, 0))


    def _draw_centered_text(self, text: str, font: pygame.font.Font, color: Tuple[int,int,int], center_x: int, center_y: int):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(center_x, center_y))
        self.screen.blit(surf, rect)

    def _draw_overlay_message(self, message: str, color: Tuple[int,int,int] = COLOR_WHITE, title_font=None, y_offset_factor=0.5):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Dark semi-transparent overlay
        self.screen.blit(overlay, (0,0))
        
        font_to_use = title_font if title_font else self.ui_font
        self._draw_centered_text(message, font_to_use, color, self.screen_width // 2, int(self.screen_height * y_offset_factor))


    # --- Event Handling & Logic Sub-functions ---
    def _submit_name(self):
        name = self.name_input.get_text()
        if name:
            self.player_name = name
            self.player_id = self.player_db.add_player(name)
            if self.player_id is not None:
                self._change_state(GameState.WELCOME)
            else: # DB error or some other issue
                self.player_name = DEFAULT_PLAYER_NAME # Fallback
                self.player_id = None
                self._change_state(GameState.MAIN_MENU) # Skip welcome
        # else: stay on name input if empty

    def _go_to_change_name(self):
        """Navigate to the name change screen"""
        if not hasattr(self, 'new_name_input'):
            # Create the new name input and buttons if they don't exist yet
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2
            button_width = 200
            button_height = 50
            button_spacing = 20
            
            self.new_name_input = TextInput(
                center_x - 150, center_y - 25,
                300, 50, self.ui_font
            )
            
            self.submit_new_name_button = Button(
                center_x - button_width - button_spacing // 2, center_y + 50,
                button_width, button_height, "Submit", self.ui_font,
                action=lambda: self._try_update_player_name()
            )
            
            self.cancel_name_change_button = Button(
                center_x + button_spacing // 2, center_y + 50,
                button_width, button_height, "Cancel", self.ui_font,
                action=lambda: self._change_state(GameState.OPTIONS_MENU)
            )
        
        # Set the current name in the input field
        if self.player_id:
            player_data = self.player_db.get_player_data(self.player_id)
            current_name = player_data["name"] if player_data else self.player_name
            self.new_name_input.set_text(current_name)
        
        # Change state to name change screen
        self._change_state(GameState.CHANGE_NAME)

    def _try_update_player_name(self):
        """Attempt to update the player's name and return to options menu"""
        new_name = self.new_name_input.get_text().strip()
        if new_name and self.player_id is not None and new_name != self.player_name:
            success = self.player_db.update_player_name(self.player_id, new_name)
            if success:
                self.player_name = new_name
                print(f"Name successfully changed to: {new_name}")
                sound_manager.play_sound("menu_button")
                self._change_state(GameState.OPTIONS_MENU)
            else:
                # Name might be taken or there was a DB error
                print(f"Failed to change name to {new_name}. It might be taken.")
                # Could show error message on screen
        else:
            # No change needed or empty name
            self._change_state(GameState.OPTIONS_MENU)

    def _handle_playing_events(self, event):
        if event.type == self.SCREEN_UPDATE:
            self._update_game_logic()
        elif event.type == pygame.KEYDOWN and self.snake:
            if event.key == pygame.K_UP and self.snake.direction.y != 1: self.snake.direction = Vector2(0, -1)
            elif event.key == pygame.K_DOWN and self.snake.direction.y != -1: self.snake.direction = Vector2(0, 1)
            elif event.key == pygame.K_LEFT and self.snake.direction.x != 1: self.snake.direction = Vector2(-1, 0)
            elif event.key == pygame.K_RIGHT and self.snake.direction.x != -1: self.snake.direction = Vector2(1, 0)


    def _update_game_logic(self):
        if not self.snake or not self.wall: return

        self.snake.move()
        
        # Check Collisions
        head = self.snake.body[0]
        # Wall collision
        if self.wall.check_collision(head):
            self._trigger_game_over()
            return
        # Edge collision
        if self.snake.check_bounds_collision():
            self._trigger_game_over()
            return
        # Self collision
        if self.snake.check_collision_with_self():
            self._trigger_game_over()
            return

        # Apple collision
        for apple_idx, apple in enumerate(self.apples):
            if apple.is_active and head == apple.pos:
                if apple.state == AppleState.POISONOUS:
                    # Play vomit sound and shrink the snake
                    sound_manager.play_sound("vomit")
                    self.snake.shrink()  # Using new shrink method
                    self.score = max(0, self.score - 1)  # Reduce score but not below 0
                else:
                    # Play crunch sound and grow the snake
                    sound_manager.play_sound("crunch")
                    self.snake.grow()  # Using new grow method
                    self.score += 1
                
                self._handle_apple_despawn(apple, eaten=True)
                break
                
        # Dynamic Wall Changes (if enabled by difficulty)
        obstacle_speed_factor = self.current_difficulty_settings.get("obstacle_speed_factor", 1.0)
        wall_change_interval = 10000 * obstacle_speed_factor # Base 10s, adjusted
        if wall_change_interval < float('inf') and pygame.time.get_ticks() - self.last_wall_change_time > wall_change_interval:
            num_obs = self.level_manager.get_num_obstacles()
            apple_curr_pos = [a.pos for a in self.apples if a.is_active]
            self.wall.generate(num_obs, self.snake.body, apple_curr_pos)
            self.last_wall_change_time = pygame.time.get_ticks()

        # Check for level completion
        if self.level_manager.is_level_complete(self.score):
            if self.level_manager.is_game_complete(): # Last level of difficulty completed
                self._trigger_game_completed()
            else:
                self._change_state(GameState.LEVEL_TRANSITION)

    def _handle_name_confirmation(self):
        """Process player name confirmation"""
        player_name = self.name_input.get_text().strip()
        if not player_name:
            player_name = DEFAULT_PLAYER_NAME
        
        player_id = self.player_db.add_player(player_name)
        if player_id:
            self.player_id = player_id
            self.player_name = player_name

            self.player_db.update_player_snake_color(self.player_id, self.snake_color)

            player_data = self.player_db.get_player_data(player_id)

            if player_data: 
                self.volume = player_data.get("volume", DEFAULT_VOLUME)
                sound_manager.set_volume(self.volume)
                
                loaded_difficulty_from_db = player_data.get("difficulty") 
                self.difficulty = loaded_difficulty_from_db if loaded_difficulty_from_db is not None else DEFAULT_DIFFICULTY
                
                print(f"Player {player_name} (ID: {self.player_id}) processed. Settings: Volume: {self.volume:.2f}, Difficulty: {self.difficulty}, Snake Color: {self.snake_color}")
            else:
                print(f"[WARN] Player {player_name} (ID: {self.player_id}) - no data found after add/update. Using current controller state.")
                self.player_db.update_player_difficulty(self.player_id, self.difficulty)
                self.player_db.update_player_volume(self.player_id, self.volume)

            for diff, button in self.difficulty_buttons.items():
                button.color = COLOR_BUTTON_HIGHLIGHT if diff == self.difficulty else COLOR_BUTTON_NORMAL
                button._render_text()
            
            self._change_state(GameState.WELCOME)
            sound_manager.play_sound("game_start")
        else:
            print(f"Error adding/retrieving player ID for {player_name}. Name might be invalid or DB error.")
            self.name_input.set_text("Error. Try different name.")

    def _spawn_initial_apples(self):
        self.apples.clear()
        self.last_apple_spawn_time.clear()
        num_apples_for_level = self.level_manager.get_num_apples()
        for i in range(num_apples_for_level):
            self._add_new_apple(slot_index=i)
        
    def _ensure_apple_count(self):
        """Manages apple respawning to maintain the correct number for the level."""
        num_apples_for_level = self.level_manager.get_num_apples()
        current_apple_count = sum(1 for apple in self.apples if apple.is_active)
        
        # Find empty slots or respawn inactive apples
        for i in range(num_apples_for_level):
            # Check if an apple for this slot exists and is active
            slot_filled = False
            for apple in self.apples:
                # A simple way to associate an apple with a "slot" is just by count
                # This part can be more complex if apples need unique IDs tied to slots
                pass # For now, just check if we have enough active apples

            if current_apple_count < num_apples_for_level:
                 # Try to find an inactive apple to reactivate or add a new one if list is too short
                found_inactive_to_reuse = False
                for apple_in_list in self.apples:
                    if not apple_in_list.is_active:
                        self._reactivate_apple(apple_in_list)
                        found_inactive_to_reuse = True
                        current_apple_count +=1
                        break
                if not found_inactive_to_reuse and len(self.apples) < num_apples_for_level:
                     self._add_new_apple(slot_index=len(self.apples)) # Add to a new conceptual slot
                     current_apple_count +=1


    def _add_new_apple(self, slot_index: int):
        if not self.world_tileset: return
        new_apple = Fruit(self.cell_size, self.cell_number, self.current_difficulty_settings)
        
        occupied_by_others = [a.pos for a in self.apples if a.is_active]
        new_apple.randomize(self.snake.body if self.snake else [], self.wall.positions if self.wall else [], occupied_by_others)
        
        if new_apple.is_active:
            self.apples.append(new_apple)
            self.last_apple_spawn_time[id(new_apple)] = pygame.time.get_ticks() # Use apple id as key for timer

    def _reactivate_apple(self, apple: Fruit):
        occupied_by_others = [a.pos for a in self.apples if a.is_active and a is not apple]
        apple.randomize(self.snake.body if self.snake else [], self.wall.positions if self.wall else [], occupied_by_others)
        if apple.is_active:
             self.last_apple_spawn_time[id(apple)] = pygame.time.get_ticks()


    def _handle_apple_despawn(self, apple_to_remove: Fruit, eaten: bool = False):
        # Mark as inactive instead of removing from list, to allow for fixed number of Fruit objects
        apple_to_remove.is_active = False
        apple_to_remove.pos = Vector2(-1,-1) # Move off screen

        # Logic to respawn an apple after a delay
        # For simplicity, we'll just call _ensure_apple_count which will try to fill slots.
        # A more robust system might use a timer per apple "slot".
        pygame.time.set_timer(pygame.USEREVENT + 2 + self.apples.index(apple_to_remove), self.level_manager.get_apple_spawn_delay(), True) # One-shot timer
        # The event for this timer should trigger _ensure_apple_count or a specific respawn for that slot.
        # For now, _ensure_apple_count will be called periodically or after an apple is gone.
        self._ensure_apple_count()


    def _trigger_game_over(self):
        """End the game and transition to game over state"""
        print("Game Over triggered!")
        if self.player_id is not None:
            self.player_db.update_player_score(
                self.player_id, self.score, self.difficulty, self.level_manager.get_level_number()
            )
        self._change_state(GameState.GAME_OVER)

    def _trigger_game_completed(self):
        print("Game Completed (difficulty) triggered!")
        if self.player_id is not None:
            self.player_db.update_player_score(
                self.player_id, self.score, self.difficulty, self.level_manager.get_level_number() # Final level
            )
        self._change_state(GameState.GAME_COMPLETED)

    def _play_transition_sound(self, old_state, new_state):
        """Play appropriate sound for state transitions"""
        if old_state == GameState.NAME_INPUT and new_state == GameState.WELCOME:
            # Player just entered their name
            sound_manager.play_sound("game_start")
        elif new_state == GameState.GAME_OVER:
            # Game Over state
            sound_manager.play_sound("game_over")
        elif new_state in [GameState.LEVEL_TRANSITION, GameState.GAME_COMPLETED]:
            # Level completion
            sound_manager.play_sound("level_finished")

    def _handle_button_click(self, event, button):
        """Generic method to handle button clicks with sound"""
        if button.handle_event(event):
            sound_manager.play_sound("menu_button")
            return True
        return False

    def _retry_game(self):
        """Restart the game after game over"""
        self._play_again()
        sound_manager.play_sound("game_start")

    def set_current_name(self, current_name):
        self.new_name_input.set_text(current_name)

    def _toggle_pause(self):
        """Toggle between playing and paused states"""
        if self.game_state == GameState.PLAYING:
            self._change_state(GameState.PAUSED)
        elif self.game_state == GameState.PAUSED:
            self._change_state(GameState.PLAYING)
        sound_manager.play_sound("menu_button")

    def _go_to_level_select(self):
        """Method to go to level selection screen - store current difficulty first"""
        self.selected_difficulty_for_level_select = self.difficulty
        self.level_manager.set_difficulty(self.difficulty) 
        self._change_state(GameState.LEVEL_SELECT)

    def _select_snake_color(self, color: str):
        """Set the snake color, update UI, and save to DB."""
        if color in SNAKE_COLORS_AVAILABLE:
            self.snake_color = color
            sound_manager.play_sound("menu_button")
            print(f"Snake color changed to: {self.snake_color}")

            if self.player_id:
                self.player_db.update_player_snake_color(self.player_id, self.snake_color)

            if self.game_state == GameState.NAME_INPUT:
                self.selected_color_index_name_input = SNAKE_COLORS_AVAILABLE.index(color)
        else:
            print(f"Attempted to select invalid snake color: {color}")

    def _cycle_snake_color_name_input(self, direction: int):
        """Cycles through SNAKE_COLORS_AVAILABLE for the name input screen."""
        current_index = SNAKE_COLORS_AVAILABLE.index(self.snake_color)
        new_index = (current_index + direction) % len(SNAKE_COLORS_AVAILABLE)
        self._select_snake_color(SNAKE_COLORS_AVAILABLE[new_index])