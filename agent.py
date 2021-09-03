import torch
import random
from collections import deque
from heli_mania_ai import HeliMania
from model import LinearQNet, QTrainer
from helper import plot
import copy

MAX_MEMORY = 100000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0
        self.discount = 0.9
        self.memory = deque(maxlen = MAX_MEMORY)
        self.model = LinearQNet(4, 256, 3)
        self.trainer = QTrainer(self.model, lr = LR, discount = self.discount)

    def _check_game_over(self, game, heli, obstacles, enemies):
        if heli.y <= 0 or heli.y > game.height:
            return True

        for obstacle in obstacles:
            if heli.rect.colliderect(obstacle):
                return True

        for enemy in enemies:
            if heli.rect.colliderect(enemy):
                return True

        return False


    def get_state(self, game):
        lowest_go_up_game_over = 0
        lowest_go_down_game_over = 0
        danger = 0

        for obstacle in game.obstacles:
            if obstacle.x < game.heli.x - 30:
                continue

            if abs(obstacle.x - game.heli.x) <= 550 and abs(obstacle.y - game.heli.y) >= 300:
                danger = 1

        for enemy in game.enemies:
            if enemy.x < game.heli.x - 30:
                continue

            if abs(enemy.x - game.heli.x) <= 550 and abs(enemy.y - game.heli.y) >= 300:
                danger = 1


        heli = copy.deepcopy(game.heli)
        obstacles = copy.deepcopy(game.obstacles)
        enemies = copy.deepcopy(game.enemies)

        while True:

            if self._check_game_over(game, heli, obstacles, enemies):
                break
            
            for obstacle in obstacles:
                obstacle.x -= obstacle.speed
                obstacle.rect = game.obstacle_frames[obstacle.frame].get_rect(topleft = (obstacle.x, obstacle.y))

            for enemy in enemies:
                enemy.x -= enemy.speed
                enemy.rect = game.enemy_frames[enemy.frame].get_rect(topleft = (enemy.x, enemy.y))

            lowest_go_up_game_over += 1
            heli.y -= heli.speed
            heli.rect = game.heli_frames[heli.frame].get_rect(topleft = (heli.x, heli.y))

        heli = copy.deepcopy(game.heli)
        obstacles = copy.deepcopy(game.obstacles)
        enemies = copy.deepcopy(game.enemies)

        while True:

            if self._check_game_over(game, heli, obstacles, enemies):
                break
            
            for obstacle in obstacles:
                obstacle.x -= obstacle.speed
                obstacle.rect = game.obstacle_frames[obstacle.frame].get_rect(topleft = (obstacle.x, obstacle.y))

            for enemy in enemies:
                enemy.x -= enemy.speed
                enemy.rect = game.enemy_frames[enemy.frame].get_rect(topleft = (enemy.x, enemy.y))

            lowest_go_down_game_over += 1
            heli.y += heli.speed
            heli.rect = game.heli_frames[heli.frame].get_rect(topleft = (heli.x, heli.y))

        heli = copy.deepcopy(game.heli)
        obstacles = copy.deepcopy(game.obstacles)
        enemies = copy.deepcopy(game.enemies)

        state = [game.heli.y, lowest_go_up_game_over, lowest_go_down_game_over, danger]
        return state

    def remember(self, state, action, reward, next_state, game_over):
        self.memory.append((state, action, reward, next_state, game_over))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, game_overs = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, game_overs)

    def train_short_memory(self, state, action, reward, next_state, game_over):
        self.trainer.train_step(state, action, reward, next_state, game_over)

    def get_action(self, state):
        self.epsilon = 0.2
        action = [0,0,0]
        if random.random() < self.epsilon:
            action_idx = random.randint(0, 1)
            action[action_idx] = 1
        else:
            state_0 = torch.tensor(state, dtype = torch.float)
            prediction = self.model(state_0)
            action_idx = torch.argmax(prediction)
            action[action_idx] = 1

        return action


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = HeliMania()

    while True:
        state = agent.get_state(game)
        action = agent.get_action(state)

        reward, game_over, score = game.play_step(action)
        next_state = agent.get_state(game)

        agent.train_short_memory(state, action, reward, next_state, game_over)
        agent.remember(state, action, reward, next_state, game_over)

        if game_over:
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print(f'Game: {agent.n_games}, Score: {score}, Record: {record}')

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)

def test():
    agent = Agent()
    game = HeliMania()
    score = 0
    agent.model.load()
    while True:
        state = agent.get_state(game)
        action = agent.get_action(state)

        reward, game_over, score = game.play_step(action)
        
        if game_over:
            print(f'Score = {score}')
            break

if __name__ == '__main__':

    # train()
    test()