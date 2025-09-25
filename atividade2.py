import sys
if sys.platform == "emscripten":
    import pygbag.aio as asyncio
else:
    import asyncio

import pygame as pg
import random
import math

WIDTH, HEIGHT = 900, 600
FPS = 60

pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("AirStay Dash — Advergame não oficial do Airbnb")
clock = pg.time.Clock()

FONT = pg.font.Font(None, 32)
BIG = pg.font.Font(None, 64)
SMALL = pg.font.Font(None, 24)

WHITE = (255, 255, 255)
BLACK = (25, 25, 28)
BG = (30, 30, 36)
RAUSCH = (255, 90, 95)
TEAL = (0, 166, 153)
SAND = (245, 232, 220)
GOLD = (255, 215, 0)
GRAY = (110, 115, 120)
GREEN = (60, 200, 120)
RED = (220, 70, 80)

STATE_MENU = 0
STATE_PLAY = 1
STATE_OVER = 2
STATE_BRAND = 3

state = STATE_MENU

player_w, player_h = 60, 24
player_x = WIDTH // 2
player_y = HEIGHT - 80
player_speed = 420

lives = 3
score = 0
mult = 1
time_left = 60.0

fall_min = 180
fall_max = 320
spawn_cd = 0.0

particles = []

banner_idx = 0
banner_time = 0.0
banners = [
    "Viaje como um local — encontre estadias únicas.",
    "Experiências ao seu estilo, em qualquer lugar.",
    "Reserve com tranquilidade e viva memórias incríveis.",
    "Hospedagens para todos os momentos da sua jornada.",
]

def draw_banner(dt):
    global banner_idx, banner_time
    banner_time += dt
    if banner_time > 6:
        banner_time = 0
        banner_idx = (banner_idx + 1) % len(banners)
    pg.draw.rect(screen, RAUSCH, (0, 0, WIDTH, 40))
    t = SMALL.render(banners[banner_idx], True, WHITE)
    screen.blit(t, (20, 10))

def spawn_particle(x, y, color):
    for _ in range(8):
        vx = random.uniform(-1.5, 1.5)
        vy = random.uniform(-2.0, -0.2)
        r = random.randint(2, 4)
        life = random.uniform(0.5, 1.2)
        particles.append([x, y, vx, vy, r, life, color])

def update_particles(dt):
    for p in particles[:]:
        p[0] += p[2] * 60 * dt
        p[1] += p[3] * 60 * dt
        p[5] -= dt
        if p[5] <= 0:
            particles.remove(p)
        else:
            pg.draw.circle(screen, p[6], (int(p[0]), int(p[1])), p[4])

