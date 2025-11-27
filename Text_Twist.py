import pygame
import random
import sys
import json
import os
from itertools import permutations

pygame.init()

# ---------------- Constants ----------------
WIDTH, HEIGHT = 1300, 700
FONT_SIZE = 32
LETTER_BOX_SIZE = 35
BUTTON_SIZE = 52
BUTTON_MARGIN = 12
FPS = 60

# Colors (palette)
WHITE = (250, 250, 250)
BLACK = (20, 20, 20)
GREEN = (100, 200, 100)
RED = (220, 80, 80)
BLUE = (45, 130, 200)
LIGHT_BLUE = (170, 200, 240)
DIM_BLUE = (110, 150, 200)
YELLOW = (245, 210, 90)
GRAY = (235, 235, 240)
DARK_GRAY = (80, 80, 90)
PANEL_BG = (245, 248, 252)
GOLD = (245, 210, 90)

SCORES_FILE = "scores.json"
WORDS_FILE = "words.txt"
# -------------------------------------------

# ---------------- Utilities ----------------
def load_words():
    """Load words from WORDS_FILE into a sorted unique list (lowercase)."""
    if not os.path.exists(WORDS_FILE):
        raise FileNotFoundError(f"{WORDS_FILE} not found in working directory.")
    with open(WORDS_FILE, encoding="utf-8") as f:
        return sorted({w.strip().lower() for w in f if w.strip()})

def load_scores():
    """Load leaderboard from SCORES_FILE (returns list)."""
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_score(name, score):
    """Save a name+score to SCORES_FILE and keep top 20."""
    scores = load_scores()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:20]
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=4)
# -------------------------------------------

# ---------------- Game Helpers --------------
def generate_letters(word):
    """Return a shuffled list of letters from word."""
    letters = list(word)
    random.shuffle(letters)
    return letters

def get_possible_words(letters, valid_words, main_word):
    """
    Compute all valid permutations (length >=3) from letters that exist in valid_words.
    Ensure the main_word is included.
    """
    possible_words = set()
    for i in range(3, len(letters) + 1):
        for perm in permutations(letters, i):
            candidate = ''.join(perm)
            if candidate in valid_words:
                possible_words.add(candidate)
    possible_words.add(main_word)
    return sorted(possible_words, key=lambda w: (len(w), w))
# -------------------------------------------

# ---------------- UI Classes ----------------
class Button:
    """Simple rectangular button with hover/selected state."""
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.is_selected = False

    def draw(self, surface, font, radius=10):
        color = DIM_BLUE if self.is_selected else (self.hover_color if self.is_hovered else self.color)
        pygame.draw.rect(surface, color, self.rect, border_radius=radius)
        pygame.draw.rect(surface, (30,30,30), self.rect, 2, border_radius=radius)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos)

class LetterBox:
    """Single square box which can hold a letter."""
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.letter = ""

    def draw(self, surface, font):
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=6)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 2, border_radius=6)
        if self.letter:
            text_surface = font.render(self.letter.upper(), True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)

class WordGroup:
    """Represents a horizontal series of LetterBoxes for a word."""
    def __init__(self, word, x, y):
        self.word = word
        self.boxes = [LetterBox(x + i * (LETTER_BOX_SIZE + 6), y, LETTER_BOX_SIZE) for i in range(len(word))]
        self.revealed = False

    def draw(self, surface, font):
        for box in self.boxes:
            box.draw(surface, font)

    def fill_word(self):
        for i, ch in enumerate(self.word):
            self.boxes[i].letter = ch
# -------------------------------------------

