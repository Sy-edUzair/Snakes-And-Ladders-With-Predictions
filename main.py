import pygame
import sys
from snl import SnakesAndLadders, Player, AIPlayer
from snl_gui import SnakesAndLaddersGUI, HumanGUIPlayer, ColorSelector, SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    # Initialize pygame for color selection
    pygame.init()
    
    # Create screen for color selection
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Strategic Snakes and Ladders")
    
    # Create color selector
    color_selector = ColorSelector(screen)
    running = True
    selected_color_value = None
    
    # Color selection loop
    while running:
        color_rects = color_selector.draw()
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if color_selector.handle_click(event.pos, color_rects):
                    selected_color_name = color_selector.selected_color
                    selected_color_value = color_selector.color_options[selected_color_name]
                    running = False
    
    # Create the game with a default board layout
    game = SnakesAndLadders(board_size=100)
    
    # Create GUI with the game
    gui = SnakesAndLaddersGUI(game)
    
    # Set player colors based on user selection
    all_colors = list(color_selector.color_options.values())
    remaining_colors = [c for c in all_colors if c != selected_color_value][:1]  # Get just 1 other color
    
    # Create new player colors list with selected color first
    custom_player_colors = [selected_color_value] + remaining_colors
    
    # Override the default player colors in the GUI instance and recreate player pieces
    gui.player_colors = custom_player_colors
    gui.player_images = []
    for i in range(2):  # Only need 2 player pieces now
        gui.player_images.append(gui.create_player_piece(i))
    
    # Add a human player controlled via GUI
    human_player = HumanGUIPlayer("Human", gui)
    game.add_player(human_player)
    
    # Add only AI Easy
    game.add_player(AIPlayer("AI Easy", difficulty="easy"))
    
    # Make sure the human player goes first and set the is_human_turn flag
    game.current_player_idx = 0
    game.is_human_turn = True
    
    # Start the game
    gui.run_game()

if __name__ == "__main__":
    main() 