class House:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed
        self.w = 40
        self.h = 30
        self.value = 10
    def update(self, dt):
        self.y += self.speed * dt
    def draw(self):
        body = pg.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)
        roof = [(body.centerx - self.w//2, body.top),
                (body.centerx, body.top - self.h//1.3),
                (body.centerx + self.w//2, body.top)]
        pg.draw.rect(screen, RAUSCH, body, border_radius=6)
        pg.draw.polygon(screen, RAUSCH, roof)
        pg.draw.rect(screen, WHITE, body, 2, border_radius=6)
    def rect(self):
        return pg.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

class Star:
    def __init__(self, x, y, speed):
        self.x, self.y = x, y
        self.speed = speed
        self.R = 22
        self.r = 10
        self.value = 15
    def update(self, dt):
        self.y += self.speed * dt
    def draw(self):
        pts = []
        for i in range(10):
            ang = math.pi/2 + i * math.pi/5
            rad = self.R if i % 2 == 0 else self.r
            pts.append((self.x + math.cos(ang)*rad, self.y - math.sin(ang)*rad))
        pg.draw.polygon(screen, GOLD, pts)
        pg.draw.polygon(screen, WHITE, pts, 2)
    def rect(self):
        return pg.Rect(int(self.x - self.R), int(self.y - self.R), int(self.R*2), int(self.R*2))

class BlockX:
    def __init__(self, x, y, speed):
        self.x, self.y = x, y
        self.speed = speed
        self.size = 40
    def update(self, dt):
        self.y += self.speed * dt
    def draw(self):
        r = pg.Rect(int(self.x - self.size/2), int(self.y - self.size/2), self.size, self.size)
        pg.draw.rect(screen, BLACK, r, border_radius=6)
        pg.draw.line(screen, RED, (r.left+6, r.top+6), (r.right-6, r.bottom-6), 6)
        pg.draw.line(screen, RED, (r.left+6, r.bottom-6), (r.right-6, r.top+6), 6)
        pg.draw.rect(screen, WHITE, r, 2, border_radius=6)
    def rect(self):
        return pg.Rect(int(self.x - self.size/2), int(self.y - self.size/2), self.size, self.size)

items = []

def spawn_item():
    x = random.randint(60, WIDTH-60)
    y = -40
    speed = random.uniform(fall_min, fall_max)  # antes: randint(...)
    t = random.random()
    if t < 0.5:
        items.append(House(x, y, speed))
    elif t < 0.8:
        items.append(Star(x, y, speed))
    else:
        items.append(BlockX(x, y, speed))


def reset_game():
    global player_x, lives, score, mult, time_left, items, spawn_cd, fall_min, fall_max, banner_idx, banner_time
    player_x = WIDTH // 2
    lives = 3
    score = 0
    mult = 1
    time_left = 60.0
    items = []
    spawn_cd = 0.0
    fall_min, fall_max = 180, 320
    banner_idx = 0
    banner_time = 0.0

def draw_player():
    base = pg.Rect(int(player_x - player_w/2), player_y, player_w, player_h)
    wheel_l = (base.left + 10, base.bottom + 8)
    wheel_r = (base.right - 10, base.bottom + 8)
    pg.draw.rect(screen, TEAL, base, border_radius=8)
    pg.draw.circle(screen, WHITE, wheel_l, 6)
    pg.draw.circle(screen, WHITE, wheel_r, 6)
    pg.draw.rect(screen, WHITE, base, 2, border_radius=8)

def draw_hud():
    hud = pg.Rect(0, HEIGHT-60, WIDTH, 60)
    pg.draw.rect(screen, (38, 38, 44), hud)
    s = FONT.render(f"Pontos: {score}", True, WHITE)
    m = FONT.render(f"Multiplicador: x{mult}", True, WHITE)
    t = FONT.render(f"Tempo: {int(time_left)}s", True, WHITE)
    l = FONT.render(f"Vidas: {lives}", True, WHITE)
    screen.blit(s, (20, HEIGHT-44))
    screen.blit(m, (220, HEIGHT-44))
    screen.blit(t, (520, HEIGHT-44))
    screen.blit(l, (720, HEIGHT-44))

def skyline():
    rng = random.Random(123)
    pg.draw.rect(screen, (26, 26, 32), (0, 40, WIDTH, HEIGHT-100))
    x = 0
    while x < WIDTH:
        w = rng.randint(40, 90)
        h = rng.randint(80, 180)
        pg.draw.rect(screen, (36, 36, 48), (x, HEIGHT-100-h, w, h))
        x += w + rng.randint(8, 20)


def menu_screen():
    screen.fill(BG)
    skyline()
    pg.draw.rect(screen, RAUSCH, (WIDTH//2-220, 120, 440, 120), border_radius=16)
    title = BIG.render("Airbnb", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
    sub = SMALL.render("Advergame não oficial inspirado no Airbnb", True, WHITE)
    screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 220))
    play_btn = pg.Rect(WIDTH//2-140, 300, 280, 52)
    pg.draw.rect(screen, TEAL, play_btn, border_radius=12)
    pg.draw.rect(screen, WHITE, play_btn, 2, border_radius=12)
    screen.blit(FONT.render("Jogar agora", True, WHITE), (play_btn.centerx-70, play_btn.centery-14))
    info = SMALL.render("← → para mover • Colete Casas e Estrelas • Evite o X • 60s", True, WHITE)
    screen.blit(info, (WIDTH//2 - info.get_width()//2, 380))
    return play_btn

def over_screen():
    screen.fill(BG)
    skyline()
    t = BIG.render("Fim de Jogo", True, WHITE)
    screen.blit(t, (WIDTH//2 - t.get_width()//2, 120))
    s = FONT.render(f"Pontuação final: {score}", True, WHITE)
    screen.blit(s, (WIDTH//2 - s.get_width()//2, 200))
    msg = SMALL.render("Dica: combos aumentam muito seus pontos!", True, GRAY)
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 240))
    again = pg.Rect(WIDTH//2-160, 310, 320, 50)
    brand = pg.Rect(WIDTH//2-160, 380, 320, 50)
    pg.draw.rect(screen, TEAL, again, border_radius=12)
    pg.draw.rect(screen, WHITE, again, 2, border_radius=12)
    pg.draw.rect(screen, RAUSCH, brand, border_radius=12)
    pg.draw.rect(screen, WHITE, brand, 2, border_radius=12)
    screen.blit(FONT.render("Jogar de novo", True, WHITE), (again.centerx-88, again.centery-14))
    screen.blit(FONT.render("Conheça o Airbnb ▶", True, WHITE), (brand.centerx-120, brand.centery-14))
    return again, brand

def brand_screen():
    screen.fill(BG)
    pg.draw.rect(screen, RAUSCH, (0, 0, WIDTH, 70))
    tt = BIG.render("Airbnb", True, WHITE)
    screen.blit(tt, (20, 10))
    box = pg.Rect(80, 120, WIDTH-160, HEIGHT-220)
    pg.draw.rect(screen, SAND, box, border_radius=20)
    pg.draw.rect(screen, RAUSCH, box, 8, border_radius=20)
    lines = [
        "Encontre lugares memoráveis para ficar — do campo à cidade.",
        "Experiências selecionadas para você explorar cada destino.",
        "Viaje com mais flexibilidade e viva histórias únicas.",
        "Crie sua próxima viagem hoje mesmo."
    ]
    y = box.top + 40
    for ln in lines:
        screen.blit(FONT.render(ln, True, BLACK), (box.left + 24, y))
        y += 44
    cta = pg.Rect(WIDTH//2-150, box.bottom-80, 300, 50)
    pg.draw.rect(screen, TEAL, cta, border_radius=12)
    pg.draw.rect(screen, BLACK, cta, 2, border_radius=12)
    screen.blit(FONT.render("Explorar estadias", True, WHITE), (cta.centerx-100, cta.centery-14))
    note = SMALL.render("Este é um jogo promocional não oficial criado para fins educacionais.", True, GRAY)
    screen.blit(note, (WIDTH//2 - note.get_width()//2, HEIGHT-40))
    return cta

def frame(events, dt):
    global state, player_x, lives, score, mult, time_left, spawn_cd, fall_min, fall_max
    screen.fill(BG)
    if state == STATE_MENU:
        pb = menu_screen()
        mx, my = pg.mouse.get_pos()
        click = any(e.type == pg.MOUSEBUTTONDOWN and e.button == 1 for e in events)
        if click and pb.collidepoint(mx, my):
            reset_game()
            state = STATE_PLAY
    elif state == STATE_PLAY:
        draw_banner(dt)
        skyline()
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            player_x -= player_speed * dt
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            player_x += player_speed * dt
        player_x = max(40, min(WIDTH-40, player_x))
        spawn_cd -= dt
        if spawn_cd <= 0:
            spawn_item()
            spawn_cd = random.uniform(0.4, 0.9)
        for it in items[:]:
            it.update(dt)
            it.draw()
            if it.rect().colliderect(pg.Rect(int(player_x - player_w/2), player_y, player_w, player_h)):
                if isinstance(it, House):
                    score += it.value * mult
                    mult = min(10, mult + 1)
                    spawn_particle(it.x, it.y, RAUSCH)
                elif isinstance(it, Star):
                    score += it.value * mult
                    mult = min(12, mult + 2)
                    spawn_particle(it.x, it.y, GOLD)
                else:
                    lives -= 1
                    mult = 1
                    spawn_particle(it.x, it.y, RED)
                items.remove(it)
            elif it.y > HEIGHT + 60:
                items.remove(it)
        draw_player()
        time_left -= dt
        fall_min = min(360, fall_min + dt * 2)
        fall_max = min(520, fall_max + dt * 2.5)
        draw_hud()
        update_particles(dt)
        if lives <= 0 or time_left <= 0:
            state = STATE_OVER
    elif state == STATE_OVER:
        again, brand = over_screen()
        update_particles(dt)
        mx, my = pg.mouse.get_pos()
        clicked = any(e.type == pg.MOUSEBUTTONDOWN and e.button == 1 for e in events)
        if clicked and again.collidepoint(mx, my):
            reset_game()
            state = STATE_PLAY
        if clicked and brand.collidepoint(mx, my):
            state = STATE_BRAND
    elif state == STATE_BRAND:
        cta = brand_screen()
        update_particles(dt)
        mx, my = pg.mouse.get_pos()
        clicked = any(e.type == pg.MOUSEBUTTONDOWN and e.button == 1 for e in events)
        if clicked and cta.collidepoint(mx, my):
            pg.draw.circle(screen, TEAL, (cta.centerx, cta.centery), 10)
    pg.display.flip()

async def main_async():
    reset_game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        events = pg.event.get()
        for e in events:
            if e.type == pg.QUIT:
                running = False
        frame(events, dt)
        await asyncio.sleep(0)

def main_sync():
    reset_game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        events = pg.event.get()
        for e in events:
            if e.type == pg.QUIT:
                running = False
        frame(events, dt)

if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.run(main_async())
    else:
        main_sync()
