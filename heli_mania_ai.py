import random
import sys
import pygame
from pygame.locals import *

class Obstacle:

    def __init__(self, x, y, rect):
        self.x = x
        self.y = y
        self.scored = False
        self.speed = 10
        self.frame = 0
        self.frame_limit = 23
        self.rect = rect

class Enemy:

    def __init__(self, x, y, rect):
        self.x = x
        self.y = y
        self.scored = False
        self.speed = 10
        self.frame = 0
        self.frame_limit = 4
        self.health = 2
        self.rect = rect

class Heli:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        self.frame_limit = 4
        self.speed = 5
        self.rect = None

class HeliMania:

    def __init__(self, width = 1200, height = 600):
        self.width = width
        self.height = height

        # init display
        self.display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Heli Mania')
        self.clock = pygame.time.Clock()
        
        # init surfaces
        self.bg = pygame.image.load('assets/bg.png').convert()
        self.heli_frames = []
        self.obstacle_frames = []
        self.enemy_frames = []
        self.x_axis = []
        self.y_axis = [30, 80, 160, 320, 480]
        self._load_x_axis()
        self._load_heli_frames()
        self._load_obstacle_frames()
        self._load_enemy_frames()

        # init game state
        self.reset()

    def reset(self):
        self.score = 0
        self.game_over = False
        self.up = False
        self.down = False
        self.obstacle_num = 10
        self.enemy_num = 5
        self.enemies = []
        self.obstacles = []
        self.heli = Heli(self.width / 6., self.height / 2.)

        for i in range(self.obstacle_num):
            self._create_obstacle()

        for i in range(self.enemy_num):
            self._create_enemy()

        self.heli.rect = self.heli_frames[self.heli.frame].get_rect(topleft = (self.heli.x, self.heli.y)) 

    def play_step(self, action):

        # check if elements are outside screen
        self._remove_obstacles_out_of_frame()
        self._remove_enemies_out_of_frame()
        
        reward = self._add_score()

        while len(self.obstacles) < self.obstacle_num:
            self._create_obstacle()

        while len(self.enemies) < self.enemy_num:
            self._create_enemy()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Uncomment to play manually
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_w:
            #         self.up = True

            #     if event.key == pygame.K_s:
            #         self.down = True

            # if event.type == pygame.KEYUP:
            #     if event.key == pygame.K_w:
            #         self.up = False

            #     if event.key == pygame.K_s:
            #         self.down = False
        
        # Comment these two lines to play manually
        self.up = action[0]
        self.down = action[1]

        # obstacle update
        for obstacle in self.obstacles:
            obstacle.x -= obstacle.speed
            obstacle.rect = self.obstacle_frames[obstacle.frame].get_rect(topleft = (obstacle.x, obstacle.y))

        # enemy update
        for enemy in self.enemies:
            enemy.x -= enemy.speed
            enemy.rect = self.enemy_frames[enemy.frame].get_rect(topleft = (enemy.x, enemy.y))

        # heli update
        if self.up:
            self.heli.y -= self.heli.speed

        if self.down:
            self.heli.y += self.heli.speed

        self.heli.rect = self.heli_frames[self.heli.frame].get_rect(topleft = (self.heli.x, self.heli.y))

        self.game_over = self._check_game_over(self.heli)

        self._update_ui()

        if self.game_over:
            reward = -100

        return reward, self.game_over, self.score

    def _update_ui(self):

        # draw background
        self.display.blit(self.bg, (0,0))
        
        # draw heli
        self.display.blit(self.heli_frames[self.heli.frame], self.heli.rect)

        self.heli.frame += 1
        if self.heli.frame == self.heli.frame_limit:
            self.heli.frame = 0

        # draw obstacles
        for obstacle in self.obstacles:
            self.display.blit(self.obstacle_frames[obstacle.frame], obstacle.rect)
            obstacle.frame += 1
            if obstacle.frame == obstacle.frame_limit:
                obstacle.frame = 0

        # draw enemies
        for enemy in self.enemies:
            self.display.blit(self.enemy_frames[enemy.frame], enemy.rect)
            enemy.frame += 1
            if enemy.frame == enemy.frame_limit:
                enemy.frame = 0

        pygame.display.update()
        self.clock.tick(60)

    def _load_x_axis(self):
        val = self.width + 100
        for i in range(50):
            self.x_axis.append(val)
            val += 130

    def _load_heli_frames(self):
        for i in range(5):
            self.heli_frames.append(pygame.image.load(f'assets/heli/frame{(i + 1)}.png').convert_alpha())
    
    def _load_obstacle_frames(self):
        for i in range(24):
            self.obstacle_frames.append(pygame.transform.flip(pygame.image.load(f'assets/obstacle/bomb{i + 1}.png').convert_alpha(), True, False))

    def _load_enemy_frames(self):
        for i in range(5):
            self.enemy_frames.append(pygame.image.load(f'assets/enemy/enemy{i + 1}.png').convert_alpha())

    def _remove_obstacles_out_of_frame(self):
        remove = []
        for obstacle in self.obstacles:
            if obstacle.x < 0:
                remove.append(obstacle)
        for obstacle in remove:
            self.obstacles.remove(obstacle)

    def _remove_enemies_out_of_frame(self):
        remove = []
        for enemy in self.enemies:
            if enemy.x < 0:
                remove.append(enemy)
        for enemy in remove:
            self.enemies.remove(enemy)

    def _check_obstacle_enemy_collision(self, rect):
        for obstacle in self.obstacles:
            if rect.colliderect(obstacle):
                return True

        for enemy in self.enemies:
            if rect.colliderect(enemy):
                return True

        return False

    def _create_obstacle(self):
        obstacle = None
        while True:
            x, y = random.choice(self.x_axis), random.choice(self.y_axis)

            obstacle = Obstacle(x, y, self.obstacle_frames[0].get_rect(topleft = (x, y)))
            if self._check_obstacle_enemy_collision(obstacle.rect) == False:
                break

        self.obstacles.append(obstacle)

    def _create_enemy(self):
        enemy = None
        while True:
            x, y = random.choice(self.x_axis), random.choice(self.y_axis)

            enemy = Enemy(x, y, self.enemy_frames[0].get_rect(topleft = (x, y)))
            if self._check_obstacle_enemy_collision(enemy.rect) == False:
                break

        self.enemies.append(enemy)

    def _add_score(self):
        reward = 0
        for obstacle in self.obstacles:
            if not obstacle.scored and obstacle.x < self.heli.x:
                obstacle.scored = True
                self.score += 10
                reward += 10

        for enemy in self.enemies:
            if not enemy.scored and enemy.x < self.heli.x:
                enemy.scored = True 
                self.score += 10
                reward += 10

        reward += 5
        self.score += 5
        return reward

    def _check_game_over(self, heli):
        if heli.y <= 0:
            return True

        if heli.y > self.height:
            return True

        if self._check_obstacle_enemy_collision(heli.rect):
            return True

        return False


if __name__ == '__main__':
    game = HeliMania()

    action = [0,0,0]
    while True:
        reward, game_over, score = game.play_step(action)

        if game_over:
            break

    print(f'Final score = {score}')

    pygame.quit()

