import pygame
import math
import random
import time
import json
import os
from enum import Enum
from typing import List, Dict, Any, cast
from bresenham import bresenham
from rotation import rotation
from ellipse import filled_ellipse

WIDTH, HEIGHT = 1280, 720
FPS = 60

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 50, 50)
COLOR_GREEN = (50, 255, 50)
COLOR_BLUE = (50, 50, 255)
COLOR_YELLOW = (255, 255, 50)
COLOR_ORANGE = (255, 165, 0)
COLOR_PURPLE = (200, 50, 250)
COLOR_CYAN = (50, 255, 255)
COLOR_DARK_GRAY = (40, 40, 40)
COLOR_SKY_LIGHT = (40, 60, 100)

DURATIONS = [30, 60, 120]
HIGHSCORE_FILE = "highscore.json"

GRAVITY_BASE = 0.15
WIND_AMPLITUDE_BASE = 0.3
WIND_FREQUENCY = 0.02
NEEDLE_BASE = (50, HEIGHT - 50)
NEEDLE_LENGTH = 100
NEEDLE_ROT_SPEED_BASE = 1.5
ARROW_SPEED = 12
ARROW_LENGTH = 20

EXCLUSION_ZONE = pygame.Rect(0, HEIGHT - 200, 200, 200)

class GameState(Enum):
    DIFFICULTY_SELECT = 0
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3

class Difficulty(Enum):
    EASY = (0.7, 0.5, "EASY", COLOR_GREEN)
    NORMAL = (1.0, 1.0, "NORMAL", COLOR_YELLOW)
    HARD = (1.5, 1.5, "HARD", COLOR_RED)

    def __init__(self, g_mult: float, w_mult: float, label: str, color: tuple):
        self.g_mult = g_mult
        self.w_mult = w_mult
        self.label = label
        self.color = color

class BalloonType(Enum):
    SMALL_FAST = (1, 3, (25, 30), 1.5, COLOR_RED) 
    LARGE_SLOW = (2, 1, (45, 55), 0.8, COLOR_BLUE)

    def __init__(self, id_val: int, points: int, radii: tuple, speed_mult: float, color: tuple):
        self.points = points
        self.radii = radii
        self.speed_mult = speed_mult
        self.color = color

class PowerUpType(Enum):
    BONUS_TIME = ("+5s", COLOR_GREEN, 5)
    DOUBLE_POINTS = ("2x", COLOR_YELLOW, 8) 
    SLOW_MO = ("Slow", COLOR_CYAN, 5)

    def __init__(self, label: str, color: tuple, power_val: int):
        self.label = label
        self.color = color
        self.power_val = power_val

class Cloud:
    def __init__(self):
        self.x: float = 0.0
        self.y: float = 0.0
        self.speed: float = 0.0
        self.rx: int = 0
        self.ry: int = 0
        self.reset()
        self.x = float(random.randint(0, WIDTH))

    def reset(self):
        self.x = float(WIDTH + random.randint(50, 200))
        self.y = float(random.randint(50, 300))
        self.speed = random.uniform(0.5, 1.5)
        self.rx = random.randint(40, 80)
        self.ry = int(self.rx * 0.6)

    def update(self):
        self.x -= self.speed
        if self.x < -self.rx * 2:
            self.reset()

    def draw(self, screen):
        filled_ellipse(screen, int(self.x), int(self.y), self.rx, self.ry, (100, 120, 160))
        filled_ellipse(screen, int(self.x + self.rx*0.4), int(self.y - self.ry*0.2), int(self.rx*0.7), int(self.ry*0.8), (100, 120, 160))

