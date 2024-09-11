import pygame
import math
import random

pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Drag to create fading ripples")

BLACK = (0, 0, 0)
WHITE = (100, 100, 100)

# 背景画像の読み込み
background = pygame.image.load("AdobeStock_Cave.jpeg").convert_alpha()

class Ripple:
    # (クラスの内容は前述のものと同じ)
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = 100
        self.speed = 1.5
        self.alpha = 255
        self.amplitude = 1.0
        self.phase = 0
        self.wave_amplitude = 10  # 波の振幅
        self.wave_speed = 0.1     # 波の速度

    def update(self):
        self.radius += self.speed
        # 半径が最大値の半分を超えたら、フェードアウトを開始
        if self.radius > self.max_radius / 2:
            self.alpha = max(0, self.alpha - 10)
            self.amplitude = max(0.0, self.amplitude - 0.01)
        self.phase += self.wave_speed

        return self.alpha > 0

    def draw(self, surface):
        if self.alpha > 0:
            # 同心円を描画する
            for r in range(int(self.radius), 0, -10):
                # 水面の揺れを表現するためにランダムな変位を加える
                x_offset = int(math.sin(self.phase + r / 10) * self.wave_amplitude)
                y_offset = int(math.cos(self.phase + r / 10) * self.wave_amplitude)
                pygame.draw.circle(surface, (*WHITE, int(self.alpha * (1 - r / self.radius) * self.amplitude)), (int(self.x + x_offset), int(self.y + y_offset)), r, 2)

# ripples リストを初期化
ripples = []
dragging = False
last_pos = None
min_distance = 20

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # (イベント処理は前述のものと同じ)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            dragging = True
            x, y = pygame.mouse.get_pos()
            ripples.append(Ripple(x, y))
            last_pos = (x, y)
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            last_pos = None
    
    if dragging:
        x, y = pygame.mouse.get_pos()
        if last_pos:
            distance = math.sqrt((x - last_pos[0])**2 + (y - last_pos[1])**2)
            if distance >= min_distance:
                ripples.append(Ripple(x, y))
                last_pos = (x, y)

    # 背景画像の描画
    screen.blit(background, (0, 0))

    ripples = [ripple for ripple in ripples if ripple.update()]
    for ripple in ripples:
        ripple.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()