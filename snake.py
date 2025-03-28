import pygame,sys,random, time
from pygame.math import Vector2
from PIL import Image, ImageSequence
from typing import List, Tuple, Optional

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font, 
                 color: Tuple[int, int, int], hover_color: Tuple[int, int, int]):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.text_surf = self.font.render(text, True, (255, 255, 255))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        
    def draw(self, screen: pygame.Surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 3, border_radius=12)
        screen.blit(self.text_surf, self.text_rect)
        
    def check_hover(self, mouse_pos: Tuple[int, int]) -> bool:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
    
    def is_clicked(self, mouse_pos: Tuple[int, int], mouse_clicked: bool) -> bool:
        return self.rect.collidepoint(mouse_pos) and mouse_clicked

class SNAKE:
	def __init__(self, cell_size: int):
		self.body = [Vector2(5,10),Vector2(4,10),Vector2(3,10)]
		self.direction = Vector2(0,0)
		self.new_block = False
		self.cell_size = cell_size

		self.head_up = pygame.image.load('Graphics/head_up.png').convert_alpha()
		self.head_down = pygame.image.load('Graphics/head_down.png').convert_alpha()
		self.head_right = pygame.image.load('Graphics/head_right.png').convert_alpha()
		self.head_left = pygame.image.load('Graphics/head_left.png').convert_alpha()
		
		self.tail_up = pygame.image.load('Graphics/tail_up.png').convert_alpha()
		self.tail_down = pygame.image.load('Graphics/tail_down.png').convert_alpha()
		self.tail_right = pygame.image.load('Graphics/tail_right.png').convert_alpha()
		self.tail_left = pygame.image.load('Graphics/tail_left.png').convert_alpha()

		self.body_vertical = pygame.image.load('Graphics/body_vertical.png').convert_alpha()
		self.body_horizontal = pygame.image.load('Graphics/body_horizontal.png').convert_alpha()

		self.body_tr = pygame.image.load('Graphics/body_tr.png').convert_alpha()
		self.body_tl = pygame.image.load('Graphics/body_tl.png').convert_alpha()
		self.body_br = pygame.image.load('Graphics/body_br.png').convert_alpha()
		self.body_bl = pygame.image.load('Graphics/body_bl.png').convert_alpha()

		self.crunch_sound = pygame.mixer.Sound('Sound/crunch.wav')

		self.head = self.head_right
		self.tail = self.tail_left

	def draw_snake(self, screen: pygame.Surface, cell_size: int):
		self.update_head_graphics()
		self.update_tail_graphics()

		for index,block in enumerate(self.body):
			x_pos = int(block.x * cell_size)
			y_pos = int(block.y * cell_size)
			block_rect = pygame.Rect(x_pos,y_pos,cell_size,cell_size)

			if index == 0:
				screen.blit(self.head,block_rect)
			elif index == len(self.body) - 1:
				screen.blit(self.tail,block_rect)
			else:
				previous_block = self.body[index + 1] - block
				next_block = self.body[index - 1] - block
				if previous_block.x == next_block.x:
					screen.blit(self.body_vertical,block_rect)
				elif previous_block.y == next_block.y:
					screen.blit(self.body_horizontal,block_rect)
				else:
					if previous_block.x == -1 and next_block.y == -1 or previous_block.y == -1 and next_block.x == -1:
						screen.blit(self.body_tl,block_rect)
					elif previous_block.x == -1 and next_block.y == 1 or previous_block.y == 1 and next_block.x == -1:
						screen.blit(self.body_bl,block_rect)
					elif previous_block.x == 1 and next_block.y == -1 or previous_block.y == -1 and next_block.x == 1:
						screen.blit(self.body_tr,block_rect)
					elif previous_block.x == 1 and next_block.y == 1 or previous_block.y == 1 and next_block.x == 1:
						screen.blit(self.body_br,block_rect)

	def update_head_graphics(self):
		head_relation = self.body[1] - self.body[0]
		if head_relation == Vector2(1,0): self.head = self.head_left
		elif head_relation == Vector2(-1,0): self.head = self.head_right
		elif head_relation == Vector2(0,1): self.head = self.head_up
		elif head_relation == Vector2(0,-1): self.head = self.head_down

	def update_tail_graphics(self):
		tail_relation = self.body[-2] - self.body[-1]
		if tail_relation == Vector2(1,0): self.tail = self.tail_left
		elif tail_relation == Vector2(-1,0): self.tail = self.tail_right
		elif tail_relation == Vector2(0,1): self.tail = self.tail_up
		elif tail_relation == Vector2(0,-1): self.tail = self.tail_down

	def move_snake(self):
		if self.new_block == True:
			body_copy = self.body[:]
			body_copy.insert(0,body_copy[0] + self.direction)
			self.body = body_copy[:]
			self.new_block = False
		else:
			body_copy = self.body[:-1]
			body_copy.insert(0,body_copy[0] + self.direction)
			self.body = body_copy[:]

	def add_block(self):
		self.new_block = True

	def play_crunch_sound(self):
		self.crunch_sound.play()

	def reset(self):
		self.body = [Vector2(5,10),Vector2(4,10),Vector2(3,10)]
		self.direction = Vector2(0,0)


