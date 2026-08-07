class PlayerGrid:
    def __init__(self, cards):
        # cards: a list of exactly 4 Card objects, dealt at round start
        self.cards = cards

    def get_card(self, position):
        return self.cards[position]

    def swap(self, position, new_card):
        old_card = self.cards[position]
        self.cards[position] = new_card
        return old_card

    def total_value(self):
        total = 0
        for card in self.cards:
            total += card.value
        return total

    def __repr__(self):
        return " ".join(str(card) for card in self.cards)

