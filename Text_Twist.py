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
GOLD = (245, 210, 90)

SCORES_FILE = "scores.json"
WORDS_FILE = "words.txt"
# -------------------------------------------

# ---------------- Utilities ----------------
def load_words():
    if not os.path.exists(WORDS_FILE):
        raise FileNotFoundError(f"{WORDS_FILE} not found.")
    return sorted({w.strip().lower() for w in open(WORDS_FILE, encoding="utf-8") if w.strip()})

def load_scores():
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_score(name, score):
    scores = load_scores()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:20]
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=4)
# -------------------------------------------

# ---------------- Game Helpers --------------
def generate_letters(word):
    letters = list(word)
    random.shuffle(letters)
    return letters

def get_possible_words(letters, valid_words, main_word):
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

class WordGroup:
    def __init__(self, word, x, y):
        self.word = word
        self.boxes = [LetterBox(x + i * (LETTER_BOX_SIZE + 5), y, LETTER_BOX_SIZE) for i in range(len(word))]
        # animation state per instance when revealed
        self.revealed = False

    def draw(self, surface, font):
        for box in self.boxes:
            box.draw(surface, font)

    def fill_word(self):
        for i, ch in enumerate(self.word):
            self.boxes[i].letter = ch
# -------------------------------------------

# ---------------- Main Game ----------------
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Text Twist")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)
    small_font = pygame.font.Font(None, FONT_SIZE - 6)
    big_font = pygame.font.Font(None, 60)

    valid_words = load_words()
    six_letter_words = [w for w in valid_words if len(w) == 6]
    if not six_letter_words:
        raise RuntimeError("No 6-letter words found in words.txt")
    random_word = random.choice(six_letter_words)

    letters = generate_letters(random_word)
    possible_words = get_possible_words(letters, valid_words, random_word)

    found_words = set()
    bonus_found = set()   # track already-claimed bonus words
    score = 0
    message = ""
    message_timer = 0
    message_color = BLACK
    current_guess = []

    # ---------------- NEW TIMER SYSTEM ----------------
    timer_seconds = max(10, len(possible_words) * 9)
    timer_font = pygame.font.Font(None, 40)
    time_bonus_per_letter = 2
    game_over = False
    # --------------------------------------------------

    # Layout controls
    bottom_margin = 20
    button_height = 50
    gap_between_button_rows = 10
    gap_above_buttons_and_letters = 10

    btn_row2_y = HEIGHT - bottom_margin - button_height
    btn_row1_y = btn_row2_y - button_height - gap_between_button_rows
    letters_y = btn_row1_y - gap_above_buttons_and_letters - BUTTON_SIZE

    total_width = len(letters) * (BUTTON_SIZE + BUTTON_MARGIN) - BUTTON_MARGIN
    start_x = (WIDTH - total_width) // 2

    # Letter buttons
    letter_buttons = []
    for i, letter in enumerate(letters):
        x = start_x + i * (BUTTON_SIZE + BUTTON_MARGIN)
        y = letters_y
        letter_buttons.append(Button(x, y, BUTTON_SIZE, BUTTON_SIZE, letter.upper(), LIGHT_BLUE, BLUE, WHITE))

    # Action buttons
    w1, w2 = 120, 180
    gap = 10
    row_total = w1 + gap + w2
    left_x = (WIDTH - row_total) // 2

    submit_button = Button(left_x, btn_row1_y, w1, button_height, "SUBMIT", GREEN, (50, 230, 50), WHITE)
    clear_button = Button(left_x + w1 + gap, btn_row1_y, w2, button_height, "CLEAR", RED, (230, 50, 50), WHITE)
    shuffle_button = Button(left_x, btn_row2_y, w1, button_height, "SHUFFLE", YELLOW, (230, 200, 50), BLACK)
    new_game_button = Button(left_x + w1 + gap, btn_row2_y, w2, button_height, "NEW GAME", GRAY, DARK_GRAY, BLACK)

    # Group words by length
    grouped = {}
    for word in possible_words:
        grouped.setdefault(len(word), []).append(word)
    for length, words in list(grouped.items()):
        grouped[length] = {"header": f"{length}-Letter Words", "words": words}

    # Horizontal scroll control
    scroll_offset = 0
    scroll_speed = 40

    # Floating animations for correct words
    floating_texts = []  # each: {text, x, y, life, color, vx, vy, max_life}

    # Per-word reveal animations: map word -> {tick, reveal_speed, max_tick}
    reveal_animations = {}

    # Timer tick control
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
        screen.fill(WHITE)

        # Game over / name-entry flow
        if game_over:
            name = ""
            entering_name = True
            while entering_name:
                screen.fill(WHITE)
                go_text = big_font.render("GAME OVER!", True, RED)
                screen.blit(go_text, go_text.get_rect(center=(WIDTH//2, 120)))

                score_text_final = font.render(f"Final Score: {score}", True, BLACK)
                screen.blit(score_text_final, (WIDTH//2 - 140, 200))

                prompt = font.render("Enter your name (press ENTER to save):", True, BLACK)
                screen.blit(prompt, (WIDTH//2 - 220, 260))

                name_render = font.render(name, True, BLUE)
                screen.blit(name_render, (WIDTH//2 - 140, 320))

                # leaderboard
                scores_list = load_scores()
                heading = small_font.render("Leaderboard (Top 10)", True, DARK_GRAY)
                screen.blit(heading, (WIDTH - 360, 120))
                for idx, entry in enumerate(scores_list[:10]):
                    text = small_font.render(f"{idx+1}. {entry['name']} - {entry['score']}", True, BLACK)
                    screen.blit(text, (WIDTH - 360, 160 + idx*28))

                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if name.strip() == "":
                                name = "ANON"
                            save_score(name.strip()[:12], score)
                            entering_name = False
                            return main()
                        elif event.key == pygame.K_BACKSPACE:
                            name = name[:-1]
                        else:
                            ch = event.unicode
                            if ch.isprintable() and len(name) < 12:
                                name += ch
                clock.tick(FPS)

        # Top UI
        title = font.render("TEXT TWIST", True, BLUE)
        screen.blit(title, (100, 50))
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (WIDTH - 200, 30))

        timer_color = RED if timer_seconds <= 10 else BLACK
        timer_text = timer_font.render(f"Time: {timer_seconds}", True, timer_color)
        screen.blit(timer_text, (WIDTH - 200, 70))

        selected_text = font.render("".join(current_guess).upper(), True, BLACK)
        text_rect = selected_text.get_rect(center=(WIDTH // 2, letters_y - 40))
        screen.blit(selected_text, text_rect)

        # Draw letter buttons
        for button in letter_buttons:
            button.check_hover(mouse_pos)
            button.draw(screen, font)

        # Draw action buttons
        for btn in (submit_button, clear_button, shuffle_button, new_game_button):
            btn.check_hover(mouse_pos)
            btn.draw(screen, font)

        # Draw word groups with reveal animations
        panel_x = 40 - scroll_offset
        panel_y = 120
        panel_bottom = letters_y - 30
        row_height = LETTER_BOX_SIZE + 8
        max_rows = max(1, (panel_bottom - panel_y) // row_height)

        lengths_sorted = sorted(grouped.keys())
        col_widths = []
        for l in lengths_sorted:
            words = grouped[l]["words"]
            max_word_len = max((len(w) for w in words), default=1)
            col_widths.append(max_word_len * (LETTER_BOX_SIZE + 5) + 40)

        x_cursor = panel_x
        max_right = 0
        for idx, l in enumerate(lengths_sorted):
            words_info = grouped[l]
            header_text = small_font.render(words_info["header"], True, DARK_GRAY)
            header_rect = header_text.get_rect(center=(x_cursor + col_widths[idx] // 2, panel_y - 20))
            screen.blit(header_text, header_rect)

            row = 0
            subcol = 0
            for word in words_info["words"]:
                word_x = x_cursor + subcol * col_widths[idx]
                word_y = panel_y + row * row_height

                wg = WordGroup(word, word_x, word_y)

                # If word is found, show reveal animation (letters revealed progressively)
                if word in found_words or word in bonus_found:
                    anim = reveal_animations.get(word)
                    if not anim:
                        # initialize animation
                        reveal_animations[word] = {"tick": 0, "max_tick": 12 + len(word)*4}
                        anim = reveal_animations[word]
                    # compute how many letters to reveal based on tick
                    prog = anim["tick"] / anim["max_tick"]
                    reveal_count = int(prog * len(word))
                    reveal_count = max(0, min(len(word), reveal_count))
                    # draw boxes; fill letters up to reveal_count
                    for i, box in enumerate(wg.boxes):
                        pygame.draw.rect(screen, WHITE, box.rect, border_radius=5)
                        # border flash during reveal
                        if anim["tick"] < anim["max_tick"]:
                            border_color = GOLD if ((anim["tick"] // 3) % 2 == 0) else BLACK
                        else:
                            border_color = BLACK
                        pygame.draw.rect(screen, border_color, box.rect, 3, border_radius=5)
                        if i < reveal_count:
                            # draw letter
                            text_surface = font.render(word[i].upper(), True, BLACK)
                            text_rect = text_surface.get_rect(center=box.rect.center)
                            screen.blit(text_surface, text_rect)
                    # advance tick
                    anim["tick"] += 1
                    if anim["tick"] > anim["max_tick"]:
                        # fully reveal to ensure letters remain
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

        # clamp horizontal scroll
        scroll_offset = max(0, min(scroll_offset, max(0, max_right - WIDTH + 100)))

        # Messages
        if message and message_timer > 0:
            msg_text = font.render(message, True, message_color)
            screen.blit(msg_text, (100, 600))
            message_timer -= 1

        # Floating point animations
        for ft in floating_texts[:]:
            surf = font.render(ft["text"], True, ft["color"])
            surf.set_alpha(max(0, int(255 * (ft["life"] / ft["max_life"]))))
            screen.blit(surf, (ft["x"], ft["y"]))
            ft["x"] += ft.get("vx", 0)
            ft["y"] += ft.get("vy", -1)
            ft["life"] -= 1
            if ft["life"] <= 0:
                floating_texts.remove(ft)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Mouse wheel -> horizontal scroll
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset -= event.y * scroll_speed
                scroll_offset = max(0, min(scroll_offset, max(0, max_right - WIDTH + 100)))

            # Keyboard input (single-letter selection fix)
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
                        # Already found (visible)
                        if guess in found_words:
                            message = "Already found!"
                            message_color = DARK_GRAY
                            message_timer = 60

                        # Already found as bonus
                        elif guess in bonus_found:
                            message = "Already found!"
                            message_color = DARK_GRAY
                            message_timer = 60

                        # Bonus (in dictionary but not possible)
                        elif guess in valid_words and guess not in possible_words:
                            # accept only once
                            bonus_found.add(guess)
                            pts = len(guess) * 5
                            score += pts
                            timer_seconds += len(guess)
                            message = f"Bonus! +{pts} pts +{len(guess)}s"
                            message_color = BLUE
                            message_timer = 90
                            floating_texts.append({
                                "text": f"+{pts}",
                                "x": WIDTH//2 + 60,
                                "y": HEIGHT//2 - 20,
                                "color": BLUE,
                                "vx": 0,
                                "vy": -1.2,
                                "life": 60,
                                "max_life": 60
                            })
                            # trigger reveal animation so it looks like a found word
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
                                "x": WIDTH//2,
                                "y": HEIGHT//2 - 20,
                                "color": GREEN,
                                "vx": 0,
                                "vy": -1.4,
                                "life": 60,
                                "max_life": 60
                            })
                            reveal_animations[guess] = {"tick": 0, "max_tick": 12 + len(guess)*4}

                        else:
                            # if it's in dictionary and in possible_words but already found handled above
                            # else invalid
                            message = "Invalid!"
                            message_color = RED
                            message_timer = 60

                    # clear selection after pressing enter
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
                    start_x_local = (WIDTH - total_width_local) // 2
                    for i, button in enumerate(letter_buttons):
                        button.rect.x = start_x_local + i * (BUTTON_SIZE + BUTTON_MARGIN)

                elif event.key == pygame.K_ESCAPE:
                    return main()

            # Mouse interactions
            for button in letter_buttons:
                if button.is_clicked(mouse_pos, event):
                    if not button.is_selected:
                        button.is_selected = True
                        current_guess.append(button.text.lower())
                    else:
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
                            "x": WIDTH//2 + 60,
                            "y": HEIGHT//2 - 20,
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
                            "x": WIDTH//2,
                            "y": HEIGHT//2 - 20,
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
                start_x_local = (WIDTH - total_width_local) // 2
                for i, button in enumerate(letter_buttons):
                    button.rect.x = start_x_local + i * (BUTTON_SIZE + BUTTON_MARGIN)

            # New game
            if new_game_button.is_clicked(mouse_pos, event):
                return main()

        # end events

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
