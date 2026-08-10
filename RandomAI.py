import random

class Mordna:
    def decide_dutch(self):
        # adjust threshold value if calls dutch too much/little
        return random.random() < 0.05 

    def decide_swap_position(self):
        pos = random.randint(0, 3)
        return pos

    def decide_use_ability(self):
        return random.random() < 0.5

    def decide_targets(self, players):
        pos_a_player = random.choice(players)
        pos_a = random.randint(0, 3)
        pos_b_player = random.choice(players)
        pos_b = random.randint(0, 3)
        return (pos_a_player, pos_a, pos_b_player, pos_b)