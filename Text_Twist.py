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

# Get all possible valid words (ensure main_word included)
def get_possible_words(letters, valid_words, main_word):
    possible_words = set()
    for i in range(3, len(letters) + 1):
        for perm in permutations(letters, i):
            possible_word = ''.join(perm)
            if possible_word in valid_words:
                possible_words.add(possible_word)

    possible_words.add(main_word)
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
        # each letter box placed horizontally
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
    six_letter_words = [w for w in valid_words if len(w) == 6]
    if not six_letter_words:
        raise RuntimeError("No 6-letter words found in words.txt")
    random_word = random.choice(six_letter_words)

    letters = generate_letters(random_word)
    possible_words = get_possible_words(letters, valid_words, random_word)

    found_words = set()
    score = 0
    message = ""
    message_timer = 0
    message_color = BLACK
    current_guess = []  # track clicked letters in order

    # Bottom-centered letter buttons positions (compute once)
    total_width = len(letters) * (BUTTON_SIZE + BUTTON_MARGIN) - BUTTON_MARGIN
    letters_y = HEIGHT - 140
    start_x = (WIDTH - total_width) // 2

    # Letter buttons (centered)
    letter_buttons = []
    for i, letter in enumerate(letters):
        x = start_x + i * (BUTTON_SIZE + BUTTON_MARGIN)
        y = letters_y
        letter_buttons.append(Button(x, y, BUTTON_SIZE, BUTTON_SIZE, letter.upper(), LIGHT_BLUE, BLUE, WHITE))

    # Action buttons (2 rows centered under letters)
    btn_row1_y = HEIGHT - 90
    btn_row2_y = HEIGHT - 40
    # widths
    w1, w2 = 120, 180
    gap = 10
    row_total = w1 + gap + w2
    left_x = (WIDTH - row_total) // 2

    submit_button = Button(left_x, btn_row1_y, w1, 50, "SUBMIT", GREEN, (50, 230, 50), WHITE)
    clear_button = Button(left_x + w1 + gap, btn_row1_y, w2, 50, "CLEAR", RED, (230, 50, 50), WHITE)
    shuffle_button = Button(left_x, btn_row2_y, w1, 50, "SHUFFLE", YELLOW, (230, 200, 50), BLACK)
    new_game_button = Button(left_x + w1 + gap, btn_row2_y, w2, 50, "NEW GAME", GRAY, DARK_GRAY, BLACK)

    # Group words by length
    grouped = {}
    for word in possible_words:
        grouped.setdefault(len(word), []).append(word)
    # convert to structure with headers
    for length, words in list(grouped.items()):
        grouped[length] = {"header": f"{length}-Letter Words", "words": words}

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        # Title & Score (top)
        title = font.render("TEXT TWIST", True, BLUE)
        screen.blit(title, (100, 50))
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (WIDTH - 200, 30))

        # Current guess (centered above letters)
        selected_text = font.render("".join(current_guess).upper(), True, BLACK)
        text_rect = selected_text.get_rect(center=(WIDTH // 2, letters_y - 50))
        screen.blit(selected_text, text_rect)

        # Draw letter buttons (they remain centered)
        for button in letter_buttons:
            button.check_hover(mouse_pos)
            button.draw(screen, font)

        # Draw action buttons
        for btn in (submit_button, clear_button, shuffle_button, new_game_button):
            btn.check_hover(mouse_pos)
            btn.draw(screen, font)

        # --- Draw word groups in the upper area ---
        # build fresh per-frame (so no stale positions)
        word_groups_draw = []

        panel_x = 120                # left margin for the word grid
        panel_y = 120                # top offset for the word grid
        panel_bottom = letters_y - 70  # keep a safe gap above letters/buttons
        row_height = LETTER_BOX_SIZE + 8
        # compute max rows that fits into available vertical space
        max_rows = max(1, (panel_bottom - panel_y) // row_height)

        lengths_sorted = sorted(grouped.keys())
        # precompute column widths for each group (based on longest word)
        col_widths = []
        for l in lengths_sorted:
            words = grouped[l]["words"]
            if words:
                max_word_width = max(len(w) * (LETTER_BOX_SIZE + 5) for w in words)
            else:
                max_word_width = LETTER_BOX_SIZE
            col_widths.append(max_word_width + 40)  # padding

        # draw each group in its own column; each group wraps into sub-columns when tall
        x_cursor = panel_x
        for idx, l in enumerate(lengths_sorted):
            words_info = grouped[l]
            x_offset = x_cursor
            y_offset = panel_y

            # Draw header (centered above group column)
            header_text = small_font.render(words_info["header"], True, DARK_GRAY)
            header_rect = header_text.get_rect(center=(x_offset + col_widths[idx] // 2, y_offset - 10))
            screen.blit(header_text, header_rect)

            row = 0
            subcol = 0
            for word in words_info["words"]:
                word_x = x_offset + subcol * col_widths[idx]
                word_y = y_offset + row * row_height

                wg = WordGroup(word, word_x, word_y)
                if word in found_words:
                    wg.fill_word()
                wg.draw(screen, font)
                word_groups_draw.append(wg)

                row += 1
                if row >= max_rows:
                    row = 0
                    subcol += 1

            # move cursor to next group's column
            x_cursor += col_widths[idx]

        # --- end word groups ---

        # Messages
        if message and message_timer > 0:
            msg_text = font.render(message, True, message_color)
            screen.blit(msg_text, (100, 600))
            message_timer -= 1

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Letter clicks (maintain click order)
            for button in letter_buttons:
                if button.is_clicked(mouse_pos, event):
                    if not button.is_selected:
                        button.is_selected = True
                        current_guess.append(button.text.lower())
                    else:
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

            # Shuffle letters (shuffle objects and reposition)
            if shuffle_button.is_clicked(mouse_pos, event):
                random.shuffle(letter_buttons)
                # reposition centered
                total_width = len(letter_buttons) * (BUTTON_SIZE + BUTTON_MARGIN) - BUTTON_MARGIN
                start_x = (WIDTH - total_width) // 2
                for i, button in enumerate(letter_buttons):
                    button.rect.x = start_x + i * (BUTTON_SIZE + BUTTON_MARGIN)

            # New game (start over)
            if new_game_button.is_clicked(mouse_pos, event):
                return main()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
