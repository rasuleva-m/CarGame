import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()

# Size of the window screen
WIDTH = 600
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🏎️ Strategic Racing Championship")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
DARK_GRAY = (30, 30, 30)
RED = (255, 50, 50)
GREEN = (50, 255, 100)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 150, 50)
PURPLE = (200, 50, 255)
NEON_GREEN = (57, 255, 20)
NEON_BLUE = (4, 217, 255)
NEON_RED = (255, 20, 147)
ROAD_COLOR = (60, 60, 60)
ROAD_LINE = (255, 255, 150)

# FPS
clock = pygame.time.Clock()
FPS = 60

# Car dimensions
CAR_WIDTH = 45
CAR_HEIGHT = 90

# Player Car
player_car = pygame.Rect(WIDTH // 2 - CAR_WIDTH // 2, HEIGHT - CAR_HEIGHT - 30,
                         CAR_WIDTH, CAR_HEIGHT)

# Game variables
enemy_cars = []
base_enemy_speed = 4
spawn_timer = 0
score = 0
player_speed = 0
max_player_speed = 8
acceleration = 0.3
deceleration = 0.5
brake_force = 1.2
road_offset = 0
particles = []
brake_particles = []

# Lane positions
ROAD_LEFT = WIDTH // 2 - 140
ROAD_RIGHT = WIDTH // 2 + 140 - CAR_WIDTH
LANE_WIDTH = (ROAD_RIGHT - ROAD_LEFT) // 3
LANES = [ROAD_LEFT + i * LANE_WIDTH for i in range(3)]

# Fonts
title_font = pygame.font.Font(None, 48)
score_font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
tiny_font = pygame.font.Font(None, 18)


class Particle:
    def __init__(self, x, y, color, velocity=(0, 0), life=30):
        self.x = x
        self.y = y
        self.vx = velocity[0] + random.uniform(-1, 1)
        self.vy = velocity[1] + random.uniform(1, 3)
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        # Add some air resistance
        self.vx *= 0.98
        self.vy *= 0.98

    def draw(self, surface):
        if self.life > 0:
            alpha = self.life / self.max_life
            size = max(1, int(4 * alpha))
            color = tuple(int(c * alpha) for c in self.color[:3])
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


class EnemyCar:
    def __init__(self, x, y, colors, ai_type="normal"):
        self.rect = pygame.Rect(x, y, CAR_WIDTH, CAR_HEIGHT)
        self.colors = colors
        self.target_lane = x
        self.speed = base_enemy_speed + random.uniform(-1, 2)
        self.ai_type = ai_type
        self.lane_change_timer = 0
        self.aggressive_timer = 0

    def update(self, player_pos):
        # AI Strategic Movement
        if self.ai_type == "aggressive":
            self.aggressive_behavior(player_pos)
        elif self.ai_type == "defensive":
            self.defensive_behavior(player_pos)
        elif self.ai_type == "smart":
            self.smart_behavior(player_pos)
        else:
            self.normal_behavior()

        # Smooth lane changing
        if abs(self.rect.x - self.target_lane) > 2:
            if self.rect.x < self.target_lane:
                self.rect.x += min(3, self.target_lane - self.rect.x)
            else:
                self.rect.x -= min(3, self.rect.x - self.target_lane)

        # Move forward
        self.rect.y += self.speed
        self.lane_change_timer += 1
        self.aggressive_timer += 1

    def aggressive_behavior(self, player_pos):
        # Try to block player's path
        if self.aggressive_timer > 20 and abs(self.rect.y - player_pos[1]) < 200:
            closest_lane = min(LANES, key=lambda lane: abs(lane - player_pos[0]))
            if random.random() < 0.3:
                self.target_lane = closest_lane
                self.aggressive_timer = 0

    def defensive_behavior(self, player_pos):
        # Try to avoid player
        if abs(self.rect.y - player_pos[1]) < 150:
            current_lane_idx = min(range(len(LANES)), key=lambda i: abs(LANES[i] - self.rect.x))
            # Move away from player
            if player_pos[0] < self.rect.x and current_lane_idx < len(LANES) - 1:
                self.target_lane = LANES[current_lane_idx + 1]
            elif player_pos[0] > self.rect.x and current_lane_idx > 0:
                self.target_lane = LANES[current_lane_idx - 1]

    def smart_behavior(self, player_pos):
        # Combination of avoiding other cars and strategic positioning
        if self.lane_change_timer > 60:
            # Check for nearby cars and choose best lane
            best_lane = self.choose_best_lane()
            self.target_lane = best_lane
            self.lane_change_timer = 0

    def defensive_behavior(self, player_pos):
        # Try to avoid player
        if abs(self.rect.y - player_pos[1]) < 150:
            current_lane_idx = min(range(len(LANES)), key=lambda i: abs(LANES[i] - self.rect.x))
            # Move away from player
            if player_pos[0] < self.rect.x and current_lane_idx < len(LANES) - 1:
                self.target_lane = LANES[current_lane_idx + 1]
            elif player_pos[0] > self.rect.x and current_lane_idx > 0:
                self.target_lane = LANES[current_lane_idx - 1]

    def normal_behavior(self):
        # Random lane changes occasionally
        if self.lane_change_timer > 120 and random.random() < 0.1:
            self.target_lane = random.choice(LANES)
            self.lane_change_timer = 0

    def choose_best_lane(self):
        # Simple AI to choose lane with least traffic ahead
        lane_scores = [0, 0, 0]
        for i, lane in enumerate(LANES):
            # Check for cars in this lane ahead
            cars_ahead = sum(1 for car in enemy_cars
                             if abs(car.rect.x - lane) < 30 and
                             car.rect.y < self.rect.y and
                             car.rect.y > self.rect.y - 200)
            lane_scores[i] = -cars_ahead  # Prefer lanes with fewer cars

        best_lane_idx = lane_scores.index(max(lane_scores))
        return LANES[best_lane_idx]