class FRUIT:
	def __init__(self, cell_number: int):
		self.cell_number = cell_number
		self.pos = Vector2(0, 0)
		self.randomize()

	def draw_fruit(self, screen: pygame.Surface, cell_size: int, apple: pygame.Surface):
		fruit_rect = pygame.Rect(int(self.pos.x * cell_size),int(self.pos.y * cell_size),cell_size,cell_size)
		screen.blit(apple,fruit_rect)

	def randomize(self):
		self.x = random.randint(0,self.cell_number - 1)
		self.y = random.randint(0,self.cell_number - 1)
		self.pos = Vector2(self.x,self.y)

class WALL:
    def __init__(self, cell_number: int):
        self.cell_number = cell_number
        self.walls: List[Vector2] = []

    def generate_walls(self, min_walls: int, max_walls: int, snake_body: List[Vector2], fruit_pos: Vector2):
        self.walls.clear()
        
        num_walls = random.randint(min_walls, max_walls)
        
        for _ in range(num_walls):
            wall_pos = self.get_unique_position(snake_body, fruit_pos)
            self.walls.append(wall_pos)

    def get_unique_position(self, snake_body: List[Vector2], fruit_pos: Vector2) -> Vector2:
        attempts = 0
        max_attempts = 100  # Prevent infinite loop
        
        while attempts < max_attempts:
            x = random.randint(0, self.cell_number - 1)
            y = random.randint(0, self.cell_number - 1)
            new_pos = Vector2(x, y)
            
            if (new_pos not in snake_body and 
                new_pos != fruit_pos and 
                new_pos not in self.walls):
                return new_pos
            
            attempts += 1
        
        return Vector2(0, 0)

    def draw_walls(self, screen: pygame.Surface, cell_size: int, wall_image: pygame.Surface):
        for wall_pos in self.walls:
            wall_rect = pygame.Rect(
                int(wall_pos.x * cell_size), 
                int(wall_pos.y * cell_size), 
                cell_size, 
                cell_size
            )
            screen.blit(wall_image, wall_rect)