# ---------------- Difficulty Menu -----------
def difficulty_menu(screen, clock, fonts):
    """
    Show difficulty selection cards.
    Returns chosen word length (4,5,6,7).
    """
    font, small_font, big_font = fonts
    options = [("Easy", 4), ("Normal", 5), ("Hard", 6), ("Extreme", 7)]
    selected = 1  # default "Normal"
    running = True
    while running:
        mouse = pygame.mouse.get_pos()
        screen.fill(PANEL_BG)

        # Title card
        title_rect = pygame.Rect(120, 40, WIDTH - 240, 120)
        pygame.draw.rect(screen, WHITE, title_rect, border_radius=16)
        pygame.draw.rect(screen, DARK_GRAY, title_rect, 2, border_radius=16)
        title = big_font.render("TEXT TWIST", True, BLUE)
        screen.blit(title, title.get_rect(center=(WIDTH//2, 90)))
        subtitle = small_font.render("Choose difficulty (word length)", True, DARK_GRAY)
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH//2, 120)))

        # Option cards
        card_w = 220
        gap = 28
        total_w = len(options) * card_w + (len(options)-1) * gap
        start_x = (WIDTH - total_w) // 2
        y = 220
        for idx, (label, length) in enumerate(options):
            x = start_x + idx * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, 140)
            color = WHITE if idx != selected else LIGHT_BLUE
            pygame.draw.rect(screen, color, rect, border_radius=12)
            pygame.draw.rect(screen, DARK_GRAY, rect, 2, border_radius=12)
            txt = font.render(label, True, BLACK)
            screen.blit(txt, txt.get_rect(center=(x + card_w//2, y + 44)))
            desc = small_font.render(f"{length}-letter words", True, DARK_GRAY)
            screen.blit(desc, desc.get_rect(center=(x + card_w//2, y + 84)))
            hint = small_font.render("Click or press 1-4", True, DARK_GRAY)
            screen.blit(hint, hint.get_rect(center=(x + card_w//2, y + 114)))

        # Footer
        footer = small_font.render("Press ENTER to start with selected difficulty", True, DARK_GRAY)
        screen.blit(footer, footer.get_rect(center=(WIDTH//2, HEIGHT - 80)))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    selected = max(0, selected-1)
                elif event.key == pygame.K_RIGHT:
                    selected = min(len(options)-1, selected+1)
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    selected = 0
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    selected = 1
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    selected = 2
                elif event.key in (pygame.K_4, pygame.K_KP4):
                    selected = 3
                elif event.key == pygame.K_RETURN:
                    return options[selected][1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for idx in range(len(options)):
                    x = start_x + idx * (card_w + gap)
                    rect = pygame.Rect(x, y, card_w, 140)
                    if rect.collidepoint((mx, my)):
                        return options[idx][1]
        clock.tick(FPS)
def main_game(word_length):
    """
    Main game loop using chosen word_length.
    Left panel shows word groups (scrollable), right area has guess capsule and letters.
    """
    # Fonts
    font = pygame.font.Font(None, FONT_SIZE)
    small_font = pygame.font.Font(None, FONT_SIZE - 6)
    big_font = pygame.font.Font(None, 56)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Text Twist")
    clock = pygame.time.Clock()

    # Load dictionary and pick candidate words of the chosen length
    valid_words = load_words()
    candidates = [w for w in valid_words if len(w) == word_length]
    if not candidates:
        # fallback to 6-letter words if chosen length not present
        candidates = [w for w in valid_words if len(w) == 6]
        if not candidates:
            raise RuntimeError("No suitable words found in words.txt")

    random_word = random.choice(candidates)
    letters = generate_letters(random_word)
    possible_words = get_possible_words(letters, valid_words, random_word)

    # Layout split: left panel for words, right for guess/letters
    left_panel_w = min(760, WIDTH - 420)
    right_panel_x = left_panel_w + 40

    # Game state
    found_words = set()
    bonus_found = set()   # bonus dictionary words claimed
    score = 0
    message = ""
    message_timer = 0
    message_color = BLACK
    current_guess = []

    # Timer and bonuses
    timer_seconds = max(10, len(possible_words) * 9)
    timer_font = pygame.font.Font(None, 40)
    time_bonus_per_letter = 2
    game_over = False

    # Bottom positions for letters
    bottom_margin = 20
    button_height = 50
    gap_above_letters = 18
    letters_y = HEIGHT - bottom_margin - button_height - BUTTON_SIZE - gap_above_letters

    # Center letter buttons horizontally in the right area
    total_width = len(letters) * (BUTTON_SIZE + BUTTON_MARGIN) - BUTTON_MARGIN
    start_x = max(right_panel_x + (WIDTH - right_panel_x - total_width)//2, (WIDTH - total_width)//2)

    # Create letter buttons
    letter_buttons = []
    for i, letter in enumerate(letters):
        x = start_x + i * (BUTTON_SIZE + BUTTON_MARGIN)
        y = letters_y
        letter_buttons.append(Button(x, y, BUTTON_SIZE, BUTTON_SIZE, letter.upper(), LIGHT_BLUE, BLUE, WHITE))

    # Action buttons: single row bottom
    act_w = 140
    gap = 20
    actions_total = 3 * act_w + 2*gap
    left_x = right_panel_x + (WIDTH - right_panel_x - actions_total)//2
    submit_button = Button(left_x, HEIGHT - bottom_margin - button_height, act_w, button_height, "SUBMIT", GREEN, (50, 230, 50), WHITE)
    clear_button = Button(left_x + act_w + gap, HEIGHT - bottom_margin - button_height, act_w, button_height, "CLEAR", RED, (230, 50, 50), WHITE)
    shuffle_button = Button(left_x + 2*(act_w + gap), HEIGHT - bottom_margin - button_height, act_w, button_height, "SHUFFLE", YELLOW, (230, 200, 50), BLACK)
    new_game_button = Button(WIDTH - 180, 28, 140, 42, "NEW GAME", GRAY, DARK_GRAY, BLACK)

    # Group possible words by length for the left panel
    grouped = {}
    for word in possible_words:
        grouped.setdefault(len(word), []).append(word)
    for length, words in list(grouped.items()):
        grouped[length] = {"header": f"{length}-Letter Words", "words": words}

    # Build visible_required_words list for completion detection
    visible_required_words = []
    for length in sorted(grouped.keys()):
        visible_required_words.extend(grouped[length]["words"])

    # Scrolling state for left panel
    scroll_offset = 0
    scroll_speed = 40

    # Animations: floating point texts and reveal animations per word
    floating_texts = []
    reveal_animations = {}
    last_tick = pygame.time.get_ticks()

    running = True
    while running:
        now = pygame.time.get_ticks()
        elapsed = now - last_tick
        if elapsed >= 1000:
            dec = elapsed // 1000
            if not game_over:
                timer_seconds -= dec
                if timer_seconds <= 0:
                    timer_seconds = 0
                    game_over = True
            last_tick += dec * 1000

        mouse_pos = pygame.mouse.get_pos()
        screen.fill(PANEL_BG)

        # Top bar
        top_bar = pygame.Rect(20, 16, WIDTH - 40, 88)
        pygame.draw.rect(screen, WHITE, top_bar, border_radius=14)
        pygame.draw.rect(screen, DARK_GRAY, top_bar, 2, border_radius=14)
        title = big_font.render("TEXT TWIST", True, BLUE)
        screen.blit(title, (40, 30))
        # Timer and score in top bar
        timer_color = RED if timer_seconds <= 10 else BLACK
        timer_text = timer_font.render(f"Time: {timer_seconds}", True, timer_color)
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(timer_text, (WIDTH - 300, 24))
        screen.blit(score_text, (WIDTH - 300, 56))
        new_game_button.check_hover(mouse_pos)
        new_game_button.draw(screen, font, radius=12)

        # Left panel for words
        left_rect = pygame.Rect(20, 120, left_panel_w, HEIGHT - 180)
        pygame.draw.rect(screen, WHITE, left_rect, border_radius=12)
        pygame.draw.rect(screen, DARK_GRAY, left_rect, 2, border_radius=12)
        panel_title = small_font.render("Words", True, DARK_GRAY)
        screen.blit(panel_title, (left_rect.x + 16, left_rect.y + 12))

        # Content area inside left panel
        content_x = left_rect.x + 12
        content_y = left_rect.y + 44
        content_w = left_rect.width - 24
        content_h = left_rect.height - 56

        # Draw word groups inside left panel with horizontal columns and scrolling
        row_height = LETTER_BOX_SIZE + 10
        max_rows = max(1, content_h // row_height)
        lengths_sorted = sorted(grouped.keys())

        col_widths = []
        for l in lengths_sorted:
            words = grouped[l]["words"]
            max_word_len = max((len(w) for w in words), default=1)
            col_widths.append(max_word_len * (LETTER_BOX_SIZE + 6) + 40)

        x_cursor = content_x - scroll_offset
        max_right = 0
        for idx, l in enumerate(lengths_sorted):
            words_info = grouped[l]
            header_text = small_font.render(words_info["header"], True, DARK_GRAY)
            header_rect = header_text.get_rect(center=(x_cursor + col_widths[idx] // 2, content_y - 16))
            screen.blit(header_text, header_rect)

            row = 0
            subcol = 0
            for word in words_info["words"]:
                word_x = x_cursor + subcol * col_widths[idx]
                word_y = content_y + row * row_height

                wg = WordGroup(word, word_x, word_y)

                # If the word is found (visible or bonus), run reveal animation
                if word in found_words or word in bonus_found:
                    anim = reveal_animations.get(word)
                    if not anim:
                        reveal_animations[word] = {"tick": 0, "max_tick": 12 + len(word)*4}
                        anim = reveal_animations[word]
                    prog = anim["tick"] / anim["max_tick"]
                    reveal_count = int(prog * len(word))
                    reveal_count = max(0, min(len(word), reveal_count))
                    # draw boxes and letters progressively
                    for i, box in enumerate(wg.boxes):
                        pygame.draw.rect(screen, WHITE, box.rect, border_radius=6)
                        border_color = GOLD if (anim["tick"] < anim["max_tick"] and (anim["tick"]//3)%2 == 0) else DARK_GRAY
                        pygame.draw.rect(screen, border_color, box.rect, 2, border_radius=6)
                        if i < reveal_count:
                            txt = font.render(word[i].upper(), True, BLACK)
                            screen.blit(txt, txt.get_rect(center=box.rect.center))
                    anim["tick"] += 1
                    if anim["tick"] > anim["max_tick"]:
                        # finalize fill to keep letters visible
                        for i, ch in enumerate(word):
                            wg.boxes[i].letter = ch
                else:
                    wg.draw(screen, font)

                row += 1
                if row >= max_rows:
                    row = 0
                    subcol += 1

            total_subcols = subcol + 1
            x_cursor += col_widths[idx] * total_subcols
            max_right = max(max_right, x_cursor)

        # clamp left panel horizontal scroll
        scroll_offset = max(0, min(scroll_offset, max(0, max_right - content_x - content_w + 40)))

        # Right panel: guess area
        guess_card = pygame.Rect(right_panel_x, 140, WIDTH - right_panel_x - 40, 160)
        pygame.draw.rect(screen, WHITE, guess_card, border_radius=12)
        pygame.draw.rect(screen, DARK_GRAY, guess_card, 2, border_radius=12)
        guess_label = small_font.render("Your Guess", True, DARK_GRAY)
        screen.blit(guess_label, (guess_card.x + 18, guess_card.y + 12))

        # Capsule for typed letters
        capsule = pygame.Rect(guess_card.x + 18, guess_card.y + 46, guess_card.width - 36, 72)
        pygame.draw.rect(screen, PANEL_BG, capsule, border_radius=36)
        pygame.draw.rect(screen, (200,200,200), capsule, 2, border_radius=36)
        guess_text = big_font.render("".join(current_guess).upper(), True, BLACK)
        screen.blit(guess_text, guess_text.get_rect(center=capsule.center))

        # Draw letter buttons (bottom)
        for button in letter_buttons:
            button.check_hover(mouse_pos)
            button.draw(screen, font, radius=10)

        # Draw action buttons (bottom center)
        for btn in (submit_button, clear_button, shuffle_button):
            btn.check_hover(mouse_pos)
            btn.draw(screen, font, radius=12)

        # Messages
        if message and message_timer > 0:
            msg_surf = font.render(message, True, message_color)
            screen.blit(msg_surf, (right_panel_x + 20, guess_card.y + guess_card.height + 10))
            message_timer -= 1

        # Floating animations
        for ft in floating_texts[:]:
            surf = font.render(ft["text"], True, ft["color"])
            surf.set_alpha(max(0, int(255 * (ft["life"] / ft["max_life"]))))
            screen.blit(surf, (ft["x"], ft["y"]))
            ft["x"] += ft.get("vx", 0)
            ft["y"] += ft.get("vy", -1)
            ft["life"] -= 1
            if ft["life"] <= 0:
                floating_texts.remove(ft)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Mouse wheel scroll left panel content
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset -= event.y * scroll_speed
                scroll_offset = max(0, min(scroll_offset, max(0, max_right - content_x - content_w + 40)))

            # Keyboard input (only select first unused matching letter button)
            if event.type == pygame.KEYDOWN:
                key = event.unicode.lower()
                if key.isalpha() and len(key) == 1:
                    for button in letter_buttons:
                        if button.text.lower() == key and not button.is_selected:
                            button.is_selected = True
                            current_guess.append(button.text.lower())
                            break

                elif event.key == pygame.K_RETURN:
                    guess = "".join(current_guess).lower().strip()
                    if not guess:
                        message = "No input!"
                        message_color = RED
                        message_timer = 60
                    else:
                        # Already found visible word
                        if guess in found_words:
                            message = "Already found!"
                            message_color = DARK_GRAY
                            message_timer = 60
                        # Already claimed as bonus
                        elif guess in bonus_found:
                            message = "Already found!"
                            message_color = DARK_GRAY
                            message_timer = 60
                        # Bonus dictionary word (not in possible_words)
                        elif guess in valid_words and guess not in possible_words:
                            # accept once
                            bonus_found.add(guess)
                            pts = len(guess) * 5
                            score += pts
                            timer_seconds += len(guess)
                            message = f"Bonus! +{pts} pts +{len(guess)}s"
                            message_color = BLUE
                            message_timer = 90
                            floating_texts.append({
                                "text": f"+{pts}",
                                "x": right_panel_x + 160,
                                "y": 220,
                                "color": BLUE,
                                "vx": 0,
                                "vy": -1.2,
                                "life": 60,
                                "max_life": 60
                            })
                            reveal_animations[guess] = {"tick": 0, "max_tick": 12 + len(guess)*4}
                        # Normal visible-word scoring
                        elif guess in possible_words and guess not in found_words:
                            found_words.add(guess)
                            pts = len(guess) * 10
                            score += pts
                            timer_seconds += len(guess) * time_bonus_per_letter
                            message = f"Good! +{pts} pts +{len(guess)*time_bonus_per_letter}s"
                            message_color = GREEN
                            message_timer = 90
                            floating_texts.append({
                                "text": f"+{pts}",
                                "x": right_panel_x + 80,
                                "y": 220,
                                "color": GREEN,
                                "vx": 0,
                                "vy": -1.4,
                                "life": 60,
                                "max_life": 60
                            })
                            reveal_animations[guess] = {"tick": 0, "max_tick": 12 + len(guess)*4}
                        else:
                            message = "Invalid!"
                            message_color = RED
                            message_timer = 60

                    # reset selection and current_guess
                    current_guess = []
                    for b in letter_buttons:
                        b.is_selected = False

                elif event.key == pygame.K_BACKSPACE:
                    current_guess = []
                    for b in letter_buttons:
                        b.is_selected = False

                elif event.key == pygame.K_SPACE:
                    random.shuffle(letter_buttons)
                    total_width_local = len(letter_buttons) * (BUTTON_SIZE + BUTTON_MARGIN) - BUTTON_MARGIN
                    start_x_local = max(right_panel_x + (WIDTH - right_panel_x - total_width_local)//2, (WIDTH - total_width_local)//2)
                    for i, button in enumerate(letter_buttons):
                        button.rect.x = start_x_local + i * (BUTTON_SIZE + BUTTON_MARGIN)

                elif event.key == pygame.K_ESCAPE:
                    # Return to difficulty menu by exiting this function
                    return

            # Mouse interactions with letter buttons
            for button in letter_buttons:
                if button.is_clicked(mouse_pos, event):
                    if not button.is_selected:
                        button.is_selected = True
                        current_guess.append(button.text.lower())
                    else:
                        # deselect (remove first occurrence)
                        button.is_selected = False
                        if button.text.lower() in current_guess:
                            current_guess.remove(button.text.lower())

            # Submit button
            if submit_button.is_clicked(mouse_pos, event):
                guess = "".join(current_guess).lower().strip()
                if not guess:
                    message = "No input!"
                    message_color = RED
                    message_timer = 60
                else:
                    if guess in found_words or guess in bonus_found:
                        message = "Already found!"
                        message_color = DARK_GRAY
                        message_timer = 60
                    elif guess in valid_words and guess not in possible_words:
                        bonus_found.add(guess)
                        pts = len(guess) * 5
                        score += pts
                        timer_seconds += len(guess)
                        message = f"Bonus! +{pts} pts +{len(guess)}s"
                        message_color = BLUE
                        message_timer = 90
                        floating_texts.append({
                            "text": f"+{pts}",
                            "x": right_panel_x + 160,
                            "y": 220,
                            "color": BLUE,
                            "vx": 0,
                            "vy": -1.2,
                            "life": 60,
                            "max_life": 60
                        })
                        reveal_animations[guess] = {"tick": 0, "max_tick": 12 + len(guess)*4}
                    elif guess in possible_words and guess not in found_words:
                        found_words.add(guess)
                        pts = len(guess) * 10
                        score += pts
                        timer_seconds += len(guess) * time_bonus_per_letter
                        message = f"Good! +{pts} pts +{len(guess)*time_bonus_per_letter}s"
                        message_color = GREEN
                        message_timer = 90
                        floating_texts.append({
                            "text": f"+{pts}",
                            "x": right_panel_x + 80,
                            "y": 220,
                            "color": GREEN,
                            "vx": 0,
                            "vy": -1.4,
                            "life": 60,
                            "max_life": 60
                        })
                        reveal_animations[guess] = {"tick": 0, "max_tick": 12 + len(guess)*4}
                    else:
                        message = "Invalid!"
                        message_color = RED
                        message_timer = 60

                current_guess = []
                for b in letter_buttons:
                    b.is_selected = False

            # Clear
            if clear_button.is_clicked(mouse_pos, event):
                current_guess = []
                for b in letter_buttons:
                    b.is_selected = False

            # Shuffle
            if shuffle_button.is_clicked(mouse_pos, event):
                random.shuffle(letter_buttons)
                total_width_local = len(letter_buttons) * (BUTTON_SIZE + BUTTON_MARGIN) - BUTTON_MARGIN
                start_x_local = max(right_panel_x + (WIDTH - right_panel_x - total_width_local)//2, (WIDTH - total_width_local)//2)
                for i, button in enumerate(letter_buttons):
                    button.rect.x = start_x_local + i * (BUTTON_SIZE + BUTTON_MARGIN)

            # New game
            if new_game_button.is_clicked(mouse_pos, event):
                return

        # After event processing, check for completion: all visible words found
        if all(w in found_words for w in visible_required_words):
            # award completion bonus and end game
            message = "All words found! +100 bonus"
            message_color = GOLD
            message_timer = 180
            score += 100
            game_over = True

        # If timer expired, go to Game Over name entry
        if game_over or timer_seconds <= 0:
            name = ""
            entering_name = True
            while entering_name:
                screen.fill(PANEL_BG)
                card = pygame.Rect(200, 120, WIDTH-400, 420)
                pygame.draw.rect(screen, WHITE, card, border_radius=14)
                pygame.draw.rect(screen, DARK_GRAY, card, 2, border_radius=14)
                go_t = pygame.font.Font(None, 64).render("GAME OVER!", True, RED)
                screen.blit(go_t, go_t.get_rect(center=(WIDTH//2, 180)))
                final = font.render(f"Final Score: {score}", True, BLACK)
                screen.blit(final, final.get_rect(center=(WIDTH//2, 240)))
                prompt = font.render("Enter your name (press ENTER to save):", True, BLACK)
                screen.blit(prompt, (card.x + 40, 300))
                name_render = font.render(name, True, BLUE)
                screen.blit(name_render, (card.x + 40, 340))

                # leaderboard
                scores_list = load_scores()
                heading = small_font.render("Leaderboard (Top 10)", True, DARK_GRAY)
                screen.blit(heading, (card.x + 40, 380))
                for idx, entry in enumerate(scores_list[:10]):
                    text = small_font.render(f"{idx+1}. {entry['name']} - {entry['score']}", True, BLACK)
                    screen.blit(text, (card.x + 40, 410 + idx*26))

                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if name.strip() == "":
                                n = "ANON"
                            else:
                                n = name.strip()[:12]
                            save_score(n, score)
                            entering_name = False
                            return
                        elif event.key == pygame.K_BACKSPACE:
                            name = name[:-1]
                        else:
                            ch = event.unicode
                            if ch.isprintable() and len(name) < 12:
                                name += ch
                clock.tick(FPS)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

# ---------------- App Entrypoint ----------------
def run():
    # Initialize a small surface for the menu and pass fonts
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Text Twist")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)
    small_font = pygame.font.Font(None, FONT_SIZE - 6)
    big_font = pygame.font.Font(None, 56)
    fonts = (font, small_font, big_font)

    while True:
        chosen_length = difficulty_menu(screen, clock, fonts)
        main_game(chosen_length)

if __name__ == "__main__":
    run()
