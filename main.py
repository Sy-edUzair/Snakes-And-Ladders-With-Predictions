import pygame
import sys
from snl import SnakesAndLadders,AIPlayer
from snl_gui import SnakesAndLaddersGUI, HumanGUIPlayer, ColorSelector, SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Strategic Snakes and Ladders")
    color_selector = ColorSelector(screen)
    running = True
    selected_color_value = None
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
    game = SnakesAndLadders(board_size=100)
    gui = SnakesAndLaddersGUI(game)
    all_colors = list(color_selector.color_options.values())
    remaining_colors = [c for c in all_colors if c != selected_color_value][:1]  
    custom_player_colors = [selected_color_value] + remaining_colors
    gui.player_colors = custom_player_colors
    gui.player_images = []
    for i in range(2): 
        gui.player_images.append(gui.create_player_piece(i))
    human_player = HumanGUIPlayer("Human", gui)
    game.add_player(human_player)
    game.add_player(AIPlayer("AI Easy", difficulty="easy"))
    game.current_player_idx = 0
    game.is_human_turn = True
    
    # Start the game
    gui.run_game()

if __name__ == "__main__":
    main() 