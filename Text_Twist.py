import pygame
import random
import sys
from itertools import permutations

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1300, 700
FONT_SIZE = 32
LETTER_BOX_SIZE = 35
BUTTON_SIZE = 45
BUTTON_MARGIN = 10
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (100, 200, 100)
RED = (220, 100, 100)
BLUE = (50, 150, 220)
LIGHT_BLUE = (150, 200, 255)
DIM_BLUE = (100, 150, 200)
YELLOW = (250, 200, 50)
GRAY = (220, 220, 220)
DARK_GRAY = (80, 80, 80)

# Load words
def load_words():
    return sorted({w.strip().lower() for w in open("words.txt") if w.strip()})

# Generate letters from a random word
def generate_letters(word):
    letters = list(word)
    random.shuffle(letters)
    return letters

# Get all possible valid words
def get_possible_words(letters, valid_words):
    possible_words = set()
    for i in range(3, len(letters) + 1):
        for perm in permutations(letters, i):
            possible_word = ''.join(perm)
            if possible_word in valid_words:
                possible_words.add(possible_word)
    return sorted(possible_words, key=lambda w: (len(w), w))

# Button class
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.is_selected = False

    def draw(self, surface, font):
        color = DIM_BLUE if self.is_selected else (self.hover_color if self.is_hovered else self.color)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)

        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos)

# LetterBox class
class LetterBox:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.letter = ""

    def draw(self, surface, font):
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)
        if self.letter:
            text_surface = font.render(self.letter.upper(), True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)

# WordGroup class
class WordGroup:
    def __init__(self, word, x, y):
        self.word = word
        self.boxes = [LetterBox(x + i * (LETTER_BOX_SIZE + 5), y, LETTER_BOX_SIZE) for i in range(len(word))]

    def draw(self, surface, font):
        for box in self.boxes:
            box.draw(surface, font)

    def fill_word(self):
        for i, ch in enumerate(self.word):
            self.boxes[i].letter = ch

# Main Game
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Text Twist")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)
    small_font = pygame.font.Font(None, FONT_SIZE - 6)

    valid_words = load_words()
    random_word = random.choice(valid_words)
    letters = generate_letters(random_word)
    possible_words = get_possible_words(letters, valid_words)
    found_words = set()
    score = 0
    message = ""
    message_timer = 0
    message_color = BLACK
    current_guess = []  # track clicked letters in order

    # Letter buttons
    letter_buttons = []
    start_x = 100
    for i, letter in enumerate(letters):
        x = start_x + i * (BUTTON_SIZE + BUTTON_MARGIN)
        y = 250
        letter_buttons.append(Button(x, y, BUTTON_SIZE, BUTTON_SIZE, letter.upper(), LIGHT_BLUE, BLUE, WHITE))

    # Action buttons
    submit_button = Button(100, 350, 120, 50, "SUBMIT", GREEN, (50, 230, 50), WHITE)
    clear_button = Button(240, 350, 180, 50, "CLEAR", RED, (230, 50, 50), WHITE)
    shuffle_button = Button(100, 420, 120, 50, "SHUFFLE", YELLOW, (230, 200, 50), BLACK)
    new_game_button = Button(240, 420, 180, 50, "NEW GAME", GRAY, DARK_GRAY, BLACK)

    # Group words by length
    word_groups = []
    grouped = {}
    for word in possible_words:
        grouped.setdefault(len(word), []).append(word)

    # Layout word groups neatly in right panel
    start_y = 120
    panel_x = 500
    col_width = 200
    max_rows = 12
    for length, words in grouped.items():
        header = f"{length}-Letter Words"
        grouped[length] = {"header": header, "words": words}

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        # Title & Score
        title = font.render("TEXT TWIST", True, BLUE)
        screen.blit(title, (100, 50))
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (WIDTH - 200, 30))

        # Current guess
        selected_text = font.render("".join(current_guess).upper(), True, BLACK)
        screen.blit(selected_text, (100, 200))

        # Draw letter buttons
        for button in letter_buttons:
            button.check_hover(mouse_pos)
            button.draw(screen, font)

        # Draw action buttons
        for btn in (submit_button, clear_button, shuffle_button, new_game_button):
            btn.check_hover(mouse_pos)
            btn.draw(screen, font)

        # Draw word groups (organized by length in columns)
        base_x = panel_x
        y_offset = start_y
        col_width = 220
        bottom_limit = HEIGHT - 80

        for idx, length in enumerate(sorted(grouped.keys())):
            words_info = grouped[length]
            col_x = base_x + idx * col_width
            y_offset = start_y

            # Draw header
            header_text = small_font.render(words_info["header"], True, DARK_GRAY)
            screen.blit(header_text, (col_x, y_offset))
            y_offset += 25

            # Draw words in boxes
            for word in words_info["words"]:
                wg = next((g for g in word_groups if g.word == word), None)
                if not wg:
                    wg = WordGroup(word, col_x, y_offset)
                    word_groups.append(wg)
                wg.draw(screen, font)

                y_offset += LETTER_BOX_SIZE + 8

                # If we run out of vertical space, start new sub-column
                if y_offset > bottom_limit:
                    col_x += col_width // 2   # start half-width column beside it
                    y_offset = start_y + 25


        # Messages
        if message and message_timer > 0:
            msg_text = font.render(message, True, message_color)
            screen.blit(msg_text, (100, 600))
            message_timer -= 1

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle letter clicks (track order)
            for button in letter_buttons:
                if button.is_clicked(mouse_pos, event):
                    if not button.is_selected:  # select
                        button.is_selected = True
                        current_guess.append(button.text.lower())
                    else:  # deselect
                        button.is_selected = False
                        if button.text.lower() in current_guess:
                            current_guess.remove(button.text.lower())

            # Submit guess
            if submit_button.is_clicked(mouse_pos, event):
                guess = "".join(current_guess)
                if guess in possible_words and guess not in found_words:
                    found_words.add(guess)
                    score += len(guess) * 10
                    message = f"Good! +{len(guess)*10} points"
                    message_color = GREEN
                    message_timer = 60
                    for wg in word_groups:
                        if wg.word == guess:
                            wg.fill_word()
                else:
                    message = "Invalid guess!"
                    message_color = RED
                    message_timer = 60

                # reset selections
                current_guess = []
                for b in letter_buttons:
                    b.is_selected = False

            # Clear guess
            if clear_button.is_clicked(mouse_pos, event):
                current_guess = []
                for b in letter_buttons:
                    b.is_selected = False

            # Shuffle letters
            if shuffle_button.is_clicked(mouse_pos, event):
                random.shuffle(letter_buttons)
                start_x = 100
                for i, button in enumerate(letter_buttons):
                    button.rect.x = start_x + i * (BUTTON_SIZE + BUTTON_MARGIN)

            # New game
            if new_game_button.is_clicked(mouse_pos, event):
                return main()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


main()