class Particle:
    def __init__(self, x: float, y: float, color: tuple):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-6, 6)
        self.vy = random.uniform(-6, 6)
        self.life = 20
        self.color = color
        self.radius = float(random.randint(3, 6))
        self.angle = 0.0
        self.rot_speed = random.uniform(-10, 10)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1
        self.angle += self.rot_speed
        self.radius = max(0.0, self.radius - 0.15)

    def draw(self, screen):
        if self.life > 0:
            rad = math.radians(self.angle)
            offset = self.radius * 1.5
            p1 = rotation(self.x + offset, self.y, self.x, self.y, rad)
            p2 = rotation(self.x - offset, self.y, self.x, self.y, rad)
            p3 = rotation(self.x, self.y + offset, self.x, self.y, rad)
            p4 = rotation(self.x, self.y - offset, self.x, self.y, rad)
            
            p1_x, p1_y = int(p1[0][0]), int(p1[1][0])
            p2_x, p2_y = int(p2[0][0]), int(p2[1][0])
            p3_x, p3_y = int(p3[0][0]), int(p3[1][0])
            p4_x, p4_y = int(p4[0][0]), int(p4[1][0])
            
            for px, py in bresenham(p1_x, p1_y, p2_x, p2_y): screen.set_at((px, py), self.color)
            for px, py in bresenham(p3_x, p3_y, p4_x, p4_y): screen.set_at((px, py), self.color)
            filled_ellipse(screen, int(self.x), int(self.y), int(self.radius), int(self.radius), self.color)

