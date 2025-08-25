import pygame
import sys
import random

# --- Configuration ---
# Screen and Grid
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
GRID_WIDTH = 40
GRID_HEIGHT = 40
CELL_WIDTH = SCREEN_WIDTH // GRID_WIDTH
CELL_HEIGHT = SCREEN_HEIGHT // GRID_HEIGHT
GAME_FPS = 60

# Color Palette
BACKGROUND_COLOR = (13, 14, 16)
WHITE = (255, 255, 255)
LIFEFORM_COLOR = (0, 255, 0)
SHIP_COLOR = (255, 255, 0)
GUN_BULLET_COLOR = (255, 255, 0)
DGUN_BULLET_COLOR = (184, 53, 0)
SCORE_COLOR = (0, 255, 255)
AMMO_COLOR = (221, 160, 221)
BOSS_NAME_COLOR = (255, 0, 0)
BOSS_COLOR = (255, 105, 180)

# Classic Conway's Game of Life Rules (B3/S23)
LF_SURVIVE_MIN = 2
LF_SURVIVE_MAX = 3
LF_BORN_N = 3

# Ship Properties
SHIP_START_X = GRID_WIDTH // 2
SHIP_WIDTH_CELLS = 3
SHIP_HEIGHT_CELLS = 2
SHIP_SPEED = 0.5

# Bullet Properties
BULLET_SPEED = 8.0
DGUN_SHOTS_INITIAL = 25
DGUN_SHOTS_DELTA = 5
DGUN_DELTA = 5000
DGUN_SHOTS_ANGLE = 0.2

# Gameplay & Difficulty
SPAWN_DELTA_INITIAL = 2000
SPAWN_COUNT_INITIAL = 1
DIFFICULTY_DELTA = 30000
DIFFICULTY_RATIO = 0.99
LF_UPDATE_DELTA = 1000
BOSS_SPAWN_SCORE = 25

# --- Predefined Conway's Game of Life Patterns ---
PATTERNS = {
    "block": [[1, 1], [1, 1]],
    "glider": [[0, 1, 0], [0, 0, 1], [1, 1, 1]],
    "acorn": [[0,1,0,0,0,0,0],[0,0,0,1,0,0,0],[1,1,0,0,1,1,1]],
    "heart": [[1,0,0,0,1],[1,1,0,1,1],[1,0,1,0,1],[0,1,0,1,0],[0,0,1,0,0]]
}
SPACE_INVADER_PATTERN = [
    [0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0], [0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1], [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0]
]

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.2, 1.5)
        self.color = WHITE
        self.timer = 0
        self.color_change_interval = 10

    def update(self, is_win_screen=False):
        self.y -= self.speed
        if self.y < 0:
            self.y = SCREEN_HEIGHT
            self.x = random.randint(0, SCREEN_WIDTH)

        if is_win_screen:
            self.timer += 1
            if self.timer > self.color_change_interval:
                self.timer = 0
                self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        else:
            self.color = WHITE

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, 2, 2))


