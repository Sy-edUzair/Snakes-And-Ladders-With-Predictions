import random
import numpy as np
import copy
from typing import List, Dict, Tuple, Optional, Union, Any

class Player:
    def __init__(self, name: str, color: str = "Red", is_ai: bool = False):
        self.name = name
        self.color = color
        self.position = 0
        self.is_ai = is_ai
        self.tokens = 0
        self.skipped = False
        self.prediction = None
        self.on_board = True  
    
    def reset(self):
        self.position = 0
        self.skipped = False
        self.prediction = None
        self.on_board = True  
    
    def __str__(self):
        return f"{self.name} at position {self.position} with {self.tokens} tokens"
    
    def make_prediction(self, game_state=None):
        """Make a prediction for the dice roll (1-6)."""
        if self.is_ai:
            return random.randint(1, 6)
        return None 
    
    def choose_reward(self, game_state) -> int:
        """Choose a reward when prediction is correct.
        1: Bonus roll, 2: Gain tokens
        To be overridden by AI Player."""
        return random.choice([1, 2])  
    
    def should_use_tokens_for_snake(self, snake_length, token_cost):
        """Decide whether to use tokens to avoid a snake."""
        if self.is_ai:
            if self.tokens < token_cost:
                return False
            if snake_length > 25 and self.tokens >= token_cost:
                return True
            if snake_length > 15 and self.tokens >= token_cost * 2:
                return True
            if snake_length <= 15 and self.tokens >= token_cost * 3:
                return True
            if self.position > 80 and self.tokens >= token_cost:
                return True
            return False
        
        return None 
    
    def decide_use_tokens(self, game_state, tokens_required: int) -> bool:
        """Alias for should_use_tokens_for_snake for consistency."""
        return self.should_use_tokens_for_snake(
            game_state.get_snake_length(self.position), tokens_required)

