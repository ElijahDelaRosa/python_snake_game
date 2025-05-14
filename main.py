import pygame
from game_controller import GameController
from config import DATABASE_DIR # To ensure directory exists
import os

if __name__ == "__main__":
    # Add this line to suggest centering the window
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    pygame.mixer.pre_init(44100, -16, 2, 512) # Before pygame.init()
    pygame.init()
    pygame.font.init() # Explicitly init font system
    pygame.mixer.init()# Explicitly init mixer

    # Ensure database directory exists
    os.makedirs(DATABASE_DIR, exist_ok=True)

    try:
        game = GameController()
        game.run()
    except Exception as e:
        print(f"An error occurred: {e}")
        pygame.quit()
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()