import pygame
import sys
import math
import os
import random
from snl import SnakesAndLadders, Player, AIPlayer

pygame.init()

# Constants
SCREEN_WIDTH = 1200 
SCREEN_HEIGHT = 750 
BOARD_SIZE = 500  
BOARD_OFFSET_X = 30  
BOARD_OFFSET_Y = 50
INFO_PANEL_X = BOARD_SIZE + BOARD_OFFSET_X + 20
INFO_PANEL_WIDTH = SCREEN_WIDTH - INFO_PANEL_X - 20


FULLSCREEN_MODE = False 
WINDOW_CONTROLS_Y = 10
CONTROL_BUTTON_SIZE = 30
CONTROL_PADDING = 5

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (210, 230, 255)
SNAKE_COLOR = (255, 50, 50)
LADDER_COLOR = (50, 200, 50)
BEIGE = (245, 245, 220)
LIGHT_GREEN = (220, 255, 220)

RED = (255, 50, 50)    
BLUE = (50, 50, 255)    
GREEN = (50, 180, 50)   
PURPLE = (180, 50, 180) 

PLAYER_COLORS = [RED, BLUE, GREEN, PURPLE]

class SnakesAndLaddersGUI:
    def __init__(self, game: SnakesAndLadders):
        self.game = game

        #Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Strategic Snakes and Ladders")
        self.player_colors = [RED, BLUE, GREEN, PURPLE]
        self.font = pygame.font.SysFont('Arial', 16)
        self.small_font = pygame.font.SysFont('Arial', 13)
        self.large_font = pygame.font.SysFont('Arial', 24, bold=True)
        self.title_font = pygame.font.SysFont('Arial', 32, bold=True)
        self.board_image = pygame.image.load("board_new.png")
        board_files = ["board_new.png"]
        
        for board_file in board_files:
            try:
                print(f"Attempting to load board image: {board_file}")
                self.board_image = pygame.image.load(board_file)
                self.board_image = pygame.transform.scale(self.board_image, (BOARD_SIZE, BOARD_SIZE))
                print(f"Successfully loaded {board_file}")
                break
            except (pygame.error, FileNotFoundError) as e:
                print(f"Error loading board image {board_file}: {e}")
        if self.board_image is None:
            print("Creating fallback board image")
            self.board_image = self.create_fallback_board()
        
        self.player_images = []
        for i in range(4):
            piece = self.create_player_piece(i)
            self.player_images.append(piece)
        
        self.cell_size = BOARD_SIZE // int(math.sqrt(game.board_size))
        self.rows = self.cols = int(math.sqrt(game.board_size))
        self.dice_roll = None
        self.message_log = []
        self.is_human_turn = False
        self.human_prediction = None
        self.waiting_for_prediction = False
        self.waiting_for_reward_choice = False
        self.current_player = None
        self.confirm_button_rect = None  # Store the button rectangle for consistency
        
        # Animation variables
        self.animation_in_progress = False
        self.player_animation_positions = {}  
        self.animation_start_time = 0
        self.animation_duration = 1000  
        self.animation_start_pos = {}
        self.animation_target_pos = {}
        
        self.game_state = "INTRO"  # INTRO, PLAYING, GAME_OVER
        self.dice_images = self.load_or_create_dice_images()
        self.current_dice_image = None
        self._patch_ai_player()
    
    def create_player_piece(self, player_index):
        """Create a player piece with the appropriate color."""
        piece_size = 40
        piece_surface = pygame.Surface((piece_size, piece_size), pygame.SRCALPHA) #SRCALPHA is used for per pixel color transfer for a brighter interface
        color = self.player_colors[player_index % len(self.player_colors)]
        highlight_color = tuple(min(c + 50, 255) for c in color[:3])

        pygame.draw.circle(piece_surface, color,(piece_size//2, piece_size//2), piece_size//2)
        pygame.draw.circle(piece_surface, highlight_color,(piece_size//2 - 5, piece_size//2 - 5), piece_size//3)
        pygame.draw.circle(piece_surface, BLACK,(piece_size//2, piece_size//2), piece_size//2, 2)
        
        font = pygame.font.SysFont('Arial', 20, bold=True)
        text = font.render(str(player_index + 1), True, BLACK)
        text_rect = text.get_rect(center=(piece_size//2, piece_size//2))
        piece_surface.blit(text, text_rect)
        
        return piece_surface
    
    def _patch_ai_player(self):
        """Patch the AIPlayer class to use our safe game copy method instead of deepcopy."""
        original_simulate_move = AIPlayer._simulate_move
        gui = self
        
        def patched_simulate_move(self, game_state, prediction, dice_roll):
            prediction = max(1, min(6, prediction))
            if game_state is gui.game:
                simulated_state = gui.get_safe_game_copy()
             
                current_player_idx = simulated_state.current_player_idx
                current_player = simulated_state.players[current_player_idx]
                
                simulated_state.predictions[current_player.name] = prediction
                
                is_correct = (prediction == dice_roll)
                
                if is_correct:
                    current_player.tokens += 1  
                current_player.position += dice_roll
                
                if current_player.position in simulated_state.snakes:
                    snake_head = current_player.position
                    tokens_required = simulated_state.snake_sizes[snake_head]
                    
                    if current_player.tokens >= tokens_required:
                        current_player.tokens -= tokens_required
                    else:
                        current_player.position = simulated_state.snakes[snake_head]
                if current_player.position in simulated_state.ladders:
                    current_player.position = simulated_state.ladders[current_player.position]
                current_player.position = min(current_player.position, simulated_state.board_size)
                simulated_state.current_player_idx = (current_player_idx + 1) % len(simulated_state.players)
                return simulated_state
            else:
                return original_simulate_move(self, game_state, prediction, dice_roll)
        AIPlayer._simulate_move = patched_simulate_move
    
    def load_or_create_dice_images(self):
        """Load or create dice face images."""
        dice_images = []
        dice_size = 60
        for i in range(1, 7):
            dice_surface = pygame.Surface((dice_size, dice_size), pygame.SRCALPHA)
            pygame.draw.rect(dice_surface, WHITE, (0, 0, dice_size, dice_size), border_radius=10)
            pygame.draw.rect(dice_surface, BLACK, (0, 0, dice_size, dice_size), 2, border_radius=10)

            dot_positions = {
                1: [(dice_size//2, dice_size//2)],
                2: [(dice_size//4, dice_size//4), (3*dice_size//4, 3*dice_size//4)],
                3: [(dice_size//4, dice_size//4), (dice_size//2, dice_size//2), (3*dice_size//4, 3*dice_size//4)],
                4: [(dice_size//4, dice_size//4), (3*dice_size//4, dice_size//4), 
                   (dice_size//4, 3*dice_size//4), (3*dice_size//4, 3*dice_size//4)],
                5: [(dice_size//4, dice_size//4), (3*dice_size//4, dice_size//4), 
                   (dice_size//2, dice_size//2),
                   (dice_size//4, 3*dice_size//4), (3*dice_size//4, 3*dice_size//4)],
                6: [(dice_size//4, dice_size//4), (3*dice_size//4, dice_size//4), 
                   (dice_size//4, dice_size//2), (3*dice_size//4, dice_size//2),
                   (dice_size//4, 3*dice_size//4), (3*dice_size//4, 3*dice_size//4)]
            }
            
            for pos in dot_positions[i]:
                pygame.draw.circle(dice_surface, BLACK, pos, dice_size//10)
            dice_images.append(dice_surface)
        
        return dice_images
    
    def get_safe_game_copy(self):
        """Create a safe copy of the game state for AI algorithms without unpicklable pygame objects."""
        safe_game = SnakesAndLadders(
            board_size=self.game.board_size,
            num_snakes=0,  
            num_ladders=0  
        )
        
        safe_game.snakes = self.game.snakes.copy()
        safe_game.snake_sizes = self.game.snake_sizes.copy()
        safe_game.ladders = self.game.ladders.copy()
        safe_game.predictions = self.game.predictions.copy()
        safe_game.current_player_idx = self.game.current_player_idx
        
        for player in self.game.players:
            if isinstance(player, HumanGUIPlayer):
                new_player = Player(player.name, player.color)
                new_player.position = player.position
                new_player.tokens = player.tokens
                new_player.skipped = player.skipped
                new_player.on_board = player.on_board
                safe_game.add_player(new_player)
            elif isinstance(player, AIPlayer):
                new_player = AIPlayer(player.name, player.difficulty, player.color)
                new_player.position = player.position
                new_player.tokens = player.tokens
                new_player.skipped = player.skipped
                new_player.on_board = player.on_board
                safe_game.add_player(new_player)
            else:
                new_player = Player(player.name, player.color)
                new_player.position = player.position
                new_player.tokens = player.tokens
                new_player.skipped = player.skipped
                new_player.on_board = player.on_board
                safe_game.add_player(new_player)
        
        return safe_game
    
    def draw_board(self):
        self.screen.blit(self.board_image, (BOARD_OFFSET_X - 15, BOARD_OFFSET_Y - 15))
        title = self.title_font.render("Strategic Snakes & Ladders", True, BLACK)
        self.screen.blit(title, (BOARD_OFFSET_X + BOARD_SIZE // 2 - title.get_width() // 2, BOARD_OFFSET_Y - 45))
        
        for row in range(self.rows):
            for col in range(self.cols):
                if row % 2 == 0: 
                    pos = (self.rows - row - 1) * self.cols + col + 1
                else:  
                    pos = (self.rows - row - 1) * self.cols + (self.cols - col)
                
                rect_x = BOARD_OFFSET_X + col * self.cell_size
                rect_y = BOARD_OFFSET_Y + row * self.cell_size
                
                if pos == 1:
                    start_text = self.font.render("START", True, (0, 0, 150))
                    start_bg = pygame.Surface((start_text.get_width() + 10, start_text.get_height() + 6), pygame.SRCALPHA)
                    pygame.draw.rect(start_bg, (255, 255, 255, 180), start_bg.get_rect(), border_radius=8)
                    
                    start_bg_rect = start_bg.get_rect(center=(rect_x + self.cell_size//2, rect_y + self.cell_size - 15))
                    self.screen.blit(start_bg, start_bg_rect)
                    
                    text_rect = start_text.get_rect(center=(rect_x + self.cell_size//2, rect_y + self.cell_size - 15))
                    self.screen.blit(start_text, text_rect)
                    
                elif pos == self.game.board_size:
                    finish_text = self.font.render("FINISH", True, (150, 0, 0))
                    finish_bg = pygame.Surface((finish_text.get_width() + 10, finish_text.get_height() + 6), pygame.SRCALPHA)
                    pygame.draw.rect(finish_bg, (255, 255, 255, 180), finish_bg.get_rect(), border_radius=8)
                    
                    finish_bg_rect = finish_bg.get_rect(center=(rect_x + self.cell_size//2, rect_y + self.cell_size - 15))
                    self.screen.blit(finish_bg, finish_bg_rect)
                    
                    text_rect = finish_text.get_rect(center=(rect_x + self.cell_size//2, rect_y + self.cell_size - 15))
                    self.screen.blit(finish_text, text_rect)
    
    def get_cell_center(self, position):
        if position <= 0:
            #Enter players from the right
            return (BOARD_OFFSET_X + BOARD_SIZE + 30, BOARD_OFFSET_Y + BOARD_SIZE - self.cell_size // 2)
            
        position -= 1  
        row = self.rows - (position // self.cols) - 1
        
        if row % 2 == 0:  
            col = position % self.cols
        else: 
            col = self.cols - 1 - (position % self.cols)
        
        center_x = BOARD_OFFSET_X + col * self.cell_size + self.cell_size // 2
        center_y = BOARD_OFFSET_Y + row * self.cell_size + self.cell_size // 2
        
        return center_x, center_y
    
    def draw_snakes_and_ladders(self):
        random.seed(42)
        
        # Draw ladders
        for bottom, top in self.game.ladders.items():
            start_x, start_y = self.get_cell_center(bottom)
            end_x, end_y = self.get_cell_center(top)
            
            # Calculate ladder width based on distance
            distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            width = max(8, min(12, distance / 20))
            
            # Calculate angle for proper ladder orientation
            angle = math.atan2(end_y - start_y, end_x - start_x)
            perpendicular_angle = angle + math.pi/2
            
            # Calculate offsets for ladder sides
            dx = math.cos(perpendicular_angle) * width
            dy = math.sin(perpendicular_angle) * width
            
            # Draw ladder sides (two parallel lines)
            pygame.draw.line(self.screen, LADDER_COLOR, (start_x - dx, start_y - dy), (end_x - dx, end_y - dy), 5)
            pygame.draw.line(self.screen, LADDER_COLOR, (start_x + dx, start_y + dy), (end_x + dx, end_y + dy), 5)
            
            # Add gold color border for more visibility
            pygame.draw.line(self.screen, (220, 220,20),(start_x - dx, start_y - dy), (end_x - dx, end_y - dy), 1)
            pygame.draw.line(self.screen, (220, 220, 20),(start_x + dx, start_y + dy), (end_x + dx, end_y + dy), 1)
            
            steps = max(3, int(distance / 30))
            for i in range(1, steps + 1):
                t = i / (steps + 1)
                rung_x = start_x + (end_x - start_x) * t
                rung_y = start_y + (end_y - start_y) * t
                
                rung_x1 = rung_x - dx
                rung_y1 = rung_y - dy
                rung_x2 = rung_x + dx
                rung_y2 = rung_y + dy
                
                pygame.draw.line(self.screen, LADDER_COLOR, (rung_x1, rung_y1), (rung_x2, rung_y2), 3)
                pygame.draw.line(self.screen, (220, 180, 0),(rung_x1, rung_y1), (rung_x2, rung_y2), 1)
        
        SNAKE_COLORS = [
            (255, 50, 50),    
            (50, 150, 50),  
            (70, 70, 200),    
            (180, 50, 180),  
            (200, 120, 0),   
            (0, 150, 150),  
            (130, 80, 0),     
            (100, 100, 100)   
        ]
        
        snake_items = list(self.game.snakes.items())
        for i, (head, tail) in enumerate(snake_items):
            snake_color = SNAKE_COLORS[i % len(SNAKE_COLORS)]
            snake_id = head 
            
            start_x, start_y = self.get_cell_center(head)
            end_x, end_y = self.get_cell_center(tail)
            glow_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
            dx = end_x - start_x
            dy = end_y - start_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            
            pattern_index = (i % 4)
            
            # Create pattern variation:
            # 0: gentle S-curve
            # 1: more pronounced S-curve
            # 2: C-curve to the right
            # 3: C-curve to the left
            
            if pattern_index == 0 or pattern_index == 1:
                # S-curve pattern
                curve_factor = 0.2 if pattern_index == 0 else 0.35  # Adjust curve intensity
                curve_direction = 1 if i % 2 == 0 else -1
                
                # First control point - perpendicular to the line
                ctrl_x1 = start_x + dx * 0.25 - math.sin(angle) * distance * curve_factor * curve_direction
                ctrl_y1 = start_y + dy * 0.25 + math.cos(angle) * distance * curve_factor * curve_direction
                
                # Second control point - perpendicular in the opposite direction
                ctrl_x2 = start_x + dx * 0.75 + math.sin(angle) * distance * curve_factor * curve_direction
                ctrl_y2 = start_y + dy * 0.75 - math.cos(angle) * distance * curve_factor * curve_direction
            else:
                # C-curve pattern
                curve_factor = 0.4  # Stronger curve
                curve_direction = 1 if pattern_index == 2 else -1
                
                # Both control points on the same side for C-curve
                ctrl_x1 = start_x + dx * 0.25 + math.sin(angle) * distance * curve_factor * curve_direction
                ctrl_y1 = start_y + dy * 0.25 - math.cos(angle) * distance * curve_factor * curve_direction
                
                ctrl_x2 = start_x + dx * 0.75 + math.sin(angle) * distance * curve_factor * curve_direction
                ctrl_y2 = start_y + dy * 0.75 - math.cos(angle) * distance * curve_factor * curve_direction
            
            points = []
            steps = 30
            for j in range(steps + 1):
                t = j / steps
                x = (1-t)**3 * start_x + 3*(1-t)**2*t * ctrl_x1 + 3*(1-t)*t**2 * ctrl_x2 + t**3 * end_x
                y = (1-t)**3 * start_y + 3*(1-t)**2*t * ctrl_y1 + 3*(1-t)*t**2 * ctrl_y2 + t**3 * end_y
                points.append((x, y))
            
            if len(points) > 1:
              
                glow_color = (*snake_color[:3], 30) 
                for j in range(len(points) - 1):
                    p1 = points[j]
                    p2 = points[j + 1]
                    pygame.draw.line(glow_surface, glow_color, p1, p2, 15)  # Thinner glow
                
                self.screen.blit(glow_surface, (0, 0))
                
                for j in range(len(points) - 1):
                    p1 = points[j]
                    p2 = points[j + 1]
                    
                    # Calculate thickness - thinner overall
                    progress = j / (len(points) - 2)  # 0 to 1
                    if progress <= 0.5:
                        thickness = 3 + 4 * (progress * 2)  # 3 to 7 (thinner)
                    else:
                        thickness = 7 - 4 * ((progress - 0.5) * 2)  # 7 to 3 (thinner)
                    
                    pygame.draw.line(self.screen, snake_color, p1, p2, int(thickness))
                    
                    if j % 4 == 0:  # Less frequent scales
                        scale_color = tuple(min(c + 60, 255) for c in snake_color[:3])
                        scale_size = thickness/2 - 1
                        if scale_size > 0:
                            pygame.draw.circle(self.screen, scale_color, p1, scale_size)
            
            head_size = 12  
            pygame.draw.circle(self.screen, snake_color, (start_x, start_y), head_size)
            
           
            eye_size = 4  
            eye_offset = head_size/2 - 1
            pygame.draw.circle(self.screen, WHITE, (start_x - eye_offset, start_y - head_size/3), eye_size)
            pygame.draw.circle(self.screen, WHITE, (start_x + eye_offset, start_y - head_size/3), eye_size)
            
            pupil_size = 2
            pygame.draw.circle(self.screen, BLACK, (start_x - eye_offset, start_y - head_size/3), pupil_size)
            pygame.draw.circle(self.screen, BLACK, (start_x + eye_offset, start_y - head_size/3), pupil_size)
            
           
            tongue_length = 8 
            start_tongue_x = start_x
            start_tongue_y = start_y + head_size/2 - 1
            end_tongue_x = start_x
            end_tongue_y = start_tongue_y + tongue_length
            fork1_x = end_tongue_x - 4 
            fork1_y = end_tongue_y + 2
            fork2_x = end_tongue_x + 4  
            fork2_y = end_tongue_y + 2
            
            pygame.draw.line(self.screen, (200, 0, 0), (start_tongue_x, start_tongue_y), (end_tongue_x, end_tongue_y), 1)  # Thinner tongue
            pygame.draw.line(self.screen, (200, 0, 0), (end_tongue_x, end_tongue_y), (fork1_x, fork1_y), 1)  # Thinner tongue
            pygame.draw.line(self.screen, (200, 0, 0), (end_tongue_x, end_tongue_y), (fork2_x, fork2_y), 1)  # Thinner tongue
        
        random.seed()
    
    def draw_players(self):
        for i, player in enumerate(self.game.players):
            if player.position <= 0 and not player.name in self.player_animation_positions:
                continue
            
            if player.name in self.player_animation_positions:
                center_x, center_y = self.player_animation_positions[player.name]
            else:
                center_x, center_y = self.get_cell_center(player.position)
            
          
            offset_x = ((i % 3) - 1) * 15
            offset_y = ((i // 3) - 1) * 15
            
           
            player_img = self.player_images[i % len(self.player_images)]
            img_rect = player_img.get_rect()
            img_rect.center = (center_x + offset_x, center_y + offset_y)
            
   
            shadow_surface = pygame.Surface(player_img.get_size(), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 80))  # Semi-transparent black
            shadow_rect = shadow_surface.get_rect()
            shadow_rect.center = (center_x + offset_x + 3, center_y + offset_y + 3)  
            self.screen.blit(shadow_surface, shadow_rect)
            self.screen.blit(player_img, img_rect)
            token_indicator = self.small_font.render(f"{player.tokens}🪙", True, BLACK)
            token_rect = token_indicator.get_rect(center=(center_x + offset_x, center_y + offset_y + 30))
            
            token_bg = pygame.Surface((token_indicator.get_width() + 10, token_indicator.get_height() + 6), pygame.SRCALPHA)
            pygame.draw.rect(token_bg, (255, 255, 255, 180), token_bg.get_rect(), border_radius=8)
            token_bg_rect = token_bg.get_rect(center=token_rect.center)
            self.screen.blit(token_bg, token_bg_rect)
            self.screen.blit(token_indicator, token_rect)
    
    def draw_info_panel(self):
        panel_rect = pygame.Rect(INFO_PANEL_X, BOARD_OFFSET_Y,INFO_PANEL_WIDTH, BOARD_SIZE)
        pygame.draw.rect(self.screen, GRAY, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2, border_radius=10)
        
        title = self.large_font.render("Game Info", True, BLACK)
        self.screen.blit(title, (INFO_PANEL_X + INFO_PANEL_WIDTH//2 - title.get_width()//2, BOARD_OFFSET_Y + 10))
      
        if self.game.players:
            y_pos = BOARD_OFFSET_Y + 45
            
            # Draw players box (includes current player)
            players_box_height = 15 + len(self.game.players) * 25
            players_box = pygame.Rect(INFO_PANEL_X + 5, y_pos - 5, INFO_PANEL_WIDTH - 10, players_box_height)
            pygame.draw.rect(self.screen, (240, 240, 240), players_box, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, players_box, 1, border_radius=5)
          
            for i, player in enumerate(self.game.players):
                is_current = (i == self.game.current_player_idx)
                color = self.player_colors[i % len(self.player_colors)]
                
                # Draw player circle
                pygame.draw.circle(self.screen, color, (INFO_PANEL_X + 20, y_pos + 10 + i*25), 8)
                pygame.draw.circle(self.screen, BLACK,(INFO_PANEL_X + 20, y_pos + 10 + i*25), 8, 1)
                
                player_font = self.font
                player_prefix = ""
                if is_current:
                    player_prefix = "➤ "
                
                player_text = player_font.render(
                    f"{player_prefix}{player.name}: Pos {player.position}, Tokens {player.tokens}", 
                    True, BLACK)
                self.screen.blit(player_text, (INFO_PANEL_X + 35, y_pos + 5 + i*25))
                

                if player.skipped:
                    skip_text = self.small_font.render("Will Skip Turn", True, (255, 0, 0))
                    self.screen.blit(skip_text, (INFO_PANEL_X + INFO_PANEL_WIDTH - 110, y_pos + 5 + i*25))
            
           
            if self.dice_roll is not None:
                dice_y = y_pos + players_box_height + 10
                dice_box = pygame.Rect(INFO_PANEL_X + 5, dice_y, 80, 80)
                pygame.draw.rect(self.screen, (240, 240, 240), dice_box, border_radius=5)
                pygame.draw.rect(self.screen, BLACK, dice_box, 1, border_radius=5)
                
                dice_label = self.font.render("Dice:", True, BLACK)
                self.screen.blit(dice_label, (INFO_PANEL_X + 15, dice_y + 5))
                
                dice_image = self.dice_images[self.dice_roll - 1]
                self.screen.blit(dice_image, (INFO_PANEL_X + 15, dice_y + 20))
            
     
            pred_y = y_pos + players_box_height + 10
            if self.dice_roll is not None:
                pred_y = dice_y + 85
                
            pred_box_height = 0  
            
            if self.game.predictions:
                pred_box_height = 15 + len(self.game.players) * 20
                pred_box = pygame.Rect(INFO_PANEL_X + 5, pred_y, INFO_PANEL_WIDTH - 10, pred_box_height)
                pygame.draw.rect(self.screen, (240, 240, 240), pred_box, border_radius=5)
                pygame.draw.rect(self.screen, BLACK, pred_box, 1, border_radius=5)
                
                pred_title = self.font.render("Predictions:", True, BLACK)
                self.screen.blit(pred_title, (INFO_PANEL_X + 15, pred_y + 5))
                
                
                for i, player in enumerate(self.game.players):
                    if player.name in self.game.predictions:
                        color = self.player_colors[i % len(self.player_colors)]
                        prediction = self.game.predictions[player.name]
                        pred_text = self.small_font.render(
                            f"{player.name}: {prediction}", True, color)
                        self.screen.blit(pred_text, (INFO_PANEL_X + 25, pred_y + 25 + i*18))
            
            log_y = pred_y + pred_box_height + 15
            log_title = self.font.render("Game Log:", True, BLACK)
            self.screen.blit(log_title, (INFO_PANEL_X + 10, log_y))
            
         
            log_height = BOARD_SIZE + BOARD_OFFSET_Y - log_y - 30
            log_rect = pygame.Rect(INFO_PANEL_X + 10, log_y + 25, INFO_PANEL_WIDTH - 20, log_height)
            pygame.draw.rect(self.screen, (240, 240, 240), log_rect, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, log_rect, 1, border_radius=5)
            

            max_visible_messages = max(10, int(log_height / 20))  
            visible_messages = self.message_log[-max_visible_messages:] if len(self.message_log) > max_visible_messages else self.message_log
            available_width = log_rect.width - 15
            def wrap_text(text, width):
                words = text.split(' ')
                lines = []
                current_line = []
                current_width = 0
                
                for word in words:
                    word_surface = self.small_font.render(word + ' ', True, BLACK)
                    word_width = word_surface.get_width()
                    
                    if current_width + word_width > width:
                        if current_line:  
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            current_width = word_width
                        else:
                            current_line.append(word)
                            lines.append(' '.join(current_line))
                            current_line = []
                            current_width = 0
                    else:
                        current_line.append(word)
                        current_width += word_width
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                return lines
            y_offset = 0
            for message in visible_messages:
                # Wrap long messages
                wrapped_lines = wrap_text(message, available_width)
                if len(wrapped_lines) > 0:
                    msg_height = len(wrapped_lines) * 18 + 2
                    msg_bg_rect = pygame.Rect(INFO_PANEL_X + 15, log_y + 30 + y_offset - 2, available_width, msg_height)
                    if visible_messages.index(message) % 2 == 0:
                        pygame.draw.rect(self.screen, (230, 230, 240), msg_bg_rect, border_radius=3)
                    else:
                        pygame.draw.rect(self.screen, (240, 240, 250), msg_bg_rect, border_radius=3)
                
                for line in wrapped_lines:
                    if log_y + 30 + y_offset >= log_rect.bottom - 5:
                        break
                    
                    log_text = self.small_font.render(line, True, BLACK)
                    if log_text.get_width() > available_width:
                        log_text = self.small_font.render(line[:50] + "...", True, BLACK)
                    
                    self.screen.blit(log_text, (INFO_PANEL_X + 15, log_y + 30 + y_offset))
                    y_offset += 18  
                y_offset += 2
                if log_y + 30 + y_offset >= log_rect.bottom - 5:
                    break
    
    def draw_prediction_explanation(self):
        """Draw an explanation about the prediction mechanics."""
        box_rect = pygame.Rect(BOARD_OFFSET_X, BOARD_SIZE + BOARD_OFFSET_Y + 20,BOARD_SIZE, SCREEN_HEIGHT - (BOARD_SIZE + BOARD_OFFSET_Y) - 30)
        pygame.draw.rect(self.screen, LIGHT_BLUE, box_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, box_rect, 2, border_radius=10)
        
        title = self.font.render("Prediction System Explained:", True, BLACK)
        self.screen.blit(title, (box_rect.x + 10, box_rect.y + 10))
        
        lines = [
            "• Before rolling the dice, players predict the outcome (1-6)",
            "• If you predict correctly: Choose bonus roll OR gain 2 tokens",
            "• If opponents predict correctly:",
            "  - First opponent: Makes you skip next turn",
            "  - Second opponent: Moves you backward",
            "• Tokens can be used to neutralize snakes when landed on"
        ]
        
        for i, line in enumerate(lines):
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (box_rect.x + 15, box_rect.y + 35 + i*20))
    
    def draw_human_controls(self):
        if not self.is_human_turn:
            return
        control_y = BOARD_SIZE + BOARD_OFFSET_Y + 20
        control_rect = pygame.Rect(BOARD_OFFSET_X, control_y,BOARD_SIZE, SCREEN_HEIGHT - control_y - 10)
        pygame.draw.rect(self.screen, LIGHT_BLUE, control_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, control_rect, 2, border_radius=10)
        
        if self.waiting_for_prediction:
            title = self.large_font.render("Make your prediction (1-6):", True, BLACK)
            self.screen.blit(title, (BOARD_OFFSET_X + BOARD_SIZE//2 - title.get_width()//2, control_y + 15))
            
            for i in range(1, 7):
                button_x = BOARD_OFFSET_X + (i-1) * 80 + 30  
                button_rect = pygame.Rect(button_x, control_y + 50, 60, 40) 
                if self.human_prediction == i:
                    pygame.draw.rect(self.screen, (180, 230, 180), button_rect, border_radius=5)
                else:
                    pygame.draw.rect(self.screen, WHITE, button_rect, border_radius=5)
                
                pygame.draw.rect(self.screen, BLACK, button_rect, 2, border_radius=5)
                dice_img = pygame.transform.scale(self.dice_images[i-1], (25, 25))
                self.screen.blit(dice_img, (button_x + 5, control_y + 58))
                num_text = self.large_font.render(str(i), True, BLACK)
                self.screen.blit(num_text, (button_x + 38, control_y + 58))
            
            if self.human_prediction is not None:
                self.confirm_button_rect = pygame.Rect(
                    BOARD_OFFSET_X + BOARD_SIZE//2 - 100,
                    control_y + 110,
                    200, 
                    60,
                )
                pygame.draw.rect(self.screen, (100, 200, 100), self.confirm_button_rect, border_radius=8)
                pygame.draw.rect(self.screen, BLACK, self.confirm_button_rect, 2, border_radius=8)
          
                confirm_text = self.large_font.render("Confirm Prediction", True, BLACK)
                text_rect = confirm_text.get_rect(center=self.confirm_button_rect.center)
                self.screen.blit(confirm_text, text_rect)
                
                selected_text = self.font.render(f"Selected: {self.human_prediction}", True, BLACK)
                self.screen.blit(selected_text, (self.confirm_button_rect.left, self.confirm_button_rect.top - 20))
        
        elif self.waiting_for_reward_choice:
            title = self.font.render("You predicted correctly! Choose your reward:", True, BLACK)
            self.screen.blit(title, (BOARD_OFFSET_X + 20, control_y + 15))
            
            bonus_rect = pygame.Rect(BOARD_OFFSET_X + BOARD_SIZE//4 - 75,control_y + 50, 150, 60)
            pygame.draw.rect(self.screen, (100, 200, 100), bonus_rect, border_radius=8)
            pygame.draw.rect(self.screen, BLACK, bonus_rect, 2, border_radius=8)
            bonus_text = self.font.render("Bonus Roll", True, BLACK)
            bonus_rect2 = bonus_text.get_rect(center=(bonus_rect.centerx, bonus_rect.centery - 10))
            self.screen.blit(bonus_text, bonus_rect2)
            dice_img = pygame.transform.scale(self.dice_images[0], (30, 30))
            self.screen.blit(dice_img, (bonus_rect.centerx - 15, bonus_rect.centery + 5))
            
            tokens_rect = pygame.Rect(BOARD_OFFSET_X + 3*BOARD_SIZE//4 - 75,control_y + 50, 150, 60)
            pygame.draw.rect(self.screen, (100, 150, 250), tokens_rect, border_radius=8)
            pygame.draw.rect(self.screen, BLACK, tokens_rect, 2, border_radius=8)
            tokens_text = self.font.render("Gain 2 Tokens", True, BLACK)
            tokens_rect2 = tokens_text.get_rect(center=(tokens_rect.centerx, tokens_rect.centery - 10))
            self.screen.blit(tokens_text, tokens_rect2)
            token_text = self.font.render("🪙 🪙", True, BLACK)
            token_rect = token_text.get_rect(center=(tokens_rect.centerx, tokens_rect.centery + 10))
            self.screen.blit(token_text, token_rect)
    
    def add_message(self, message):
        """Add a message to the game log."""
        if any(info in message for info in ["Board Size:", "Snakes:", "Ladders:", "Players:"]):
            print(message)
            return
            
        self.message_log.append(message)
        print(message) 
    
        if len(self.message_log) > 100:
            self.message_log = self.message_log[-100:]
    
    def handle_prediction_click(self, pos):
        """Handle player's click on a prediction button."""
        if not self.waiting_for_prediction:
            return None
        control_y = BOARD_SIZE + BOARD_OFFSET_Y + 20
        for i in range(1, 7):
            button_x = BOARD_OFFSET_X + (i-1) * 80 + 30
            button_rect = pygame.Rect(button_x, control_y + 50, 60, 40)
            
            if button_rect.collidepoint(pos):
                self.human_prediction = i
                return None  
        if self.human_prediction is not None and hasattr(self, 'confirm_button_rect') and self.confirm_button_rect.collidepoint(pos):
            # Confirm the prediction
            self.game.make_prediction(self.current_player.name, self.human_prediction)
            self.waiting_for_prediction = False
            self.add_message(f"{self.current_player.name} predicted {self.human_prediction}")
            
            # Get predictions from AI players
            for player in self.game.players:
                if player != self.current_player:
                    opp_prediction = player.make_prediction(self.game)
                    # Ensure prediction is valid
                    opp_prediction = max(1, min(6, opp_prediction))  # Clamp between 1 and 6
                    self.game.make_prediction(player.name, opp_prediction)
                    self.add_message(f"{player.name} predicts: {opp_prediction}")
            
        
            dice_roll = self.game.roll_dice()
            self.dice_roll = dice_roll
            self.add_message(f"Dice roll: {dice_roll}")
            
            correct_predictions = self.game.check_predictions(dice_roll)
            
            if correct_predictions[self.current_player.name]:
                self.add_message(f"Correct prediction by {self.current_player.name}!")
                self.waiting_for_reward_choice = True
                return False 
            else:
                self.handle_opponent_predictions(dice_roll, self.current_player)
                self.start_move_animation(self.current_player, dice_roll)
                return False  
        return None 
    
    def handle_reward_choice_click(self, pos):
        """Handle player's click on a reward choice button."""
        if not self.waiting_for_reward_choice:
            return None
        control_y = BOARD_SIZE + BOARD_OFFSET_Y + 20
        bonus_rect = pygame.Rect(BOARD_OFFSET_X + BOARD_SIZE//4 - 75,control_y + 50, 150, 60)
        if bonus_rect.collidepoint(pos):
            self.waiting_for_reward_choice = False
            self.add_message(f"{self.current_player.name} chose to get a bonus roll!")
            dice_roll = self.dice_roll
            self.handle_opponent_predictions(dice_roll, self.current_player)
            self.start_move_animation(self.current_player, dice_roll)
            self.after_animation_callback = self.process_bonus_roll
            
            return False
        tokens_rect = pygame.Rect(BOARD_OFFSET_X + 3*BOARD_SIZE//4 - 75,control_y + 50, 150, 60)
        if tokens_rect.collidepoint(pos):
            self.waiting_for_reward_choice = False
            self.add_message(f"{self.current_player.name} chose to gain 2 tokens!")
            self.current_player.tokens += 2
            dice_roll = self.dice_roll
            self.handle_opponent_predictions(dice_roll, self.current_player)
            self.start_move_animation(self.current_player, dice_roll)
            
            return False  
        return None  
    
    def process_bonus_roll(self):
        """Process bonus roll after animation completes."""
        bonus_dice_roll = self.game.roll_dice()
        self.dice_roll = bonus_dice_roll
        self.add_message(f"Bonus dice roll: {bonus_dice_roll}")
        self.start_move_animation(self.current_player, bonus_dice_roll)
        self.after_animation_callback = self.check_game_over
        return False
    
    def check_game_over(self):
        """Check if game is over after animation completes."""
        if self.current_player.position >= self.game.board_size:
            self.add_message(f"\n🎉 {self.current_player.name} has reached position {self.game.board_size} and won the game! 🎉")
            self.game.winner = self.current_player
            self.game.game_state = "game_over"
            return True
        self.game.next_player()
        return False
    
    def handle_snake_encounter(self, player):
        """Handle a player landing on a snake."""
        try:
            if player.position not in self.game.snakes:
                return self.check_game_over()
                
            snake_head = player.position
            snake_tail = self.game.snakes[snake_head]
            tokens_required = self.game.snake_sizes[snake_head]
            
            self.add_message(f"{player.name} landed on a snake (position {snake_head})!")
            self.add_message(f"This snake requires {tokens_required} tokens to neutralize. You have {player.tokens} tokens.")
            if isinstance(player, HumanGUIPlayer) and player == self.current_player:
                print(f"Waiting for human decision on snake at position {snake_head}")
                self.snake_head = snake_head
                self.snake_tail = snake_tail
                self.tokens_required = tokens_required
                self.snake_player = player
                self.waiting_for_snake_decision = True
                return False
            
            #For AI player
            if player.tokens >= tokens_required:
                use_tokens = player.decide_use_tokens(self.game, tokens_required)
                
                if use_tokens:
                    player.tokens -= tokens_required
                    self.add_message(f"{player.name} used {tokens_required} tokens to neutralize the snake!")
                    return self.check_game_over()
            
            # Player slides down the snake
            self.add_message(f"{player.name} slid down to position {snake_tail}!")
            # animation to the snake tail
            self.start_move_animation(player, 0, target_position=snake_tail)
            return False
        except Exception as e:
            print(f"Error in handle_snake_encounter: {e}")
            self.game.next_player()
            return False
    
    def draw_snake_dialog(self):
        """Draw the snake encounter dialog for human players."""
        if not self.waiting_for_snake_decision:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) 
        self.screen.blit(overlay, (0, 0))
        dialog_width, dialog_height = 500, 300
        dialog_rect = pygame.Rect(
            (SCREEN_WIDTH - dialog_width) // 2,
            (SCREEN_HEIGHT - dialog_height) // 2,
            dialog_width,
            dialog_height
        )
        pygame.draw.rect(self.screen, (255, 255, 200), dialog_rect) 
        pygame.draw.rect(self.screen, (255, 0, 0), dialog_rect, 5) 
        
        title = self.title_font.render("SNAKE ENCOUNTERED!", True, (255, 0, 0))
        title_pos = (SCREEN_WIDTH // 2 - title.get_width() // 2, 
                   dialog_rect.y + 30)
        self.screen.blit(title, title_pos)
        
        message1 = self.large_font.render(f"You landed on a snake at position {self.snake_head}.", True, BLACK)
        message2 = self.large_font.render(f"Use {self.tokens_required} tokens to avoid sliding down?", True, BLACK)
        message3 = self.large_font.render(f"You have {self.snake_player.tokens} tokens.", True, BLACK)
        
        msg1_pos = (SCREEN_WIDTH // 2 - message1.get_width() // 2, dialog_rect.y + 80)
        msg2_pos = (SCREEN_WIDTH // 2 - message2.get_width() // 2, dialog_rect.y + 120)
        msg3_pos = (SCREEN_WIDTH // 2 - message3.get_width() // 2, dialog_rect.y + 160)
        
        self.screen.blit(message1, msg1_pos)
        self.screen.blit(message2, msg2_pos)
        self.screen.blit(message3, msg3_pos)
        
        # Create YES button
        yes_width, yes_height = 100, 50
        self.yes_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - yes_width - 20,
            dialog_rect.y + dialog_height - 70,
            yes_width,
            yes_height
        )
        pygame.draw.rect(self.screen, (100, 255, 100), self.yes_button_rect)  
        pygame.draw.rect(self.screen, BLACK, self.yes_button_rect, 3)
        
        yes_text = self.large_font.render("YES", True, BLACK)
        yes_text_pos = (self.yes_button_rect.centerx - yes_text.get_width() // 2,self.yes_button_rect.centery - yes_text.get_height() // 2)
        self.screen.blit(yes_text, yes_text_pos)
        
        # Create NO button
        no_width, no_height = 100, 50
        self.no_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 + 20,
            dialog_rect.y + dialog_height - 70,
            no_width,
            no_height
        )
        pygame.draw.rect(self.screen, (255, 100, 100), self.no_button_rect)  
        pygame.draw.rect(self.screen, BLACK, self.no_button_rect, 3)
        
        no_text = self.large_font.render("NO", True, BLACK)
        no_text_pos = (self.no_button_rect.centerx - no_text.get_width() // 2,self.no_button_rect.centery - no_text.get_height() // 2)
        self.screen.blit(no_text, no_text_pos)
    
    def handle_snake_decision_click(self, pos):
        """Handle clicks on the snake dialog buttons."""
        if not self.waiting_for_snake_decision:
            return None
        if self.yes_button_rect.collidepoint(pos):
            print("YES button clicked - using tokens")
            self.handle_snake_decision(True)
            return False
        elif self.no_button_rect.collidepoint(pos):
            print("NO button clicked - sliding down snake")
            self.handle_snake_decision(False)
            return False
            
        return None
    
    def handle_snake_decision(self, use_tokens):
        """Handle the player's decision about using tokens."""
        self.waiting_for_snake_decision = False
        player = self.snake_player
        snake_head = self.snake_head
        snake_tail = self.snake_tail
        tokens_required = self.tokens_required
        if use_tokens and player.tokens >= tokens_required:
            player.tokens -= tokens_required
            self.add_message(f"{player.name} used {tokens_required} tokens to neutralize the snake!")
            self.check_game_over()
        else:
            player.position = snake_tail
            self.add_message(f"{player.name} slid down to position {snake_tail}!")
            self.start_move_animation(player, 0, target_position=snake_tail)
    
    def handle_event(self, event):
        """Handle a pygame event."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Remove the non-existent waiting_for_roll condition
            # if self.waiting_for_roll and self.roll_button_rect.collidepoint(event.pos):
            #    return self.handle_roll()
            
            # If waiting for prediction, check prediction buttons
            prediction_result = self.handle_prediction_click(event.pos)
            if prediction_result is not None:
                return prediction_result
            
            # If waiting for reward choice, check reward buttons
            reward_result = self.handle_reward_choice_click(event.pos)
            if reward_result is not None:
                return reward_result
                
            # If waiting for snake decision, check snake dialog buttons
            snake_decision_result = self.handle_snake_decision_click(event.pos)
            if snake_decision_result is not None:
                return snake_decision_result
                
            # Check other UI elements (skip button, etc.)
            if hasattr(self, 'skip_button_rect') and self.skip_button_rect.collidepoint(event.pos):
                self.waiting_for_token_decision = False
                self.game.next_player()  
                return False
        return None
    
    def start_move_animation(self, player, spaces, target_position=None):
        """Start animation for moving a player."""
        self.animation_start_pos[player.name] = self.get_cell_center(player.position)
        
        if target_position is None:
            old_position = player.position
            player.position += spaces
            if player.position in self.game.ladders:
                # first to ladder bottom, then to top
                ladder_bottom = player.position
                ladder_top = self.game.ladders[player.position]
                
                # First animation to ladder bottom
                self.animation_target_pos[player.name] = self.get_cell_center(ladder_bottom)
                self.add_message(f"{player.name} climbed a ladder to {ladder_top}!")
                def climb_ladder():
                    self.start_move_animation(player, 0, target_position=ladder_top)
                
                self.after_animation_callback = climb_ladder
            else:
                # Direct animation to target
                self.animation_target_pos[player.name] = self.get_cell_center(player.position)
                if player.position in self.game.snakes:
                    self.after_animation_callback = lambda: self.handle_snake_encounter(player)
                else:
                    self.after_animation_callback = self.check_game_over
        else:
            player.position = target_position
            self.animation_target_pos[player.name] = self.get_cell_center(target_position)
            self.after_animation_callback = self.check_game_over
        player.position = min(player.position, self.game.board_size)
        
        # Initialize animation
        self.animation_in_progress = True
        self.animation_start_time = pygame.time.get_ticks()
        self.player_animation_positions[player.name] = self.animation_start_pos[player.name]
    
    def update_animations(self):
        """Update all active animations."""
        if not self.animation_in_progress:
            return False
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.animation_start_time
        
        # Check if animation is complete
        if elapsed >= self.animation_duration:
            for player_name in self.animation_target_pos:
                self.player_animation_positions[player_name] = self.animation_target_pos[player_name]
            self.animation_start_pos = {}
            self.animation_target_pos = {}
            self.animation_in_progress = False
            if hasattr(self, 'after_animation_callback') and self.after_animation_callback:
                callback = self.after_animation_callback
                self.after_animation_callback = None
                return callback()
            self.game.next_player()
            return False
        t = elapsed / self.animation_duration
        for player_name, start_pos in self.animation_start_pos.items():
            target_pos = self.animation_target_pos[player_name]
            x = start_pos[0] + (target_pos[0] - start_pos[0]) * t
            y = start_pos[1] + (target_pos[1] - start_pos[1]) * t
            bounce = math.sin(t * math.pi) * 5
            y -= bounce
            self.player_animation_positions[player_name] = (x, y)
        
        return False
    
    def handle_opponent_predictions(self, dice_roll, current_player):
        """Handle consequences of correct predictions by opponents."""
        # Delegate to the game class to handle opponent predictions
        self.game.handle_correct_opponent_predictions(dice_roll, current_player)
        
        # Update UI based on results - especially for human players
        if hasattr(current_player, 'gui'):  # For human players
            current_player.gui.is_human_turn = False  # Force set for visual feedback
    
    def show_game_over_screen(self):
        """Show the game over screen with final results.
        Returns:
            - False if the game should restart
            - True if the game should exit
        """
        # Create a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        
        # Display game over message
        game_over_font = pygame.font.SysFont('Arial', 48, bold=True)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 255, 255))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        
        # Display winner
        winner = None
        for player in self.game.players:
            if player.position >= self.game.board_size:
                winner = player
                break
        
        if winner:
            winner_font = pygame.font.SysFont('Arial', 36)
            winner_text = winner_font.render(f"Winner: {winner.name}!", True, (255, 255, 0))
            winner_rect = winner_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        # Display final standings
        results_font = pygame.font.SysFont('Arial', 24)
        
        # Sort players by position
        sorted_players = sorted(self.game.players, key=lambda p: p.position, reverse=True)
        
        # Create play again button
        button_font = pygame.font.SysFont('Arial', 30)
        button_text = button_font.render("Play Again", True, (0, 0, 0))
        button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 100, 200, 50)
        
        # Display the game over screen
        running = True
        restart_game = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return True  # Exit the game
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(event.pos):
                        restart_game = True
                        running = False
            
            # Draw game state in background
            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_snakes_and_ladders()
            self.draw_players()
            self.draw_info_panel()
            
            # Draw overlay
            self.screen.blit(overlay, (0, 0))
            
            # Draw game over text
            self.screen.blit(game_over_text, text_rect)
            if winner:
                self.screen.blit(winner_text, winner_rect)
            
            # Draw final standings
            for i, player in enumerate(sorted_players):
                y_pos = SCREEN_HEIGHT//2 + 50 + i*30
                result_text = results_font.render(
                    f"{i+1}. {player.name}: Position {player.position}, Tokens {player.tokens}", 
                    True, (255, 255, 255))
                result_rect = result_text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
                self.screen.blit(result_text, result_rect)
            
            # Draw play again button
            pygame.draw.rect(self.screen, (200, 200, 100), button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), button_rect, 2)
            button_text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, button_text_rect)
            
            pygame.display.flip()
        
        if restart_game:
            # Reset the game state
            self.reset_game()
            return False  # Restart the game
        else:
            return True  # Exit the game
    
    def process_game_turn(self):
        """Process a single game turn. Returns True if game is over."""
        current_player = self.game.get_current_player()
        
        # Skip turn if applicable
        if current_player.skipped:
            self.add_message(f"{current_player.name}'s turn is skipped!")
            current_player.skipped = False
            self.game.next_player()
            
            # Print debug info about whose turn it is now
            next_player = self.game.get_current_player()
            print(f"Skipped {current_player.name}'s turn. Now it's {next_player.name}'s turn.")
            
            return False
        
        # Check if this is a human player
        is_human = isinstance(current_player, HumanGUIPlayer)
        self.is_human_turn = is_human
        self.current_player = current_player
        
        self.add_message(f"\n{current_player.name}'s turn")
        self.add_message(f"Position: {current_player.position}, Tokens: {current_player.tokens}")
        
        # Prediction phase - handled by player classes
        if is_human:
            self.waiting_for_prediction = True
            return False  # Wait for human input
        else:
            # For AI, make prediction immediately
            prediction = current_player.make_prediction(self.game)
            # Ensure prediction is valid
            prediction = max(1, min(6, prediction))  # Clamp between 1 and 6
            self.game.make_prediction(current_player.name, prediction)
            self.add_message(f"{current_player.name} predicts: {prediction}")
            
            # Let other players make predictions
            for player in self.game.players:
                if player != current_player:
                    opp_prediction = player.make_prediction(self.game)
                    # Ensure prediction is valid
                    opp_prediction = max(1, min(6, opp_prediction))  # Clamp between 1 and 6
                    self.game.make_prediction(player.name, opp_prediction)
                    self.add_message(f"{player.name} predicts: {opp_prediction}")
            
            # Roll dice
            dice_roll = self.game.roll_dice()
            self.dice_roll = dice_roll
            self.add_message(f"Dice roll: {dice_roll}")
            
            # Check predictions
            correct_predictions = self.game.check_predictions(dice_roll)
            
            # Handle current player's correct prediction
            bonus_roll = False
            if correct_predictions[current_player.name]:
                self.add_message(f"Correct prediction by {current_player.name}!")
                choice = current_player.choose_reward(self.game)
                if choice == 1:
                    self.add_message(f"{current_player.name} chose to get a bonus roll!")
                    bonus_roll = True
                else:
                    self.add_message(f"{current_player.name} chose to gain 2 tokens!")
                    current_player.tokens += 2
            
            # Handle opponents' correct predictions
            self.handle_opponent_predictions(dice_roll, current_player)
            
            # Start animation to move player
            self.start_move_animation(current_player, dice_roll)
            
            # Handle bonus roll after regular move completes
            if bonus_roll:
                orig_callback = self.after_animation_callback
                
                def bonus_roll_callback():
                    if orig_callback:
                        orig_callback()
                    self.process_bonus_roll()
                
                self.after_animation_callback = bonus_roll_callback
            
            return False
    
    def run_game(self):
        """Main game loop."""
        clock = pygame.time.Clock()
        running = True
        
        # Add simplified initial message
        self.add_message("=== Strategic Snakes and Ladders ===")
        # Still add these for console debugging but they'll be filtered from GUI
        self.add_message(f"Board Size: {self.game.board_size}")
        self.add_message(f"Snakes: {len(self.game.snakes)}")
        self.add_message(f"Ladders: {len(self.game.ladders)}")
        self.add_message(f"Players: {', '.join(p.name for p in self.game.players)}")
        self.add_message("\nClick on a number (1-6) to predict, then click Confirm!")
        
        # Initialize animation variables
        self.animation_in_progress = False
        self.after_animation_callback = None
        
        # Initialize snake decision variables
        self.waiting_for_snake_decision = False
        self.snake_head = None
        self.snake_tail = None
        self.tokens_required = None
        self.snake_player = None
        
        # Main loop
        while running:
            game_over = False
            
            # Game play loop
            while running and not game_over:
                # Process events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                        
                    result = self.handle_event(event)
                    if result is not None:  # Changed from "is False" to "is not None" to properly handle return values
                        if result is True:
                            game_over = True
                        break
                
                # Check if any player has won
                for player in self.game.players:
                    if player.position >= self.game.board_size:
                        game_over = True
                        self.game.winner = player
                        self.game.game_state = "game_over"
                        break
                
                # Update animations
                if self.animation_in_progress:
                    animation_result = self.update_animations()
                    if animation_result is True:  # Check if animation callback indicates game over
                        game_over = True
                
                # If not waiting for human input or animation, proceed with game logic
                elif not any([self.waiting_for_prediction, 
                            self.waiting_for_reward_choice,
                            self.waiting_for_snake_decision]):
                    # Process game turn
                    game_over = self.process_game_turn()
                    
                    # Small delay between automatic turns for visibility
                    if not game_over and not self.animation_in_progress:
                        pygame.time.delay(300)
                
                # Render the game
                self.screen.fill(WHITE)
                self.draw_board()
                self.draw_snakes_and_ladders()
                self.draw_players()
                self.draw_info_panel()
                
                # Draw either controls or prediction explanation
                if self.is_human_turn:
                    self.draw_human_controls()
                else:
                    self.draw_prediction_explanation()
                
                # Draw snake dialog if needed
                if self.waiting_for_snake_decision:
                    self.draw_snake_dialog()
                
                # Update the display
                pygame.display.flip()
                
                # Cap the frame rate
                clock.tick(60)
            
            # Show game over screen if game ended
            if game_over and running:
                restart_game = self.show_game_over_screen()
                if restart_game is False:
                    # Game will continue with reset state
                    continue
                else:
                    # Game will exit
                    running = False
        
        pygame.quit()
        sys.exit()

    def reset_game(self):
        """Reset the game to start a new round."""
        # Reset the game logic
        self.game.reset_game()
        
        # Reset GUI state variables
        self.dice_roll = None
        self.message_log = []
        self.is_human_turn = False
        self.human_prediction = None
        self.waiting_for_prediction = False
        self.waiting_for_reward_choice = False
        self.waiting_for_token_decision = False
        self.waiting_for_snake_decision = False
        self.current_player = None
        self.confirm_button_rect = None
        
        # Reset snake decision variables
        self.snake_head = None
        self.snake_tail = None
        self.tokens_required = None
        self.snake_player = None
        
        # Reset animation variables
        self.animation_in_progress = False
        self.player_animation_positions = {}
        self.animation_start_time = 0
        self.animation_start_pos = {}
        self.animation_target_pos = {}
        
        # Reset game flow control
        self.game_state = "INTRO"
        
        # Add a welcome message
        self.add_message("Starting a new game!")

    def create_fallback_board(self):
        """Create a fallback board image if the image file cannot be loaded."""
        board_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
        board_surface.fill((230, 230, 230))  # Light gray background
        
        # Calculate grid dimensions directly
        rows = cols = int(math.sqrt(self.game.board_size))
        cell_size = BOARD_SIZE // rows
        
        # Draw a grid pattern
        for row in range(rows):
            for col in range(cols):
                # Alternate colors
                if (row + col) % 2 == 0:
                    color = LIGHT_GREEN
                else:
                    color = BEIGE
                
                # Special colors for first and last cells
                pos = (rows - row - 1) * cols + col + 1
                if row % 2 == 1:  # Right to left row
                    pos = (rows - row - 1) * cols + (cols - col)
                
                if pos == 1:
                    color = (200, 200, 255)  # Light blue for start
                elif pos == self.game.board_size:
                    color = (255, 200, 200)  # Light red for finish
                
                rect_x = col * cell_size
                rect_y = row * cell_size
                pygame.draw.rect(board_surface, color, 
                                (rect_x, rect_y, cell_size, cell_size))
                pygame.draw.rect(board_surface, BLACK, 
                                (rect_x, rect_y, cell_size, cell_size), 1)
        
        return board_surface
    
    def minimize_window(self):
        """Minimize the game window."""
        pygame.display.iconify()
    
    def update_control_positions(self):
        """Update the positions of control buttons based on screen size."""
        self.fullscreen_button_rect = pygame.Rect(
            self.screen_width - 2*CONTROL_BUTTON_SIZE - CONTROL_PADDING, 
            WINDOW_CONTROLS_Y, 
            CONTROL_BUTTON_SIZE, 
            CONTROL_BUTTON_SIZE
        )
        self.minimize_button_rect = pygame.Rect(
            self.screen_width - CONTROL_BUTTON_SIZE, 
            WINDOW_CONTROLS_Y, 
            CONTROL_BUTTON_SIZE, 
            CONTROL_BUTTON_SIZE
        )
    
    # def draw_window_controls(self):
    #     """Draw window control buttons (fullscreen toggle and minimize)."""
    #     # Draw fullscreen button
    #     pygame.draw.rect(self.screen, GRAY, self.fullscreen_button_rect, border_radius=5)
    #     pygame.draw.rect(self.screen, BLACK, self.fullscreen_button_rect, 1, border_radius=5)
        
    #     # Draw fullscreen icon
    #     if self.fullscreen:
    #         # Draw exit fullscreen icon (smaller square)
    #         x, y, w, h = self.fullscreen_button_rect
    #         margin = 8
    #         pygame.draw.rect(self.screen, BLACK, 
    #                       (x + margin, y + margin, w - 2*margin, h - 2*margin), 2)
    #     else:
    #         # Draw enter fullscreen icon (larger square)
    #         x, y, w, h = self.fullscreen_button_rect
    #         margin = 5
    #         pygame.draw.rect(self.screen, BLACK, 
    #                       (x + margin, y + margin, w - 2*margin, h - 2*margin), 2)
        
    #     # Draw minimize button
    #     pygame.draw.rect(self.screen, GRAY, self.minimize_button_rect, border_radius=5)
    #     pygame.draw.rect(self.screen, BLACK, self.minimize_button_rect, 1, border_radius=5)
        
    #     # Draw minimize icon (horizontal line)
    #     x, y, w, h = self.minimize_button_rect
    #     line_y = y + h - 10
    #     pygame.draw.line(self.screen, BLACK, (x + 8, line_y), (x + w - 8, line_y), 2)

class HumanGUIPlayer(Player):
    def __init__(self, name: str, gui: SnakesAndLaddersGUI):
        # Pass a default color to the parent class constructor
        color = gui.player_colors[0] if hasattr(gui, 'player_colors') and gui.player_colors else "Red"
        super().__init__(name, color)
        self.gui = gui
    
    def make_prediction(self, game_state) -> int:
        self.gui.current_player = self
        self.gui.is_human_turn = True
        self.gui.waiting_for_prediction = True
        self.gui.human_prediction = None
        return 0  
    
    def choose_reward(self, game_state) -> int:
        self.gui.current_player = self
        self.gui.is_human_turn = True
        self.gui.waiting_for_reward_choice = True
        return 0 
    
    def decide_use_tokens(self, game_state, tokens_required: int) -> bool:
        self.gui.current_player = self
        self.gui.is_human_turn = True
        self.gui.waiting_for_token_decision = True
        return False  
    
    # Prevent pickle error by providing custom __deepcopy__ method
    def __deepcopy__(self, memo):
        # Create a regular Player instance instead of HumanGUIPlayer
        player_copy = Player(self.name, self.color)
        player_copy.position = self.position
        player_copy.tokens = self.tokens
        player_copy.skipped = self.skipped
        player_copy.on_board = self.on_board
        return player_copy

class ColorSelector:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.subtitle_font = pygame.font.SysFont('Arial', 24)
        self.font = pygame.font.SysFont('Arial', 20)
        self.color_options = {
            "Red": RED,
            "Blue": BLUE,
            "Green": GREEN,
            "Purple": PURPLE,
        }
        self.selected_color = None
        self.continue_button = None
    
    def draw(self):
        # Draw background
        self.screen.fill(WHITE)
        
        # Draw title
        title = self.title_font.render("Choose Your Player Color", True, BLACK)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Draw subtitle
        subtitle = self.subtitle_font.render("Click on a color to select it", True, BLACK)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Draw color options
        color_rects = {}
        colors_per_row = 4
        button_width = 120
        button_height = 80
        spacing = 30
        start_x = (SCREEN_WIDTH - (colors_per_row * button_width + (colors_per_row - 1) * spacing)) // 2
        start_y = 200
        
        i = 0
        for color_name, color_value in self.color_options.items():
            row = i // colors_per_row
            col = i % colors_per_row
            
            x = start_x + col * (button_width + spacing)
            y = start_y + row * (button_height + spacing)
            
            # Draw color button
            button_rect = pygame.Rect(x, y, button_width, button_height)
            pygame.draw.rect(self.screen, color_value, button_rect, border_radius=10)
            
            # Draw highlight if selected
            if self.selected_color == color_name:
                pygame.draw.rect(self.screen, BLACK, button_rect, 4, border_radius=10)
            else:
                pygame.draw.rect(self.screen, BLACK, button_rect, 2, border_radius=10)
            
            # Draw color name
            name_text = self.font.render(color_name, True, BLACK)
            name_rect = name_text.get_rect(center=(x + button_width // 2, y + button_height + 20))
            self.screen.blit(name_text, name_rect)
            
            # Store rect for click handling
            color_rects[color_name] = button_rect
            
            i += 1
        
        # Draw continue button if color is selected
        if self.selected_color:
            button_width = 200
            button_height = 60
            button_x = (SCREEN_WIDTH - button_width) // 2
            button_y = SCREEN_HEIGHT - 100
            
            self.continue_button = pygame.Rect(button_x, button_y, button_width, button_height)
            
            pygame.draw.rect(self.screen, (100, 200, 100), self.continue_button, border_radius=10)
            pygame.draw.rect(self.screen, BLACK, self.continue_button, 2, border_radius=10)
            
            continue_text = self.subtitle_font.render("Continue", True, BLACK)
            continue_rect = continue_text.get_rect(center=(button_x + button_width // 2, button_y + button_height // 2))
            self.screen.blit(continue_text, continue_rect)
        
        return color_rects
    
    def handle_click(self, pos, color_rects):
        # Check if a color was clicked
        for color_name, rect in color_rects.items():
            if rect.collidepoint(pos):
                self.selected_color = color_name
                return False  # Selection not complete
        
        # Check if continue button was clicked
        if self.selected_color and self.continue_button and self.continue_button.collidepoint(pos):
            return True  # Selection complete
        
        return False  # Selection not complete