class MAIN:
	DIFFICULTY = {
        "Easy": {
            "speed": 200,
			"wall_count": (3, 5),
            "wall_change_time": float('inf'),
            "apple_poison_time": float('inf')
        },
        "Medium": {
            "speed": 150,
			"wall_count": (5, 7),
            "wall_change_time": 10000,
            "apple_poison_time": 10000
        },
        "Hard": {
            "speed": 100,
			"wall_count": (7, 9),
            "wall_change_time": 5000,
            "apple_poison_time": 5000
        }
    }

	def __init__(self, screen: pygame.Surface, cell_size: int, cell_number: int, 
                 game_font: pygame.font.Font, apple: pygame.Surface, clock: pygame.time.Clock):
		self.screen = screen
		self.cell_size = cell_size
		self.cell_number = cell_number
		self.game_font = game_font
		self.apple = apple
		self.clock = clock
		self.snake = SNAKE(cell_size)
		self.fruit = FRUIT(cell_number)
		self.score = 0
		self.game_active = False
		self.difficulty = "Medium"
		self.game_speed = self.DIFFICULTY[self.difficulty]["speed"]

		self.grass_image_1 = pygame.image.load("Graphics/grass1.png").convert()
		self.grass_image_2 = pygame.image.load("Graphics/grass2.png").convert()
		self.grass_image_1 = pygame.transform.scale(self.grass_image_1, (cell_size, cell_size))
		self.grass_image_2 = pygame.transform.scale(self.grass_image_2, (cell_size, cell_size))

		background = Image.open("Graphics/main_menu_bg.gif")

		self.frames = [
			pygame.image.fromstring(frame.convert("RGBA").tobytes(), frame.size, "RGBA") 
			for frame in ImageSequence.Iterator(background)
		]

		self.scaled_frames = [
			pygame.transform.scale(frame, (cell_number * cell_size, cell_number * cell_size))
			for frame in self.frames
		]

		title_width = cell_number * cell_size
		title_height = cell_size * 2
		title_font = pygame.font.Font('Font/dpcomic.ttf', 50)

		self.title_text = title_font.render("Snake Game", True, (255, 255, 255))
		self.title_rect = self.title_text.get_rect(center=(title_width // 2, title_height // 2))

		self.wall = WALL(cell_number)
		self.wall_image = pygame.image.load('Graphics/wall.PNG').convert_alpha()
		self.wall_image = pygame.transform.scale(self.wall_image, (cell_size, cell_size))

		self.poisonous_apple_image = pygame.image.load('Graphics/poison_apple.png').convert_alpha()
		self.poisonous_apple_image = pygame.transform.scale(self.poisonous_apple_image, (cell_size, cell_size))
        
		self.last_wall_change_time = pygame.time.get_ticks()
		self.last_apple_poison_time = pygame.time.get_ticks()
		self.apple_is_poisonous = False

		self.SCREEN_UPDATE = pygame.USEREVENT
		pygame.time.set_timer(self.SCREEN_UPDATE, self.game_speed)

		self.button_font = pygame.font.Font('Font/dpcomic.ttf', 30)

		self.play_button = None
		self.quit_button = None
		self.diff_buttons = []
		self.back_button = None
		self.initialize_buttons()

	def initialize_buttons(self):
		button_width = 200
		button_height = 60
		center_x = self.cell_number * self.cell_size // 2
        
		self.play_button = Button(
            center_x - button_width // 2, 
            self.cell_number * self.cell_size // 2, 
            button_width, button_height, "PLAY", 
            self.button_font, (56, 74, 12), (76, 94, 32)
        )
        
		self.quit_button = Button(
            center_x - button_width // 2, 
            self.cell_number * self.cell_size // 2 + button_height + 20, 
            button_width, button_height, "QUIT", 
            self.button_font, (56, 74, 12), (76, 94, 32)
        )
        
		diff_button_width = 160
		diff_button_height = 50
		diff_y_start = self.cell_number * self.cell_size // 2
        
		self.diff_buttons = [
            Button(
                center_x - diff_button_width // 2,
                diff_y_start + i * (diff_button_height + 20),
                diff_button_width, diff_button_height, diff,
                self.button_font, (56, 74, 12), (76, 94, 32)
            )
            for i, diff in enumerate(["Easy", "Medium", "Hard"])
        ]
        
		self.back_button = Button(
            center_x - diff_button_width // 2,
            diff_y_start + 3 * (diff_button_height + 20),
            diff_button_width, diff_button_height, "Back",
            self.button_font, (150, 30, 30), (170, 50, 50)
        )

	def update(self):
		current_time = pygame.time.get_ticks()
        
		if current_time - self.last_wall_change_time > self.DIFFICULTY[self.difficulty]["wall_change_time"]:
			wall_range = self.DIFFICULTY[self.difficulty]["wall_count"]
			self.wall.generate_walls(
                wall_range[0], 
                wall_range[1], 
                self.snake.body, 
                self.fruit.pos
            )
			self.last_wall_change_time = current_time
        
		if current_time - self.last_apple_poison_time > self.DIFFICULTY[self.difficulty]["apple_poison_time"]:
			self.apple_is_poisonous = True
			self.last_apple_poison_time = current_time

		self.snake.move_snake()
		self.check_collision()
		self.check_fail()

	def main_menu(self):
		frame_index = 0
		menu_state = "main"

		while True:
			mouse_pos = pygame.mouse.get_pos()
			mouse_clicked = False

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == 1:
						mouse_clicked = True
			
			self.screen.blit(self.scaled_frames[frame_index], (0, 0))

			self.screen.blit(self.title_text, self.title_rect)

			if menu_state == "main":
				self.play_button.check_hover(mouse_pos)
				self.quit_button.check_hover(mouse_pos)

				self.play_button.draw(self.screen)
				self.quit_button.draw(self.screen)

				if self.play_button.is_clicked(mouse_pos, mouse_clicked):
					menu_state = "difficulty"
				elif self.quit_button.is_clicked(mouse_pos, mouse_clicked):
					pygame.quit()
					sys.exit()
			
			elif menu_state == "difficulty":
				diff_text = self.button_font.render("SELECT DIFFICULTY", True, (255, 255, 255))
				diff_rect = diff_text.get_rect(center=(self.cell_number * self.cell_size // 2, 
                                                      self.cell_number * self.cell_size // 3))
				self.screen.blit(diff_text, diff_rect)
                
				for button in self.diff_buttons:
					button.check_hover(mouse_pos)
					button.draw(self.screen)
                    
					if button.is_clicked(mouse_pos, mouse_clicked):
						self.difficulty = button.text
						self.game_speed = self.DIFFICULTY[self.difficulty]["speed"]
						pygame.time.set_timer(self.SCREEN_UPDATE, self.game_speed)

						wall_range = self.DIFFICULTY[self.difficulty]["wall_count"]
						self.wall.generate_walls(
							wall_range[0], 
							wall_range[1],
							self.snake.body, 
							self.fruit.pos
						)

						self.game_active = True
						self.snake.direction = Vector2(1, 0)
						return
                
				self.back_button.check_hover(mouse_pos)
				self.back_button.draw(self.screen)
                
				if self.back_button.is_clicked(mouse_pos, mouse_clicked):
					menu_state = "main"
            
			frame_index = (frame_index + 1) % len(self.frames)

			pygame.display.update()
			self.clock.tick(10)

	def check_collision(self):
		if self.fruit.pos == self.snake.body[0]:
			if self.apple_is_poisonous:
				print("Ate poisonous apple!")
				self.score -= 1
				self.apple_is_poisonous = False
				self.fruit.randomize()
				while (any(block == self.fruit.pos for block in self.snake.body) or 
		   			   any(block == self.fruit.pos for block in self.wall.walls)):
					self.fruit.randomize()
				return

			self.fruit.randomize()
			while (any(block == self.fruit.pos for block in self.snake.body) or 
                   any(block == self.fruit.pos for block in self.wall.walls)):
				self.fruit.randomize()
			
			self.snake.add_block()
			self.snake.play_crunch_sound()
			self.score += 1

			self.apple_is_poisonous = False
			self.last_apple_poison_time = pygame.time.get_ticks()
            
			while any(block == self.fruit.pos for block in self.snake.body):
				self.fruit.randomize()

	def check_fail(self):
		if self.snake.body[0] in self.wall.walls:
			print("Hit wall")
			self.game_over()

		if not 0 <= self.snake.body[0].x < self.cell_number or not 0 <= self.snake.body[0].y < self.cell_number:
			print("Hit edge")
			self.game_over()

		for block in self.snake.body[1:]:
			if block == self.snake.body[0]:
				print("Hit self")
				self.game_over()
		
	def game_over(self):
		self.snake.reset()
		self.score = 0
		self.game_active = False
		self.main_menu()

	def draw_score(self):
		score_text = str(len(self.snake.body) - 3)
		score_surface = self.game_font.render(score_text,True,(56,74,12))
		score_x = int(self.cell_size * self.cell_number - 60)
		score_y = int(self.cell_size * self.cell_number - 40)
		score_rect = score_surface.get_rect(center = (score_x,score_y))
		apple_rect = self.apple.get_rect(midright = (score_rect.left,score_rect.centery))
		bg_rect = pygame.Rect(apple_rect.left,apple_rect.top,apple_rect.width + score_rect.width + 6,apple_rect.height)

		pygame.draw.rect(self.screen,(167,209,61),bg_rect)
		self.screen.blit(score_surface,score_rect)
		self.screen.blit(self.apple,apple_rect)
		pygame.draw.rect(self.screen,(56,74,12),bg_rect,2)

	def draw_grass(self):
		for row in range(self.cell_number):
			for col in range(self.cell_number):
				if (row + col) % 2 == 0:
					grass_rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
					self.screen.blit(self.grass_image_1, grass_rect)
				else:
					grass_rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
					self.screen.blit(self.grass_image_2, grass_rect)

	def draw_elements(self):
		self.draw_grass()

		self.wall.draw_walls(self.screen, self.cell_size, self.wall_image)

		current_apple = self.poisonous_apple_image if self.apple_is_poisonous else self.apple
		self.fruit.draw_fruit(self.screen, self.cell_size, current_apple)

		self.snake.draw_snake(self.screen, self.cell_size)
		self.draw_score()

def main():
    pygame.init()
    pygame.mixer.init()
    
    cell_size = 40
    cell_number = 20
    screen_width = cell_number * cell_size
    screen_height = cell_number * cell_size
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Snake Game")
    clock = pygame.time.Clock()
    
    game_font = pygame.font.Font('Font/PoetsenOne-Regular.ttf', 25)
    apple = pygame.image.load('Graphics/apple.png').convert_alpha()
    
    game = MAIN(screen, cell_size, cell_number, game_font, apple, clock)
    
    game.main_menu()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == game.SCREEN_UPDATE and game.game_active:
                game.update()
            if event.type == pygame.KEYDOWN and game.game_active:
                if event.key == pygame.K_UP and game.snake.direction.y != 1:
                    game.snake.direction = Vector2(0, -1)
                if event.key == pygame.K_DOWN and game.snake.direction.y != -1:
                    game.snake.direction = Vector2(0, 1)
                if event.key == pygame.K_LEFT and game.snake.direction.x != 1:
                    game.snake.direction = Vector2(-1, 0)
                if event.key == pygame.K_RIGHT and game.snake.direction.x != -1:
                    game.snake.direction = Vector2(1, 0)
                if event.key == pygame.K_ESCAPE:
                    game.game_active = False
                    game.main_menu()
        
        screen.fill((175, 215, 70))
        
        if game.game_active:
            game.draw_elements()
        
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()