import random

class RandomAI:
    def decide_dutch(self):
        return False

    def decide_swap_position(self):
        pos = random.randint(0, 3)
        return pos

    def decide_use_ability(self):
        return False