def draw_car(surface, rect, color1, color2, is_player=False, ai_type=None):
    # Main body with AI type indicator
    if ai_type == "aggressive":
        pygame.draw.rect(surface, NEON_RED, rect, 2, border_radius=10)
    elif ai_type == "smart":
        pygame.draw.rect(surface, PURPLE, rect, 2, border_radius=10)

    pygame.draw.rect(surface, color1, rect, border_radius=10)

    # Car details
    # Windshield
    windshield = pygame.Rect(rect.x + 5, rect.y + 10, rect.width - 10, 15)
    pygame.draw.rect(surface, BLUE, windshield, border_radius=5)

    # Side windows
    left_window = pygame.Rect(rect.x + 5, rect.y + 30, 8, 20)
    right_window = pygame.Rect(rect.x + rect.width - 13, rect.y + 30, 8, 20)
    pygame.draw.rect(surface, BLUE, left_window, border_radius=3)
    pygame.draw.rect(surface, BLUE, right_window, border_radius=3)

    # Wheels
    wheel_color = BLACK
    wheel_rim = color2

    # Front wheels
    front_left = pygame.Rect(rect.x - 3, rect.y + 5, 8, 15)
    front_right = pygame.Rect(rect.x + rect.width - 5, rect.y + 5, 8, 15)
    pygame.draw.rect(surface, wheel_color, front_left, border_radius=4)
    pygame.draw.rect(surface, wheel_color, front_right, border_radius=4)
    pygame.draw.rect(surface, wheel_rim, front_left, 2, border_radius=4)
    pygame.draw.rect(surface, wheel_rim, front_right, 2, border_radius=4)

    # Back wheels
    back_left = pygame.Rect(rect.x - 3, rect.y + rect.height - 20, 8, 15)
    back_right = pygame.Rect(rect.x + rect.width - 5, rect.y + rect.height - 20, 8, 15)
    pygame.draw.rect(surface, wheel_color, back_left, border_radius=4)
    pygame.draw.rect(surface, wheel_color, back_right, border_radius=4)
    pygame.draw.rect(surface, wheel_rim, back_left, 2, border_radius=4)
    pygame.draw.rect(surface, wheel_rim, back_right, 2, border_radius=4)

    if is_player:
        # Headlights
        pygame.draw.circle(surface, YELLOW, (rect.x + 10, rect.y + 3), 4)
        pygame.draw.circle(surface, YELLOW, (rect.x + rect.width - 10, rect.y + 3), 4)

        # Racing stripes
        stripe_rect = pygame.Rect(rect.x + rect.width // 2 - 2, rect.y, 4, rect.height)
        pygame.draw.rect(surface, WHITE, stripe_rect)

        # Exhaust particles
        if player_speed > 2 and random.random() < 0.7:
            particles.append(Particle(
                rect.x + rect.width // 2 + random.randint(-5, 5),
                rect.y + rect.height + 5,
                (100, 100, 255),
                (0, player_speed)
            ))

    # Car outline for premium look
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=10)


