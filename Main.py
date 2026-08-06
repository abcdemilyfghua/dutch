import collections
import random

#Define constants for card properties
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

#Represents a single playing card
class Card:
    def __init__(self, rank, suit):
        # rank: 'A','2'-'10','J','Q','K', or 'JOKER_SMALL'/'JOKER_BIG'
        # suit: 'H','D','C','S', or None for jokers
        self.rank = rank
        self.suit = suit

    @property
    def value(self):
        if self.rank == "JOKER_SMALL":
            return -1
        elif self.rank == "JOKER_BIG":
            return -2
        elif self.rank == "A":
            return 1
        elif self.rank == "K":
            if self.suit == "♥" or self.suit == "♦":
                return 0
            return 13
        elif self.rank in ("Q"):
            return 12
        elif self.rank in ("J"):
            return 11
        else:
            return int(self.rank)

    def __repr__(self):
        return f"{self.rank}{self.suit}"

#Represents a standard 52-card deck + 2 jokers
class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for s in SUITS for r in RANKS]
        self.cards.append(Card("JOKER_SMALL", None))
        self.cards.append(Card("JOKER_BIG", None))
        self.discard_pile = []
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if len(self.cards) == 0:
            self.reshuffle_discard_into_deck()
        return self.cards.pop()

    def discard(self, card):
        self.discard_pile.append(card)

    def reshuffle_discard_into_deck(self):
        if len(self.discard_pile) == 0:
            raise RuntimeError("deck and discard both empty")  
        self.cards = self.discard_pile
        self.discard_pile = []
        self.shuffle()

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

d = Deck()
print(len(d.cards))  # expect 54
c = []
for i in range(0, 4):
    c.append(d.draw())
p = PlayerGrid(c)
print(p)
print(p.total_value())
nc = Card("2", "♥")
p.swap(1, nc)
print(p)
print(p.total_value())