class GameOfLife:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.is_boss_cell = [[False for _ in range(width)] for _ in range(height)]

    def advance(self):
        new_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for r in range(self.height):
            for c in range(self.width):
                alive_neighbors = 0
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0: continue
                        nr, nc = r + i, c + j
                        if 0 <= nr < self.height and 0 <= nc < self.width and self.grid[nr][nc] == 1:
                            alive_neighbors += 1
                cell = self.grid[r][c]
                if cell == 1:
                    if LF_SURVIVE_MIN <= alive_neighbors <= LF_SURVIVE_MAX: new_grid[r][c] = 1
                else:
                    if alive_neighbors == LF_BORN_N: new_grid[r][c] = 1
        self.grid = new_grid

    def place_pattern(self, pattern, top, left, is_boss=False):
        for r_offset, row_data in enumerate(pattern):
            for c_offset, cell_val in enumerate(row_data):
                r, c = top + r_offset, left + c_offset
                if 0 <= r < self.height and 0 <= c < self.width and cell_val == 1:
                    self.grid[r][c] = 1
                    if is_boss: self.is_boss_cell[r][c] = True

    def is_area_clear(self, pattern, top, left):
        for r_offset, row_data in enumerate(pattern):
            for c_offset, cell_val in enumerate(row_data):
                if cell_val == 1:
                    r, c = top + r_offset, left + c_offset
                    if not (0 <= r < self.height and 0 <= c < self.width and self.grid[r][c] == 0):
                        return False
        return True

    def random_spawn(self, n):
        lowest_occupied_row = -1
        for r in range(self.height - 1, -1, -1):
            if any(self.grid[r]):
                lowest_occupied_row = r
                break

        if lowest_occupied_row == -1:
            spawn_row_start = 1
        else:
            spawn_row_start = lowest_occupied_row + 3

        safe_zone_top = self.height - 5 # Don't spawn in the bottom 5 rows

        for _ in range(n):
            pattern = PATTERNS[random.choice(list(PATTERNS.keys()))]
            pattern_height = len(pattern)
            pattern_width = len(pattern[0])

            effective_spawn_row = min(spawn_row_start, safe_zone_top - pattern_height)
            
            potential_cols = list(range(self.width - pattern_width))
            random.shuffle(potential_cols)
            
            placed = False
            for c in potential_cols:
                if self.is_area_clear(pattern, effective_spawn_row, c):
                    self.place_pattern(pattern, effective_spawn_row, c)
                    placed = True
                    break
            
            if not placed:
                for c in potential_cols:
                     if self.is_area_clear(pattern, 1, c):
                        self.place_pattern(pattern, 1, c)
                        break

    def kill_cell(self, r, c):
        if 0 <= r < self.height and 0 <= c < self.width:
            self.grid[r][c] = 0
            return True
        return False

    def draw(self, screen):
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == 1:
                    color = BOSS_COLOR if self.is_boss_cell[r][c] else LIFEFORM_COLOR
                    rect = pygame.Rect(c * CELL_WIDTH, r * CELL_HEIGHT, CELL_WIDTH, CELL_HEIGHT)
                    pygame.draw.rect(screen, color, rect)

class Player:
    def __init__(self, x, y):
        self.x, self.y, self.vel_x = x, y, 0

    def move(self):
        self.x += self.vel_x
        if self.x < 0: self.x = 0
        if self.x > GRID_WIDTH - SHIP_WIDTH_CELLS: self.x = GRID_WIDTH - SHIP_WIDTH_CELLS

    def draw(self, screen):
        px_x = self.x * CELL_WIDTH
        px_y = self.y * CELL_HEIGHT
        w, h = SHIP_WIDTH_CELLS * CELL_WIDTH, SHIP_HEIGHT_CELLS * CELL_HEIGHT
        points = [
            (px_x + w/2, px_y), (px_x + w, px_y + h * 0.8), (px_x + w * 0.8, px_y + h),
            (px_x + w * 0.2, px_y + h), (px_x, px_y + h * 0.8),
        ]
        pygame.draw.polygon(screen, SHIP_COLOR, points)

    def shoot(self, is_dgun=False):
        bullets = []
        bx = (self.x + SHIP_WIDTH_CELLS / 2) * CELL_WIDTH
        by = self.y * CELL_HEIGHT
        
        if is_dgun:
            angles = [0, -DGUN_SHOTS_ANGLE * 0.5, DGUN_SHOTS_ANGLE * 0.5, -DGUN_SHOTS_ANGLE, DGUN_SHOTS_ANGLE]
            for angle in angles:
                bullets.append(Bullet(bx, by, angle, -1, DGUN_BULLET_COLOR))
        else:
            bullets.append(Bullet(bx, by, 0, -1, GUN_BULLET_COLOR))
        return bullets

class Bullet:
    def __init__(self, x, y, vel_x, vel_y, color):
        self.x, self.y, self.vel_x, self.vel_y, self.color = x, y, vel_x, vel_y, color
        self.active = True

    def move(self):
        self.x += self.vel_x * BULLET_SPEED
        self.y += self.vel_y * BULLET_SPEED
        if not (0 < self.y < SCREEN_HEIGHT and 0 < self.x < SCREEN_WIDTH):
            self.active = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, 4, 10))

