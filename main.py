import pygame
from game_controller import GameController
from config import DATABASE_DIR 
import os

if __name__ == "__main__":
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    pygame.mixer.pre_init(44100, -16, 2, 512) 
    pygame.init()
    pygame.font.init() 
    pygame.mixer.init()

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