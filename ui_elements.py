import pygame
from typing import Tuple, Callable
from config import (COLOR_BLACK, COLOR_TEXT_INPUT_INACTIVE, COLOR_TEXT_INPUT_ACTIVE,
                    COLOR_WHITE, COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER)
from assets import load_font # Import the centralized font loader

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
        self.blink_speed = 500

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
            if self.active:
                self.cursor_timer = pygame.time.get_ticks()
                self.cursor_visible = True
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < self.max_chars and event.unicode.isprintable():
                self.text += event.unicode
        return False

    def update(self):
        if self.active:
            current_time = pygame.time.get_ticks()
            if current_time - self.cursor_timer > self.blink_speed:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = current_time

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 5, self.rect.centery))
        screen.blit(text_surface, text_rect)
        if self.active and self.cursor_visible:
            cursor_pos_x = text_rect.right + 1
            cursor_y1 = text_rect.top
            cursor_y2 = text_rect.bottom
            pygame.draw.line(screen, self.text_color, (cursor_pos_x, cursor_y1), (cursor_pos_x, cursor_y2), 2)

    def get_text(self) -> str:
        return self.text.strip()

    def set_text(self, text: str):
        self.text = text[:self.max_chars]


class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font,
                 color: Tuple[int, int, int] = COLOR_BUTTON_NORMAL,
                 hover_color: Tuple[int, int, int] = COLOR_BUTTON_HOVER,
                 text_color: Tuple[int, int, int] = COLOR_WHITE, border_radius: int = 12,
                 action: callable = None): # Added action parameter
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.is_hovered = False
        self.action = action # Store the action
        self._render_text()

    def _render_text(self):
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, screen: pygame.Surface):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, self.text_color, self.rect, 3, border_radius=self.border_radius)
        screen.blit(self.text_surf, self.text_rect)

    def check_hover(self, mouse_pos: Tuple[int, int]):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Checks if the button was clicked and executes its action. Returns True if action performed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                print(f"Button '{self.text}' clicked. Action: {self.action}") # DEBUG PRINT
                if self.action:
                    self.action() # Execute the callback
                    return True # Action performed
                return False # No action to perform, but button was clicked
        return False

    def set_position(self, x: int, y: int):
        self.rect.topleft = (x,y)
        self._render_text() # Re-center text

class Slider:
    def __init__(self, x: int, y: int, width: int, height: int, 
                 min_value: float, max_value: float, initial_value: float,
                 label: str, font: pygame.font.Font,
                 color: Tuple[int, int, int] = COLOR_WHITE,
                 handle_color: Tuple[int, int, int] = COLOR_BUTTON_NORMAL,
                 handle_hover_color: Tuple[int, int, int] = COLOR_BUTTON_HOVER,
                 on_change: Callable[[float], None] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.track_rect = pygame.Rect(x + 10, y + height // 2 - 2, width - 20, 4)
        self.handle_size = (20, 20)
        self.handle_rect = pygame.Rect(0, 0, self.handle_size[0], self.handle_size[1])
        
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self._update_handle_position()
        
        self.label = label
        self.font = font
        self.color = color
        self.handle_color = handle_color
        self.handle_hover_color = handle_hover_color
        self.is_hovered = False
        self.is_dragging = False
        self.on_change = on_change
        self._render_label()
        
    def _render_label(self):
        # Create label with current value
        value_text = f"{int(self.value * 100)}%"
        self.label_surf = self.font.render(f"{self.label}: {value_text}", True, self.color)
        self.label_rect = self.label_surf.get_rect(midleft=(self.rect.x, self.rect.y - 15))
        
    def _update_handle_position(self):
        # Convert value to position
        value_range = self.max_value - self.min_value
        if value_range == 0:  # Prevent division by zero
            position_ratio = 0
        else:
            position_ratio = (self.value - self.min_value) / value_range
            
        handle_x = self.track_rect.x + int(position_ratio * self.track_rect.width) - self.handle_size[0] // 2
        handle_y = self.track_rect.centery - self.handle_size[1] // 2
        self.handle_rect.topleft = (handle_x, handle_y)
        
    def _update_value_from_position(self, x_pos: int):
        # Convert position to value
        value_range = self.max_value - self.min_value
        position_ratio = max(0, min(1, (x_pos - self.track_rect.x) / self.track_rect.width))
        self.value = self.min_value + position_ratio * value_range
        self._render_label()
        if self.on_change:
            self.on_change(self.value)
            
    def set_value(self, value: float):
        self.value = max(self.min_value, min(self.max_value, value))
        self._update_handle_position()
        self._render_label()
        if self.on_change:
            self.on_change(self.value)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos):
                self.is_dragging = True
                return True
            elif self.track_rect.collidepoint(event.pos):
                self._update_value_from_position(event.pos[0])
                self._update_handle_position()
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
            
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.handle_rect.collidepoint(event.pos)
            if self.is_dragging:
                self._update_value_from_position(event.pos[0])
                self._update_handle_position()
                return True
                
        return False
        
    def check_hover(self, mouse_pos: Tuple[int, int]):
        self.is_hovered = self.handle_rect.collidepoint(mouse_pos)
        
    def draw(self, screen: pygame.Surface):
        # Draw label
        screen.blit(self.label_surf, self.label_rect)
        
        # Draw track
        pygame.draw.rect(screen, self.color, self.track_rect)
        
        # Draw handle
        current_handle_color = self.handle_hover_color if self.is_hovered or self.is_dragging else self.handle_color
        pygame.draw.circle(screen, current_handle_color, self.handle_rect.center, self.handle_size[0] // 2)
        pygame.draw.circle(screen, self.color, self.handle_rect.center, self.handle_size[0] // 2, 2)