#Main class
class Game: 
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Conway Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24)
        self.large_font = pygame.font.SysFont("monospace", 75)
        self.reset_game()

    def reset_game(self, play_without_boss=False):
        self.lifeform = GameOfLife(GRID_WIDTH, GRID_HEIGHT)
        self.player = Player(SHIP_START_X, GRID_HEIGHT - SHIP_HEIGHT_CELLS - 1)
        self.bullets, self.score, self.level = [], 0, 1
        self.dgun_shots = DGUN_SHOTS_INITIAL
        self.spawn_delta, self.spawn_count = SPAWN_DELTA_INITIAL, SPAWN_COUNT_INITIAL
        self.boss_spawned, self.boss_health = False, 0
        self.play_without_boss = play_without_boss
        self.last_lf_update, self.last_spawn = pygame.time.get_ticks(), pygame.time.get_ticks()
        self.last_difficulty_increase, self.last_dgun_ammo_increase = pygame.time.get_ticks(), pygame.time.get_ticks()
        self.running, self.game_over, self.paused, self.show_help, self.you_won = True, False, False, True, False
        self.stars = [Star() for _ in range(150)]

    def run(self):
        while self.running:
            self.handle_events()
            if not self.paused and not self.game_over and not self.you_won:
                self.update()
            self.draw()
            self.clock.tick(GAME_FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                self._handle_key_press(event.key)
        
        if not self.game_over and not self.you_won and not self.paused:
            self._handle_movement()

    def _handle_key_press(self, key):
        if key == pygame.K_q: self.running = False
        if key == pygame.K_p: self.paused = not self.paused; self.show_help = False
        if key == pygame.K_h: self.show_help = not self.show_help

        if self.you_won:
            if key == pygame.K_r: self.reset_game(play_without_boss=False)
            if key == pygame.K_s: self.reset_game(play_without_boss=True)
            return

        if self.game_over:
            if key == pygame.K_r: self.reset_game()
            return
        
        if not self.paused:
            if key == pygame.K_z:
                self.show_help = False
                self.bullets.extend(self.player.shoot(is_dgun=False))
            if key == pygame.K_x and self.dgun_shots > 0:
                self.show_help = False
                self.dgun_shots -= 1
                self.bullets.extend(self.player.shoot(is_dgun=True))
    
    def _handle_movement(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.vel_x = -SHIP_SPEED
            self.show_help = False
        elif keys[pygame.K_RIGHT]:
            self.player.vel_x = SHIP_SPEED
            self.show_help = False
        else:
            self.player.vel_x = 0

    def spawn_boss(self):
        self.boss_spawned = True
        boss_width = len(SPACE_INVADER_PATTERN[0])
        spawn_col = (GRID_WIDTH - boss_width) // 2
        self.lifeform.place_pattern(SPACE_INVADER_PATTERN, 1, spawn_col, is_boss=True)

    def update(self):
        current_time = pygame.time.get_ticks()
        self._update_entities()
        self._update_game_of_life(current_time)
        self._update_spawning_and_difficulty(current_time)
        self._check_collisions()
        self._check_game_over()

    def _update_entities(self):
        self.player.move()
        for bullet in self.bullets:
            bullet.move()
        self.bullets = [b for b in self.bullets if b.active]

    def _update_game_of_life(self, current_time):
        if current_time - self.last_lf_update > LF_UPDATE_DELTA:
            self.lifeform.advance()
            self.last_lf_update = current_time
            if self.boss_spawned:
                self.boss_health = sum(
                    1 for r in range(GRID_HEIGHT) for c in range(GRID_WIDTH)
                    if self.lifeform.is_boss_cell[r][c] and self.lifeform.grid[r][c] == 1
                )
                if self.boss_health <= 0:
                    self.you_won = True
                    self.game_over = False

    def _update_spawning_and_difficulty(self, current_time):
        if not self.boss_spawned and current_time - self.last_spawn > self.spawn_delta:
            self.lifeform.random_spawn(self.spawn_count)
            self.last_spawn = current_time
        
        if current_time - self.last_difficulty_increase > DIFFICULTY_DELTA:
            self.level += 1
            self.spawn_delta *= DIFFICULTY_RATIO
            self.spawn_count += 1
            self.last_difficulty_increase = current_time
        
        if current_time - self.last_dgun_ammo_increase > DGUN_DELTA:
            self.dgun_shots += DGUN_SHOTS_DELTA
            self.last_dgun_ammo_increase = current_time
        
        if self.score >= BOSS_SPAWN_SCORE and not self.boss_spawned and not self.play_without_boss:
            self.spawn_boss()

    def _check_collisions(self):
        for bullet in self.bullets:
            if not bullet.active: continue
            grid_c = int(bullet.x // CELL_WIDTH)
            grid_r = int(bullet.y // CELL_HEIGHT)
            if 0 <= grid_r < GRID_HEIGHT and 0 <= grid_c < GRID_WIDTH and self.lifeform.grid[grid_r][grid_c] == 1:
                if self.lifeform.kill_cell(grid_r, grid_c):
                    self.score += 1
                    bullet.active = False
    
    def _check_game_over(self):
        player_x, player_y = int(self.player.x), int(self.player.y)
        for r_offset in range(SHIP_HEIGHT_CELLS):
            for c_offset in range(SHIP_WIDTH_CELLS):
                check_r, check_c = player_y + r_offset, player_x + c_offset
                if 0 <= check_r < GRID_HEIGHT and 0 <= check_c < GRID_WIDTH and self.lifeform.grid[check_r][check_c] == 1:
                    self.game_over = True
                    return 

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        for star in self.stars:
            star.update(is_win_screen=self.you_won)
            star.draw(self.screen)
            
        if self.you_won:
            self._draw_win_screen()
        elif self.game_over:
            self._draw_game_over_screen()
        else:
            self._draw_game_screen()

        pygame.display.flip()

    def _draw_text(self, text, font, color, x, y):
        self.screen.blit(font.render(text, True, color), (x, y))

    def _draw_centered_text(self, text, font, color, y_offset=0):
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + y_offset))
        self.screen.blit(text_surf, text_rect)

    def _draw_hud(self):
        self._draw_text(f"Score {self.score}", self.font, SCORE_COLOR, 10, 10)
        self._draw_text(f"Level {self.level}", self.font, WHITE, 10, 40)
        self._draw_text(f"Ammo {self.dgun_shots}", self.font, AMMO_COLOR, SCREEN_WIDTH - 150, 10)
        if self.boss_spawned and not self.you_won:
            self._draw_text(f"Boss Cells {self.boss_health}", self.font, BOSS_NAME_COLOR, SCREEN_WIDTH / 2 - 120, 10)

    def _draw_help(self):
        help_text = ["Move: Left/Right", "Fire: 'Z'", "Super Fire: 'X'", "Pause: 'P'", "Help: 'H'", "Quit: 'Q'"]
        for i, line in enumerate(help_text):
            self._draw_text(line, self.font, WHITE, 250, 200 + i * 40)

    def _draw_game_screen(self):
        self.lifeform.draw(self.screen)
        self.player.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        self._draw_hud()
        if self.show_help: self._draw_help()
        if self.paused: self._draw_centered_text("PAUSED", self.large_font, WHITE)

    def _draw_win_screen(self):
        self._draw_centered_text("YOU WON!", self.large_font, (50, 255, 50), y_offset=-50)
        self._draw_centered_text("R - Play Again (with boss)", self.font, WHITE, y_offset=20)
        self._draw_centered_text("S - Play Again (no boss)", self.font, WHITE, y_offset=60)

    def _draw_game_over_screen(self):
        self._draw_centered_text("GAME OVER", self.large_font, DGUN_BULLET_COLOR, y_offset=-50)
        self._draw_centered_text("Press 'R' to Restart", self.font, WHITE, y_offset=50)

if __name__ == '__main__':
    game = Game()
    game.run()
