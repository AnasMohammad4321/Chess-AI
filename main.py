# import required modules
import Mechanics, AI_Engine     # import the Mechanics and AI_Engine modules
import pygame                   # pygame module for GUI
import sys                      # sys module for exiting the program
from multiprocessing import Process, Queue      # multiprocessing module for AI move finder

# declare required global variables 
BOARD_WIDTH = BOARD_HEIGHT = 512            # width and height of the board
DIMENSION = 8                               # dimension of the board is 8x8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION     # size of each square on the board
MAX_FPS = 120                               # for animations later on
IMAGES = {}                                 # dictionary of images
player_one = False              # if player one is a human, then this will be true
player_two = False              # if player two is a human, then this will be true



# main driver for the code
def main():
    pygame.init()                                                           # initialize pygame
    screen = pygame.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))           # create the screen
    pygame.display.set_caption('Chess.AI')                                  # set the title of the window
    icon = pygame.image.load('data/icon.png')                             # load the icon
    pygame.display.set_icon(icon)
    clock = pygame.time.Clock()                                             # create a clock object
    screen.fill(pygame.Color("white"))                                      # fill the screen with white color
    
    player_one, player_two = display_menu(screen)                           # display the menu and get the players' choices

    game_state = Mechanics.GameState()                                    # create a game state object
    valid_moves = game_state.getValidMoves()                                # get the valid moves for the current game state
    move_made = False                                                       # flag variable for when a move is made
    animate = False                                                         # flag variable for when we should animate a move
    loadImages()                                                            # do this only once before while loop
    running = True                                                          # flag variable for when the game is running
    square_selected = ()                                                    # no square is selected initially, this will keep track of the last click of the user (tuple(row,col))
    player_clicks = []                                                      # this will keep track of player clicks (two tuples)
    game_over = False                                                       # flag variable for when the game is over
    ai_thinking = False                                                     # flag variable for when the AI is thinking
    move_undone = False                                                     # flag variable for when a move is undone
    move_finder_process = None                                              # variable to store the process of the AI move finder

    # main game loop 
    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # mouse handler
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    location = pygame.mouse.get_pos()  # (x, y) location of the mouse
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:  # user clicked the same square twice
                        square_selected = ()  # deselect
                        player_clicks = []  # clear clicks
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  # append for both 1st and 2nd click
                    if len(player_clicks) == 2 and human_turn:  # after 2nd click
                        move = Mechanics.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()  # reset user clicks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]

            # key handler
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_a:  # undo when 'a' is pressed
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == pygame.K_s:  # reset the game when 's' is pressed
                    game_state = Mechanics.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

                if e.key == pygame.K_d:              # when 'd' is pressed
                    # stop the background music if it is playing
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    else:
                        # play the background music
                        pygame.mixer.music.play(-1)

        # AI move finder
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # used to pass data between threads
                move_finder_process = Process(target=AI_Engine.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():      
                ai_move = return_queue.get()            
                if ai_move is None:                 
                    ai_move = AI_Engine.findRandomMove(valid_moves)
                    #ai_move = AI_Engine.bestMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Black wins by checkmate")
            else:
                drawEndGameText(screen, "White wins by checkmate")

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        pygame.display.flip()

# functio to display the menu
def display_menu(screen):
    # Set the screen background
    screen.fill((0, 0, 0))

    # I want background music
    # initialize the mixer
    pygame.mixer.init()
    pygame.mixer.music.load('data/background.mp3')
    pygame.mixer.music.play(-1)                 
    background_image = pygame.image.load("data/1st.png").convert()
    # I want to reduce the transparency of the background image
    background_image.set_alpha(200)
    screen.blit(background_image, [0, 0])          
    # Display the screen
    pygame.display.flip()

    # Event loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    # stop the background music if it is playing
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    else:
                        # play the background music
                        pygame.mixer.music.play(-1)
                    # space bar to start the game
                if event.key == pygame.K_RETURN:
                    # remove the background image
                    screen.fill((0, 0, 0))
                    # display background image
                    background_image = pygame.image.load("data/2nd.png").convert()
                    # I want to reduce the transparency of the background image
                    background_image.set_alpha(200)
                    screen.blit(background_image, [0, 0])
                    # Display the screen
                    pygame.display.flip()

                    # # Event loop
                    while True:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT: 
                                pygame.quit()
                            elif event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_d:
                                    # stop the background music if it is playing
                                    if pygame.mixer.music.get_busy():
                                        pygame.mixer.music.stop()
                                    else:
                                        # play the background music
                                        pygame.mixer.music.play(-1)
                                if event.key == pygame.K_1:
                                    return True, True
                                elif event.key == pygame.K_2:
                                    # clear the screen
                                    screen.fill((0, 0, 0))
                                    # display image 
                                    background_image = pygame.image.load("data/3rd.png").convert()
                                    # I want to reduce the transparency of the background image
                                    background_image.set_alpha(200)
                                    screen.blit(background_image, [0, 0])
                                    # Display the screen
                                    pygame.display.flip()

                                    while True:
                                        for event in pygame.event.get():
                                            if event.type == pygame.QUIT:
                                                return
                                            elif event.type == pygame.KEYDOWN:
                                                if event.key == pygame.K_d:
                                                    # stop the background music if it is playing
                                                    if pygame.mixer.music.get_busy():
                                                        pygame.mixer.music.stop()
                                                    else:
                                                        # play the background music
                                                        pygame.mixer.music.play(-1)
                                                if event.key == pygame.K_1:
                                                    return True, False
                                                elif event.key == pygame.K_2:
                                                    return False, True
                                elif event.key == pygame.K_3:
                                    return False, False
                                elif event.key == pygame.K_4:
                                    pygame.quit()

# Highlight square selected and moves for piece selected
def highlightSquares(screen, game_state, valid_moves, square_selected):
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(pygame.Color('#224952'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == (
                'w' if game_state.white_to_move else 'b'):  # square_selected is a piece that can be moved
            # highlight selected square
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)  # transparency value 0 -> transparent, 255 -> opaque
            s.fill(pygame.Color('black'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # highlight moves from that square
            s.fill(pygame.Color('#5A5A5A'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))

# Animating a move
def animateMove(move, screen, board, clock):
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row = move.start_row + d_row * frame / frame_count
        col = move.start_col + d_col * frame / frame_count
        drawBoard(screen)
        drawPieces(screen, board)
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = pygame.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, color, end_square)
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = pygame.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        screen.blit(IMAGES[move.piece_moved], pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        pygame.display.flip()
        clock.tick(60)

# Drawing the board
def drawBoard(screen):
    global colors
    colors = [pygame.Color("#f0d9b5"), pygame.Color("#b58863")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            x = column * SQUARE_SIZE
            y = row * SQUARE_SIZE
            pygame.draw.rect(screen, color, pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))
            
            # draw the labels
            if row == 0:
                # draw alphabet labels
                label = chr(97 + column)
                font = pygame.font.SysFont(None, 15)
                text = font.render(label, True, pygame.Color("black"))
                screen.blit(text, (x+2, y+2))
            if column == 0:
                # draw number labels
                label = str(8 - row)
                font = pygame.font.SysFont(None, 15)
                text = font.render(label, True, pygame.Color("black"))
                screen.blit(text, (x+2, y+53))

# Drawing the pieces
def drawEndGameText(screen, text):
    font = pygame.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, pygame.Color("gray"))
    text_location = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, pygame.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))

# Drawing the pieces
def drawPieces(screen, board):
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], pygame.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

# Drawing the game state
def drawGameState(screen, game_state, valid_moves, square_selected):
    drawBoard(screen)  # draw squares on the board
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # draw pieces on top of those squares

# to load the images of the pieces
def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = pygame.transform.scale(pygame.image.load("data/" + piece + ".png"), (60, 60))     # scale the images to 60x60 pixels

if __name__ == "__main__":
    main()