def draw_road():
    global road_offset

    # Road background
    road_rect = pygame.Rect(WIDTH // 2 - 150, 0, 300, HEIGHT)
    pygame.draw.rect(screen, ROAD_COLOR, road_rect)

    # Lane dividers
    for i in range(1, 3):
        lane_x = ROAD_LEFT + i * LANE_WIDTH
        for y in range(0, HEIGHT, 60):
            y_pos = y + (road_offset % 60)
            pygame.draw.rect(screen, WHITE, (lane_x - 2, y_pos, 4, 30), border_radius=2)

    # Road borders with neon glow
    for i in range(3):
        border_color = (*NEON_BLUE, 255 - i * 80)
        pygame.draw.line(screen, NEON_BLUE,
                         (WIDTH // 2 - 150 - i, 0),
                         (WIDTH // 2 - 150 - i, HEIGHT), 3 - i)
        pygame.draw.line(screen, NEON_BLUE,
                         (WIDTH // 2 + 150 + i, 0),
                         (WIDTH // 2 + 150 + i, HEIGHT), 3 - i)

    # Animated road lines
    road_offset += player_speed + base_enemy_speed


def draw_background():
    # Gradient background
    for y in range(HEIGHT):
        color_ratio = y / HEIGHT
        r = int(20 * (1 - color_ratio) + 5 * color_ratio)
        g = int(25 * (1 - color_ratio) + 10 * color_ratio)
        b = int(50 * (1 - color_ratio) + 30 * color_ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Stars in background
    for i in range(50):
        x = (i * 137) % WIDTH
        y = (i * 211) % HEIGHT
        if random.random() < 0.1:
            pygame.draw.circle(screen, WHITE, (x, y), 1)


def draw_ui():
    # Score with glow effect
    score_text = score_font.render(f"SCORE: {score}", True, NEON_GREEN)
    score_shadow = score_font.render(f"SCORE: {score}", True, BLACK)
    screen.blit(score_shadow, (22, 22))
    screen.blit(score_text, (20, 20))

    # Speed indicator with color coding
    speed_color = GREEN if player_speed < 5 else ORANGE if player_speed < 7 else RED
    speed_text = small_font.render(f"SPEED: {int(player_speed)}", True, speed_color)
    screen.blit(speed_text, (20, 60))

    # Controls guide
    controls = [
        "↑/W: Tezlashtirish",
        "↓/S: Tormoz",
        "←→/AD: Boshqarish"
    ]

    for i, control in enumerate(controls):
        control_text = tiny_font.render(control, True, WHITE)
        screen.blit(control_text, (20, HEIGHT - 80 + i * 15))

    # AI car legend
    legend_y = 100
    ai_info = [
        ("Qizil: Aggressive", NEON_RED),
        ("Binafsha: Smart", PURPLE),
        ("Oddiy: Normal", WHITE)
    ]

    for info, color in ai_info:
        legend_text = tiny_font.render(info, True, color)
        screen.blit(legend_text, (20, legend_y))
        legend_y += 15

    # Game title
    title_text = title_font.render("STRATEGIC RACING", True, NEON_BLUE)
    title_shadow = title_font.render("STRATEGIC RACING", True, BLACK)
    screen.blit(title_shadow, (WIDTH - 302, 22))
    screen.blit(title_text, (WIDTH - 300, 20))


def create_enemy_car():
    colors = [
        (RED, YELLOW),
        (PURPLE, WHITE),
        (ORANGE, BLACK),
        (BLUE, RED),
        (GREEN, WHITE)
    ]

    # Choose AI type based on game progression
    ai_types = ["normal", "defensive", "aggressive", "smart"]
    weights = [0.4, 0.2, 0.2, 0.2]  # 40% normal, 20% each other type

    # Increase difficulty with score
    if score > 20:
        weights = [0.2, 0.2, 0.3, 0.3]  # More aggressive and smart cars

    ai_type = random.choices(ai_types, weights=weights)[0]

    spawn_lane = random.choice(LANES)
    color_pair = random.choice(colors)

    return EnemyCar(spawn_lane, -CAR_HEIGHT, color_pair, ai_type)


def game_over():
    # Create explosion particles
    for i in range(50):
        particles.append(Particle(
            player_car.centerx + random.randint(-30, 30),
            player_car.centery + random.randint(-30, 30),
            (255, random.randint(50, 255), 0),
            (random.uniform(-5, 5), random.uniform(-8, -2)),
            60
        ))

    # Game over screen
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(180)
    screen.blit(overlay, (0, 0))

    game_over_text = title_font.render("O'YIN TUGADI!", True, RED)
    final_score = score_font.render(f"Yakuniy ball: {score}", True, WHITE)
    restart_text = small_font.render("SPACE - Qayta boshlash, ESC - Chiqish", True, YELLOW)

    screen.blit(game_over_text, (WIDTH // 2 - 140, HEIGHT // 2 - 50))
    screen.blit(final_score, (WIDTH // 2 - 100, HEIGHT // 2))
    screen.blit(restart_text, (WIDTH // 2 - 180, HEIGHT // 2 + 50))

    pygame.display.update()

    # Wait for input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True  # Restart
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
    return False


def reset_game():
    global enemy_cars, score, base_enemy_speed, particles, brake_particles, player_speed
    enemy_cars = []
    score = 0
    base_enemy_speed = 4
    particles = []
    brake_particles = []
    player_speed = 0
    player_car.x = WIDTH // 2 - CAR_WIDTH // 2


# Main Game loop
running = True
is_braking = False

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Player Controls with realistic acceleration/deceleration
    keys = pygame.key.get_pressed()
    is_braking = False

    # Horizontal movement
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        if player_car.left > ROAD_LEFT:
            player_car.x -= 7
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        if player_car.right < ROAD_RIGHT + CAR_WIDTH:
            player_car.x += 7

    # Vertical movement and speed control
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        # Accelerate
        player_speed = min(player_speed + acceleration, max_player_speed)
    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
        # Brake
        is_braking = True
        player_speed = max(player_speed - brake_force, 0)

        # Add brake particles
        if player_speed > 1:
            for i in range(3):
                brake_particles.append(Particle(
                    player_car.x + random.randint(5, CAR_WIDTH - 5),
                    player_car.y + CAR_HEIGHT + 2,
                    (255, 200, 0),  # Orange/yellow brake sparks
                    (random.uniform(-2, 2), random.uniform(2, 5)),
                    20
                ))
    else:
        # Natural deceleration
        player_speed = max(player_speed - deceleration / 2, 0)

    # Enemy Cars Spawn
    spawn_timer += 1
    spawn_rate = max(30 - score // 5, 15)  # Faster spawning with higher score
    if spawn_timer > spawn_rate:
        enemy_cars.append(create_enemy_car())
        spawn_timer = 0

    # Enemy Cars Movement and AI
    current_enemy_speed = base_enemy_speed + (score // 15) * 0.5
    for car in enemy_cars[:]:
        car.speed = current_enemy_speed + random.uniform(-0.5, 0.5)
        car.update((player_car.x, player_car.y))

        if car.rect.top > HEIGHT:
            enemy_cars.remove(car)
            score += 1

    # Check Collision
    for car in enemy_cars:
        if player_car.colliderect(car.rect):
            if game_over():
                reset_game()
            break

    # Update particles
    for particle in particles[:]:
        particle.update()
        if particle.life <= 0:
            particles.remove(particle)

    for particle in brake_particles[:]:
        particle.update()
        if particle.life <= 0:
            brake_particles.remove(particle)

    # Drawing
    draw_background()
    draw_road()

    # Draw cars
    draw_car(screen, player_car, NEON_GREEN, WHITE, True)

    for car in enemy_cars:
        draw_car(screen, car.rect, car.colors[0], car.colors[1], False, car.ai_type)

    # Draw particles
    for particle in particles + brake_particles:
        particle.draw(screen)

    # Draw UI
    draw_ui()

    pygame.display.update()

pygame.quit()