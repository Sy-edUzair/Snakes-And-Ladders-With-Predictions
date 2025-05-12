# Snakes and Ladders with Prediction Challenge

A modern, interactive implementation of the classic Snakes and Ladders board game with additional prediction-based mechanics.

## Features

- Traditional 100-tile Snakes and Ladders gameplay with a vibrant custom board
- Multiplayer support for 2 players (1 human + 1 AI opponents)
- Prediction-based mechanics:
  - Players predict dice rolls before each turn
  - Correct predictions by the current player grant bonus actions
  - Correct predictions by opponents can cause negative effects
- Token system:
  - Earn tokens for correct predictions
  - Use tokens to neutralize snake effects
- Interactive UI with real-time game log
- Play again functionality

# Demo (Access using NU ID only)
Video Link: https://drive.google.com/file/d/1c1w5oDrXCS0bv1RUOUNnzP6QntwHze0q/view?usp=sharing

## Requirements

- Python 3.6+
- Pygame

## Installation

1. Make sure you have Python installed on your system.
2. Install Pygame:
```
pip install pygame
```

## How to Run

Run the game with the following command:
```
python main.py
```

## Game Rules

### Basic Rules
- Players take turns rolling a dice and moving their token.
- To enter the board, a player must roll a 1 or a 6.
- First player to reach square 100 exactly wins.
- Ladders move players upward, snakes move players downward.

### Prediction Mechanics
1. Before each turn, players must predict the dice value (1-6).
2. If the current player predicts correctly:
   - They can choose between a bonus roll or earning tokens.
3. If an opponent predicts correctly:
   - One opponent can skip the current player's next turn.
   - With multiple correct predictions, another opponent can move the current player backward.

### Token System
- Tokens are awarded for correct predictions.
- Tokens can be used to neutralize snake effects.
- The cost varies based on the snake length.

## Game Setup
1. Select the total number of players (2-4)
2. For the human player:
   - Enter your name
   - Choose your token color
3. AI players will be added automatically to reach the selected player count
4. Start playing!

## Game Controls
- Click buttons to make predictions, roll dice, and make choices
- Enter your name during setup
- AI players will make predictions and choices automatically

## Gameplay Tips
- Predict wisely - correct predictions give significant advantages
- Save tokens for longer snakes to maximize their value
- Watch out for opponents' predictions that could hinder your progress 