class PowerUp:
    def __init__(self):
        self.type = cast(PowerUpType, random.choice([PowerUpType.BONUS_TIME, PowerUpType.DOUBLE_POINTS, PowerUpType.SLOW_MO]))
        self.rx = 20
        self.ry = 20
        self.x: float = 0.0
        self.y: float = 0.0
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.active = False
        self.spawn_time: int = 0
        self.reset()

    def reset(self):
        self.x = float(random.randint(300, WIDTH - 100))
        self.y = float(-self.ry)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(2, 4)
        self.active = True
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt: float):
        self.x += self.vx
        self.y += self.vy
        if self.y > HEIGHT or pygame.time.get_ticks() - self.spawn_time > 12000:
            self.active = False

    def draw(self, screen, font):
        if not self.active: return
        pulse = 1.0 + 0.15 * math.sin(pygame.time.get_ticks() * 0.012)
    
        for i in range(3, 0, -1):
            filled_ellipse(screen, int(self.x), int(self.y), int(self.rx * pulse + i*2), int(self.ry * pulse + i*2), COLOR_WHITE)
        filled_ellipse(screen, int(self.x), int(self.y), int(self.rx * pulse), int(self.ry * pulse), self.type.color)
        label_surf = font.render(self.type.label, True, COLOR_WHITE)
        screen.blit(label_surf, (int(self.x - label_surf.get_width()//2), int(self.y - label_surf.get_height()//2)))

class Balloon:
    def __init__(self, balloon_type: Any = None):
        if balloon_type is None:
            self.type = cast(BalloonType, random.choice([BalloonType.SMALL_FAST, BalloonType.LARGE_SLOW]))
        else:
            self.type = balloon_type
        self.base_rx: int = random.randint(*self.type.radii)
        self.base_ry: int = int(self.base_rx * 1.2)
        self.rx: int = self.base_rx
        self.ry: int = self.base_ry
        self.color: tuple = self.type.color
        self.x: float = 0.0
        self.y: float = 0.0
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.popped = False
        self.pop_frame = 0
        self.scale_t: float = float(random.uniform(0, 2 * math.pi))
        self.reset()

    def reset(self):
        side = random.choice(['top', 'right'])
        if side == 'top':
            self.x = float(random.randint(300, WIDTH - 50))
            self.y = float(-self.ry)
        else:
            self.x = float(WIDTH + self.base_rx)
            self.y = float(random.randint(50, HEIGHT - 300))
        self.vx = random.uniform(-2, -0.5) * self.type.speed_mult
        self.vy = random.uniform(0.5, 2) * self.type.speed_mult
        self.popped = False
        self.pop_frame = 0

    def update(self, frames: int, difficulty_mult: float, slow_mo: bool = False):
        if self.popped:
            self.pop_frame += 1
            return
        self.scale_t += 0.05
        pulse = 1.0 + 0.05 * math.sin(self.scale_t)
        self.rx = int(self.base_rx * pulse)
        self.ry = int(self.base_ry * pulse)
        speed_factor = 0.5 if slow_mo else 1.0
        wind = WIND_AMPLITUDE_BASE * math.sin(WIND_FREQUENCY * frames) * difficulty_mult * speed_factor
        self.vx += wind
        self.vy += GRAVITY_BASE * difficulty_mult * speed_factor
        self.x += self.vx * speed_factor
        self.y += self.vy * speed_factor
        if self.y > HEIGHT + self.ry or self.x < -self.rx: self.reset()
        if EXCLUSION_ZONE.collidepoint(int(self.x), int(self.y)): self.reset()

    def draw(self, screen):
        if self.popped:
            scale = max(0.0, 1.0 - (self.pop_frame / 10.0))
            if scale > 0:
                filled_ellipse(screen, int(self.x), int(self.y), int(self.rx * scale), int(self.ry * scale), COLOR_WHITE)
            return
        filled_ellipse(screen, int(self.x), int(self.y), self.rx, self.ry, self.color)
        filled_ellipse(screen, int(self.x - self.rx*0.3), int(self.y - self.base_ry*0.3), int(self.rx*0.2), int(self.ry*0.2), COLOR_WHITE)

    def check_collision(self, px: float, py: float) -> bool:
        if self.popped: return False
        val = ((px - self.x)**2 / self.rx**2) + ((py - self.y)**2 / self.ry**2)
        return val <= 1.1

class FiredArrow:
    def __init__(self, x: float, y: float, angle_rad: float):
        self.x1 = float(x)
        self.y1 = float(y)
        self.angle = angle_rad
        self.dx = math.cos(angle_rad) * ARROW_SPEED
        self.dy = -math.sin(angle_rad) * ARROW_SPEED
        self.active = True
        self.trail: List[tuple] = []
        
    def update(self):
        self.trail.append((self.x1, self.y1))
        if len(self.trail) > 5: self.trail.pop(0)
        self.x1 += self.dx
        self.y1 += self.dy
        if self.x1 < 0 or self.x1 > WIDTH or self.y1 < 0 or self.y1 > HEIGHT:
            self.active = False
            
    def draw(self, screen):
        for i, pos in enumerate(self.trail):
            alpha_ratio = (i / len(self.trail))
            color = (int(100 * alpha_ratio), int(200 * alpha_ratio), int(255 * alpha_ratio))
            screen.set_at((int(pos[0]), int(pos[1])), color)
        x2 = self.x1 + math.cos(self.angle) * ARROW_LENGTH
        y2 = self.y1 - math.sin(self.angle) * ARROW_LENGTH
        for p in bresenham(int(self.x1), int(self.y1), int(x2), int(y2)):
            screen.set_at(p, COLOR_WHITE)

class GameSession:
    def __init__(self, duration: int, difficulty: Difficulty):
        self.duration = duration
        self.difficulty = difficulty
        self.score: int = 0
        self.stat_small: int = 0
        self.stat_large: int = 0
        self.stat_fired: int = 0
        self.stat_hit: int = 0
        self.start_ticks: int = pygame.time.get_ticks()
        self.bonus_time: int = 0
        self.balloons: List[Balloon] = [Balloon() for _ in range(5)]
        self.arrows: List[FiredArrow] = []
        self.particles: List[Particle] = []
        self.powerups: List[PowerUp] = []
        self.double_points_end: int = 0
        self.slow_mo_end: int = 0
        self.frames_count: int = 0

def load_high_scores() -> Dict[str, List[int]]:
    if not os.path.exists(HIGHSCORE_FILE):
        return {"30": [0], "60": [0], "120": [0]}
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            data = json.load(f)
            return cast(Dict[str, List[int]], data)
    except:
        return {"30": [0], "60": [0], "120": [0]}

def save_high_score(duration: int, score: int) -> bool:
    scores_dict = load_high_scores()
    key = str(duration)
    history = scores_dict.get(key, [])
    history.append(score)
    history.sort(reverse=True)
    scores_dict[key] = history[:3]
    with open(HIGHSCORE_FILE, 'w') as f:
        json.dump(scores_dict, f)
    return score >= history[0]

def draw_text_outlined(screen, text: str, font, color, pos, outline_color=COLOR_BLACK):
    surf = font.render(text, True, color)
    ox, oy = pos
    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        outline_surf = font.render(text, True, outline_color)
        screen.blit(outline_surf, (ox + dx, oy + dy))
    screen.blit(surf, (ox, oy))

def draw_text_centered(screen, text: str, font, color, y, outline_color=COLOR_BLACK):
    surf = font.render(text, True, color)
    x = (WIDTH - surf.get_width()) // 2
    draw_text_outlined(screen, text, font, color, (x, y), outline_color)

def draw_wind_indicator(screen, wind_force: float):
    cx, cy = WIDTH - 80, 150
    for p in bresenham(cx-20, cy, cx+20, cy):
         if p[0] % 4 == 0: screen.set_at(p, (100, 100, 150))
    length = int(wind_force * 50)
    if abs(length) > 2:
        end_x = cx + length
        for p in bresenham(cx, cy, end_x, cy): screen.set_at(p, COLOR_CYAN)
        angle = 0.0 if length > 0 else math.pi
        h1 = rotation(float(end_x - 10), float(cy - 5), float(end_x), float(cy), angle)
        h2 = rotation(float(end_x - 10), float(cy + 5), float(end_x), float(cy), angle)
        for p in bresenham(end_x, cy, int(h1[0][0]), int(h1[1][0])): screen.set_at(p, COLOR_CYAN)
        for p in bresenham(end_x, cy, int(h2[0][0]), int(h2[1][0])): screen.set_at(p, COLOR_CYAN)

def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Balloon Popping Game")
    clock = pygame.time.Clock()
    font_large = pygame.font.SysFont("Arial", 64, bold=True)
    font_medium = pygame.font.SysFont("Arial", 32, bold=True)
    font_small = pygame.font.SysFont("Arial", 24)
    font_tiny = pygame.font.SysFont("Arial", 18)
    sounds: Dict[str, pygame.mixer.Sound] = {}
    try:
        sounds['pop'] = pygame.mixer.Sound('pop.wav')
        sounds['fire'] = pygame.mixer.Sound('shoot.wav')
        pygame.mixer.music.load('music.mp3')
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.2)
    except: pass
    state = GameState.DIFFICULTY_SELECT
    difficulty = Difficulty.NORMAL
    selected_dur_idx = 0
    high_scores = load_high_scores()
    clouds = [Cloud() for _ in range(6)]
    session: Any = None
    needle_angle: float = 45.0
    needle_dir: int = 1
    running = True
    while running:
        screen.fill(COLOR_SKY_LIGHT)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if state == GameState.DIFFICULTY_SELECT:
                    if event.key == pygame.K_1: difficulty = Difficulty.EASY; state = GameState.MENU
                    elif event.key == pygame.K_2: difficulty = Difficulty.NORMAL; state = GameState.MENU
                    elif event.key == pygame.K_3: difficulty = Difficulty.HARD; state = GameState.MENU
                    elif event.key == pygame.K_ESCAPE: running = False
                elif state == GameState.MENU:
                    if event.key == pygame.K_1: selected_dur_idx = 0
                    elif event.key == pygame.K_2: selected_dur_idx = 1
                    elif event.key == pygame.K_3: selected_dur_idx = 2
                    elif event.key in [pygame.K_UP, pygame.K_DOWN]:
                        selected_dur_idx = (selected_dur_idx + (1 if event.key == pygame.K_DOWN else -1)) % 3
                    elif event.key == pygame.K_SPACE:
                        session = GameSession(DURATIONS[selected_dur_idx], difficulty)
                        state = GameState.PLAYING
                    elif event.key == pygame.K_BACKSPACE: state = GameState.DIFFICULTY_SELECT
                    elif event.key == pygame.K_ESCAPE: running = False
                elif state == GameState.PLAYING and session:
                    if event.key == pygame.K_SPACE:
                        rad = math.radians(needle_angle)
                        tip_x = NEEDLE_BASE[0] + math.cos(rad) * NEEDLE_LENGTH
                        tip_y = NEEDLE_BASE[1] - math.sin(rad) * NEEDLE_LENGTH
                        session.arrows.append(FiredArrow(tip_x, tip_y, rad))
                        session.stat_fired += 1
                        if 'fire' in sounds: sounds['fire'].play()
                    elif event.key == pygame.K_ESCAPE: state = GameState.MENU
                elif state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        session = GameSession(DURATIONS[selected_dur_idx], difficulty)
                        state = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE: state = GameState.MENU
        for c in clouds: c.update(); c.draw(screen)
        if state == GameState.DIFFICULTY_SELECT:
            draw_text_centered(screen, "CHOOSE SKILL LEVEL", font_large, COLOR_WHITE, 150)
            for i, d in enumerate([Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD]):
                draw_text_centered(screen, f"{i+1}: {d.label}", font_medium, d.color, 300 + i*60)
        elif state == GameState.MENU:
            draw_text_centered(screen, "2D BALLOON POPPING GAME ", font_large, COLOR_YELLOW, 100)
            draw_text_centered(screen, f"Difficulty: {difficulty.label}", font_small, difficulty.color, 200)
            for i, d in enumerate(DURATIONS):
                color = COLOR_ORANGE if i == selected_dur_idx else COLOR_WHITE
                text = f"> {d}s Mode <" if i == selected_dur_idx else f"{d}s Mode"
                draw_text_centered(screen, text, font_medium, color, 280 + i * 50)
            hs_list = high_scores.get(str(DURATIONS[selected_dur_idx]), [0])
            draw_text_centered(screen, "TOP RECORDS:", font_small, COLOR_GREEN, 480)
            for i, h in enumerate(hs_list): draw_text_centered(screen, f"{i+1}. {h}", font_small, COLOR_WHITE, 510 + i * 30)
            draw_text_centered(screen, "SPACE to Enter Session | BACKSPACE for Difficulty", font_small, COLOR_WHITE, 650)
        elif state == GameState.PLAYING and session:
            s: GameSession = cast(GameSession, session)
            s.frames_count += 1
            now = pygame.time.get_ticks()
            time_passed = (now - s.start_ticks) / 1000.0
            time_left = max(0.0, float(s.duration + s.bonus_time) - time_passed)
            if time_left <= 0:
                state = GameState.GAME_OVER; save_high_score(s.duration, s.score)
                high_scores = load_high_scores(); continue
            is_double, is_slow = now < s.double_points_end, now < s.slow_mo_end
            diff_mult = min(2.5, (1.0 + (s.score // 10) * 0.1) * s.difficulty.w_mult)
            needle_speed = NEEDLE_ROT_SPEED_BASE * (0.6 if is_slow else 1.0)
            needle_angle += needle_speed * needle_dir
            if needle_angle >= 90 or needle_angle <= 0: needle_dir *= -1
            rad = math.radians(needle_angle)
            tip_pos = rotation(float(NEEDLE_BASE[0] + NEEDLE_LENGTH), float(NEEDLE_BASE[1]), float(NEEDLE_BASE[0]), float(NEEDLE_BASE[1]), -rad)
            tx, ty = float(tip_pos[0][0]), float(tip_pos[1][0])
            pred_end_x = tx + math.cos(rad) * 400
            pred_end_y = ty - math.sin(rad) * 400
            for i, p in enumerate(bresenham(int(tx), int(ty), int(pred_end_x), int(pred_end_y))):
                if i % 20 < 10: screen.set_at(p, (60, 80, 100))
            filled_ellipse(screen, int(tx), int(ty), 6, 6, COLOR_CYAN if is_slow else COLOR_WHITE)
            for p in bresenham(NEEDLE_BASE[0], NEEDLE_BASE[1], int(tx), int(ty)): screen.set_at(p, COLOR_WHITE)
            current_wind = WIND_AMPLITUDE_BASE * math.sin(WIND_FREQUENCY * s.frames_count) * diff_mult
            draw_wind_indicator(screen, current_wind)
            for b in s.balloons:
                b.update(s.frames_count, diff_mult, slow_mo=is_slow)
                if b.popped and b.pop_frame >= 10: b.reset()
                b.draw(screen)
            for arrow in cast(List[FiredArrow], s.arrows[:]):
                arrow.update()
                if not arrow.active: s.arrows.remove(arrow)
                else:
                    arrow.draw(screen)
                    # Check Balloon Collisions
                    for b in s.balloons:
                        if not b.popped and b.check_collision(arrow.x1, arrow.y1):
                            b.popped, s.score, s.stat_hit = True, s.score + (b.type.points * (2 if is_double else 1)), s.stat_hit + 1
                            if b.type == BalloonType.SMALL_FAST: s.stat_small += 1
                            else: s.stat_large += 1
                            if 'pop' in sounds: sounds['pop'].play()
                            for _ in range(8): s.particles.append(Particle(b.x, b.y, b.color))
                            if random.random() < 0.15: s.powerups.append(PowerUp())
                            arrow.active = False; break
                    
                    if not arrow.active: continue # Arrow hit a balloon

                    # Check Power-up Collisions
                    for pu in cast(List[PowerUp], s.powerups[:]):
                        if pu.active and ((arrow.x1 - pu.x)**2 / pu.rx**2) + (arrow.y1 - pu.y)**2 / pu.ry**2 <= 1.2:
                            if pu.type == PowerUpType.BONUS_TIME: s.bonus_time += pu.type.power_val
                            elif pu.type == PowerUpType.DOUBLE_POINTS: s.double_points_end = now + 8000
                            elif pu.type == PowerUpType.SLOW_MO: s.slow_mo_end = now + 5000
                            pu.active = False
                            arrow.active = False
                            if 'pop' in sounds: sounds['pop'].play()
                            for _ in range(5): s.particles.append(Particle(pu.x, pu.y, pu.type.color))
                            break

            for pu in cast(List[PowerUp], s.powerups[:]):
                pu.update(1/float(FPS))
                if not pu.active: s.powerups.remove(pu)
                else: pu.draw(screen, font_small)
            for p in cast(List[Particle], s.particles[:]):
                p.update()
                if p.life <= 0: s.particles.remove(p)
                else: p.draw(screen)
            draw_text_outlined(screen, f"TIME: {time_left:.1f}s", font_medium, COLOR_RED if time_left < 10 else COLOR_WHITE, (20, 20))
            draw_text_outlined(screen, f"SCORE: {s.score}", font_medium, COLOR_WHITE, (WIDTH-220, 20))
            draw_text_outlined(screen, f"SPD: {diff_mult:.1f}x", font_tiny, COLOR_ORANGE, (WIDTH-220, 60))
            draw_text_outlined(screen, f"GRAV: {GRAVITY_BASE*diff_mult:.2f}", font_tiny, COLOR_PURPLE, (WIDTH-220, 85))
            if is_double: draw_text_outlined(screen, "2X POINTS ACTIVE!", font_tiny, COLOR_YELLOW, (WIDTH-220, 110))
            if is_slow: draw_text_outlined(screen, "SLOW-MO ACTIVE!", font_tiny, COLOR_CYAN, (WIDTH-220, 135))
        elif state == GameState.GAME_OVER and session:
            s = cast(GameSession, session)
            draw_text_centered(screen, "GAME OVER", font_large, COLOR_RED, 100)
            draw_text_centered(screen, f"Point Total: {s.score}", font_medium, COLOR_WHITE, 200)
            acc = (s.stat_hit / s.stat_fired * 100) if s.stat_fired > 0 else 0
            draw_text_centered(screen, f"Accuracy: {acc:.1f}%", font_small, COLOR_CYAN, 280)
            draw_text_centered(screen, f"Small Pops: {s.stat_small}", font_small, COLOR_RED, 320)
            draw_text_centered(screen, f"Large Pops: {s.stat_large}", font_small, COLOR_BLUE, 360)
            cur_dur = s.duration; hs_list = high_scores.get(str(cur_dur), [0])
            is_new = s.score >= hs_list[0]
            hs_text = "NEW HIGH SCORE!" if is_new else f"Best Score: {hs_list[0]}"
            hs_color = (abs(int(math.sin(time.time()*12)*100)) + 155, 255, 155) if is_new else COLOR_GREEN
            draw_text_centered(screen, hs_text, font_medium, hs_color, 420)
            draw_text_centered(screen, "SPACE to Replay | ESC for Main Menu", font_small, COLOR_WHITE, 550)
        pygame.display.flip(); clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__": main()