class AIPlayer(Player):
    def __init__(self, name: str, difficulty: str = "medium", color: str = "Red"):
        super().__init__(name, color, is_ai=True)
        self.difficulty = difficulty
        self.depth_limits = {
            "easy": 1,
            "medium": 2,
            "hard": 3,
            "expert": 4
        }
    
    def make_prediction(self, game_state) -> int:
        """Make a strategic prediction based on minimax algorithm."""
        if self.difficulty == "easy":
            return random.randint(1, 6)

        #Logic for other difficulties
        best_score = float('-inf')
        best_prediction = 1
        
        for prediction in range(1, 7):
            score = self._minimax_prediction(game_state, prediction, self.depth_limits[self.difficulty],float('-inf'), float('inf'),is_maximizing=True)
            
            if score > best_score:
                best_score = score
                best_prediction = prediction
        
        return best_prediction
    
    def _minimax_prediction(self, game_state, prediction: int, depth: int,alpha: float, beta: float, is_maximizing: bool) -> float:
        """Minimax algorithm for evaluating a prediction."""
        # Base case: reached max depth or terminal state
        if depth == 0 or self._is_terminal_state(game_state):
            return self._evaluate_state(game_state)
        
        # Calculate probabilities for each dice outcome
        dice_probs = [1/6] * 6 
        if is_maximizing:
            value = float('-inf')
            for dice_roll in range(1, 7):
                next_state = self._simulate_move(game_state, prediction, dice_roll)
                value = max(value, dice_probs[dice_roll-1] * self._minimax_prediction(next_state, prediction, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break 
            return value
        else:
            value = float('inf')
            for dice_roll in range(1, 7):
                next_state = self._simulate_move(game_state, prediction, dice_roll)
                value = min(value, dice_probs[dice_roll-1] * self._minimax_prediction(next_state, prediction, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value
    
    def _is_terminal_state(self, game_state) -> bool:
        """Check if the game state is terminal (someone won)."""
        for player in game_state.players:
            if player.position >= game_state.board_size:
                return True
        return False
    
    def _evaluate_state(self, game_state) -> float:
        """Evaluate the game state from this AI's perspective."""
        ai_player = None
        for player in game_state.players:
            if player.name == self.name:
                ai_player = player
                break
        
        if not ai_player:
            return 0.0
        
        position_score = ai_player.position / game_state.board_size * 100
        
        token_advantage = 0
        for player in game_state.players:
            if player.name != self.name:
                token_advantage += ai_player.tokens - player.tokens
        
        distance_to_win = game_state.board_size - ai_player.position
        score = position_score + token_advantage * 5 - distance_to_win * 2
        if ai_player.position >= game_state.board_size:
            score = 1000 
        
        return score
    
    def _simulate_move(self, game_state, prediction: int, dice_roll: int):
        """Simulate a move with the given prediction and dice roll."""
        simulated_state = copy.deepcopy(game_state)
        current_player_idx = simulated_state.current_player_idx
        current_player = simulated_state.players[current_player_idx]
        simulated_state.predictions[current_player.name] = prediction
        is_correct = (prediction == dice_roll)
        
        if is_correct:
            # Assume we always choose bonus roll for simulation
            current_player.tokens += 1  # Simplified reward
        
        # Move player
        current_player.position += dice_roll
        
        # Handle snakes and ladders
        if current_player.position in simulated_state.snakes:
            # Check if we have tokens to neutralize
            snake_head = current_player.position
            tokens_required = simulated_state.snake_sizes[snake_head]
            
            if current_player.tokens >= tokens_required:
                current_player.tokens -= tokens_required
            else:
                current_player.position = simulated_state.snakes[snake_head]
        
        if current_player.position in simulated_state.ladders:
            current_player.position = simulated_state.ladders[current_player.position]
        
        current_player.position = min(current_player.position, simulated_state.board_size)
        # Move to next player
        simulated_state.current_player_idx = (current_player_idx + 1) % len(simulated_state.players)
        return simulated_state
    
    def choose_reward(self, game_state) -> int:
        """Choose the best reward based on the current game state."""
        if self.difficulty == "easy":
            return random.choice([1, 2])
        # For higher difficulties, make a strategic choice
        # Calculate remaining distance to the goal
        remaining_distance = game_state.board_size - self.position
        
        # If we're close to the goal, prefer bonus roll
        if remaining_distance <= 12: #2 dice rolls
            return 1 
        
        # If we have very few tokens, gain more
        if self.tokens <= 1:
            return 2 
        
        dangerous_snakes_ahead = 0
        for snake_head in game_state.snakes:
            if self.position < snake_head <= self.position + 12: 
                dangerous_snakes_ahead += 1
        
        # If many dangerous snakes ahead, gather tokens
        if dangerous_snakes_ahead >= 2 and self.tokens < 3:
            return 2  # Gain tokens
        
        # Default strategy: alternate based on position parity
        if self.position % 2 == 0:
            return 1  # Bonus roll
        else:
            return 2  # Gain tokens
    
    def decide_use_tokens(self, game_state, tokens_required: int) -> bool:
        """Decide whether to use tokens to neutralize a snake."""
        if self.difficulty == "easy":
            return random.choice([True, False]) if self.tokens >= tokens_required else False
        
        # For higher difficulties, make a strategic decision
        # If we have plenty of tokens, use them
        if self.tokens >= tokens_required + 2:
            return True
        
        snake_head = self.position
        snake_tail = game_state.snakes[snake_head]
        snake_length = snake_head - snake_tail
        
        if snake_length > 25 and self.tokens >= tokens_required:
            return True
        remaining_distance = game_state.board_size - self.position
        if remaining_distance < 15 and self.tokens >= tokens_required:
            return True
        player_positions = [p.position for p in game_state.players if p.name != self.name]
        if all(self.position > pos for pos in player_positions) and self.tokens >= tokens_required:
            return True
        return snake_length > 15 and self.tokens >= tokens_required

class SnakesAndLadders:
    def __init__(self, board_size: int = 100, num_snakes: int = 6, num_ladders: int = 6):
        """Initialize the game with the given board size and number of snakes and ladders."""
        self.board_size = board_size
        self.players: List[Union[Player, AIPlayer]] = []
        self.current_player_idx = 0
        self.snakes: Dict[int, int] = {}  
        self.snake_sizes: Dict[int, int] = {}  
        self.ladders: Dict[int, int] = {} 
        self.predictions: Dict[str, int] = {}  
        self.dice = Dice()  
        self.game_log = []  
        self.game_state = "setup"  
        self.winner = None
        self.is_human_turn = False 
        
        # Always use the predefined board that matches the reference image
        self._setup_predefined_board()
    
    def _setup_predefined_board(self):
        """Set up the board with a predefined layout matching the Shutterstock image."""
        # Ladders (bottom to top) from the image
        self.ladders = {
            1: 38,    # Bottom left to middle
            4: 14,    # Bottom left to lower right
            9: 31,    # Bottom right to middle right
            21: 42,   # Left to middle left
            28: 84,   # Middle to upper middle
            36: 44,   # Middle to middle
            51: 67,   # Right middle to middle right
            71: 91,   # Upper right to top right
        }
        
        # Snakes (head to tail) from the image
        self.snakes = {
            98: 79,   # Near top to middle
            93: 73,   # Near top to middle
            64: 60,   # Middle to middle left
            54: 34,   # Middle to lower middle
            62: 19,   # Middle left to bottom
            87: 24,   # Upper middle to bottom
            45: 15,   # Middle to bottom
            11: 10,   # Middle to bottom (moved from 47->26)
            49: 5     # Right middle to bottom
        }
        
        # Calculate snake sizes based on length
        for head, tail in self.snakes.items():
            snake_length = head - tail
            self.calculate_snake_size(head, snake_length)
    
    def calculate_snake_size(self, head, snake_length):
        """Calculate the number of tokens required to neutralize a snake."""
        if snake_length > 25:
            self.snake_sizes[head] = 3
        elif snake_length > 15:
            self.snake_sizes[head] = 2
        else:
            self.snake_sizes[head] = 1
    
    def _setup_board(self, num_snakes: int, num_ladders: int):
        """Set up the board with randomized snakes and ladders."""
        
        # Create ladders using a zone-based approach to prevent crossing
        # Divide the board into zones for better ladder distribution
        board_zones = 4  # Number of horizontal zones on the board
        zone_size = self.board_size // board_zones
        
        ladder_destinations = set()  # Track where ladders end to prevent overlap
        ladder_starts = set()  # Track where ladders start
        ladder_bottoms = []  # Store all bottoms for snakes to avoid
        
        # Distribute ladders across zones to prevent crossing
        ladders_per_zone = max(1, num_ladders // board_zones)
        remaining_ladders = num_ladders
        
        # Create ladders zone by zone
        for zone in range(board_zones):
            zone_start = 1 + zone * zone_size
            zone_end = min(self.board_size - 10, (zone + 1) * zone_size)
            
            # Skip last few squares to avoid placing ladders too close to finish
            if zone == board_zones - 1:
                zone_end = min(zone_end, self.board_size - 15)
            
            # Number of ladders to place in this zone
            zone_ladders = min(ladders_per_zone, remaining_ladders)
            
            # Potential bottoms in this zone
            potential_bottoms = list(range(zone_start, zone_end - 10))
            random.shuffle(potential_bottoms)
            
            for _ in range(zone_ladders):
                if not potential_bottoms or remaining_ladders <= 0:
                    break
                    
                # Find a valid ladder bottom
                bottom = None
                while potential_bottoms and bottom is None:
                    candidate = potential_bottoms.pop(0)
                    # Ensure bottoms are spaced apart
                    if all(abs(candidate - existing) >= 5 for existing in ladder_starts):
                        bottom = candidate
                
                if bottom is None:
                    continue
                    
                # Calculate potential tops (only in higher zones)
                min_top_zone = min(board_zones - 1, zone + 1)  # At least one zone up
                max_top = self.board_size - 1
                min_top = bottom + 10  # Minimum climb of 10 spaces
                
                # Try to find a unique destination that's not too close to others
                attempts = 0
                found_top = False
                
                while attempts < 15 and not found_top:  # More attempts to find good spots
                    # Prefer destinations in higher zones for longer ladders
                    target_zone = random.randint(min_top_zone, board_zones - 1)
                    zone_min = max(min_top, 1 + target_zone * zone_size)
                    zone_max = min(max_top, (target_zone + 1) * zone_size)
                    
                    if zone_min >= zone_max:
                        attempts += 1
                        continue
                        
                    top = random.randint(zone_min, zone_max)
                    
                    # Check if this destination is unique and not too close to others
                    if (top not in ladder_destinations and 
                            all(abs(top - dest) >= 5 for dest in ladder_destinations)):
                        self.ladders[bottom] = top
                        ladder_destinations.add(top)
                        ladder_starts.add(bottom)
                        ladder_bottoms.append(bottom)
                        found_top = True
                        remaining_ladders -= 1
                        break
                        
                    attempts += 1
        
        # Create snakes (head -> tail)
        potential_snake_heads = list(range(20, self.board_size))
        # Don't place a snake where a ladder ends or within 3 squares of a ladder end
        for ladder_top in ladder_destinations:
            for offset in range(-3, 4):  # Avoid 3 squares before and after ladder top
                if 0 < ladder_top + offset < self.board_size:
                    if ladder_top + offset in potential_snake_heads:
                        potential_snake_heads.remove(ladder_top + offset)
        
        random.shuffle(potential_snake_heads)
        
        # Track where snake tails end to avoid overcrowding
        snake_tails = set()
        
        for i in range(num_snakes):
            if i >= len(potential_snake_heads):
                break
                
            head = potential_snake_heads[i]
            min_tail = max(1, head - 30)
            max_tail = max(min_tail, head - 10)
            
            # Try to find a unique destination
            attempts = 0
            valid_tail = False
            
            while attempts < 10 and not valid_tail:  # Limit attempts
                tail = random.randint(min_tail, max_tail)
                # Ensure this tail isn't at the bottom of a ladder or another snake tail
                # Also ensure it's not close to another snake tail or ladder bottom
                if (tail not in ladder_bottoms and 
                    tail not in snake_tails and
                    all(abs(tail - bottom) >= 3 for bottom in ladder_bottoms) and
                    all(abs(tail - other_tail) >= 3 for other_tail in snake_tails)):
                    
                    self.snakes[head] = tail
                    snake_tails.add(tail)
                    snake_length = head - tail
                    self.calculate_snake_size(head, snake_length)
                    valid_tail = True
                    
                attempts += 1
    
    def add_player(self, player: Union[Player, AIPlayer]):
        """Add a player to the game."""
        self.players.append(player)
    
    def get_snake_length(self, position):
        """Get the length of a snake at the given position."""
        if position in self.snakes:
            return position - self.snakes[position]
        return 0
    
    def get_current_player(self):
        """Get the current player."""
        return self.players[self.current_player_idx]
    
    def make_prediction(self, player_name: str, prediction: int):
        """Record a player's dice prediction."""
        if prediction < 1 or prediction > 6:
            raise ValueError("Prediction must be between 1 and 6")
        self.predictions[player_name] = prediction
    
    def roll_dice(self) -> int:
        """Roll the dice and return the result."""
        return self.dice.roll()
    
    def check_predictions(self, dice_roll: int) -> Dict[str, bool]:
        """Check which players predicted correctly."""
        return {player.name: self.predictions.get(player.name, 0) == dice_roll 
                for player in self.players}
    
    def handle_correct_opponent_predictions(self, dice_roll: int, current_player: Player):
        """Handle consequences of correct predictions by opponents."""
        correct_opponents = [p for p in self.players 
                             if p != current_player and self.predictions.get(p.name, 0) == dice_roll]
        
        if not correct_opponents:
            return
        
        # First correct opponent can skip current player's turn
        if len(correct_opponents) >= 1:
            self.log(f"{correct_opponents[0].name} predicted correctly! {current_player.name}'s turn will be skipped next round.")
            current_player.skipped = True
            correct_opponents[0].tokens += 1
        
        # Second correct opponent can move the player backward
        if len(correct_opponents) >= 2:
            self.log(f"{correct_opponents[1].name} predicted correctly! {current_player.name} moves backward by {dice_roll} spaces.")
            new_position = max(0, current_player.position - dice_roll)
            current_player.position = new_position
            correct_opponents[1].tokens += 1
        
        # Other correct opponents get tokens
        for opponent in correct_opponents[2:]:
            opponent.tokens += 1
            self.log(f"{opponent.name} predicted correctly and gained a token!")
    
    def handle_correct_current_player_prediction(self, player: Player, dice_roll: int) -> int:
        """Handle the reward for the current player's correct prediction.
        Returns choice: 1=bonus roll, 2=gain tokens."""
        
        # Ask player what reward they want
        self.log(f"Correct prediction! Choose your reward:")
        self.log("1. Get a bonus roll")
        self.log("2. Gain 2 tokens")
        
        # Get choice from player (could be AI or human)
        choice = player.choose_reward(self)
        
        if choice == 1:
            self.log(f"{player.name} chose to get a bonus roll!")
            return 1
        else:
            self.log(f"{player.name} chose to gain 2 tokens!")
            player.tokens += 2
            return 2
    
    def check_snake_encounter(self, player: Player) -> bool:
        """Check if player landed on a snake and handle token usage.
        Returns True if player used tokens to neutralize the snake."""
        
        if player.position in self.snakes:
            snake_head = player.position
            snake_tail = self.snakes[snake_head]
            tokens_required = self.snake_sizes[snake_head]
            
            self.log(f"{player.name} landed on a snake (position {snake_head})!")
            self.log(f"This snake requires {tokens_required} tokens to neutralize. You have {player.tokens} tokens.")
            use_tokens = False
            
            if player.tokens >= tokens_required:
                use_tokens = player.decide_use_tokens(self, tokens_required)
                
                if use_tokens:
                    player.tokens -= tokens_required
                    self.log(f"{player.name} used {tokens_required} tokens to neutralize the snake!")
                    return True
            
            player.position = snake_tail
            self.log(f"{player.name} slid down to position {snake_tail}!")
            
            return False
        
        return False
    
    def move_player(self, player: Player, spaces: int):
        """Move a player the specified number of spaces."""
        new_position = player.position + spaces
        if new_position > self.board_size:
            self.log(f"{player.name} needs exact dice to reach {self.board_size}. Stayed at {player.position}.")
            return
        
        player.position = new_position
        self.log(f"{player.name} moved to position {player.position}")
        if player.position in self.ladders:
            old_pos = player.position
            player.position = self.ladders[player.position]
            self.log(f"{player.name} climbed a ladder from {old_pos} to {player.position}!")
        player.position = min(player.position, self.board_size)
    
    def check_win(self, player: Player) -> bool:
        """Check if a player has won the game."""
        return player.position == self.board_size
    
    def next_player(self):
        """Move to the next player, skipping any players marked to be skipped."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        current_player = self.players[self.current_player_idx]
        if current_player.skipped:
            self.log(f"{current_player.name}'s turn is skipped!")
            current_player.skipped = False
            self.next_player()
        self.is_human_turn = not current_player.is_ai
    
    def log(self, message: str):
        """Add a message to the game log."""
        self.game_log.append(message)
        print(message)  
    def reset_game(self):
        """Reset the game state."""
        for player in self.players:
            player.reset()
        self.current_player_idx = 0
        self.predictions = {}
        self.game_log = []
        self.game_state = "setup"
        self.winner = None
        self.is_human_turn = False
    
    def play_turn(self):
        """Execute a single turn in the game."""
        current_player = self.players[self.current_player_idx]
        
        # Skip turn if applicable
        if current_player.skipped:
            self.log(f"{current_player.name}'s turn is skipped!")
            current_player.skipped = False
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            return False
        
    
        self.is_human_turn = not current_player.is_ai
        
        self.log(f"\n{current_player.name}'s turn")
        self.log(f"Current position: {current_player.position}")
        self.log(f"Tokens available: {current_player.tokens}")

        prediction = current_player.make_prediction(self)
        self.make_prediction(current_player.name, prediction)
        self.log(f"{current_player.name} predicts: {prediction}")
        

        for player in self.players:
            if player != current_player:
                opp_prediction = player.make_prediction(self)
                self.make_prediction(player.name, opp_prediction)
                self.log(f"{player.name} predicts: {opp_prediction}")
        
    
        dice_roll = self.roll_dice()
        self.log(f"Dice roll: {dice_roll}")
      
        correct_predictions = self.check_predictions(dice_roll)
        
        bonus_roll = False
        if correct_predictions[current_player.name]:
            choice = self.handle_correct_current_player_prediction(current_player, dice_roll)
            bonus_roll = (choice == 1)  # Choice 1 is bonus roll
        
        self.handle_correct_opponent_predictions(dice_roll, current_player)
        
        # Move player
        self.move_player(current_player, dice_roll)
        self.check_snake_encounter(current_player)
      
        if bonus_roll:
            self.log(f"{current_player.name} gets a bonus roll!")
            bonus_dice_roll = self.roll_dice()
            self.log(f"Bonus dice roll: {bonus_dice_roll}")
            self.move_player(current_player, bonus_dice_roll)
            self.check_snake_encounter(current_player)
        
        if self.check_win(current_player):
            self.log(f"\n🎉 {current_player.name} has reached position {self.board_size} and won the game! 🎉")
            self.winner = current_player
            self.game_state = "game_over"
            return True
        self.next_player()
        return False

class Dice:
    def __init__(self):
        self.value = 1
    
    def roll(self):
        self.value = random.randint(1, 6)
        return self.value
