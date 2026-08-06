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
        if self.suit is None:
            return self.rank
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


# d = Deck()
# print(len(d.cards))  # expect 54
# c = []
# for i in range(0, 4):
#     c.append(d.draw())
# p = PlayerGrid(c)
# print(p)
# print(p.total_value())
# nc = Card("2", "♥")
# p.swap(1, nc)
# print(p)
# print(p.total_value())


class Round:
    def __init__(self, players):
        self.players = players
        self.deck = Deck()
        self.grids = {}
        self.current_turn = 0
        self.dutch_caller = None
        self.round_over = False
        self.peeked_players = set()

        for i in range(len(players)):
            cards = []
            for _ in range(0, 4):
                cards.append(self.deck.draw())
            self.grids[players[i]] = PlayerGrid(cards)

    def initial_peek(self, player, pos_a, pos_b):
        if player in self.peeked_players:
            raise RuntimeError("You cannot look at your cards again")
        else:
            self.peeked_players.add(player)
        return self.play_queen(player, pos_a, player, pos_b)
        
    def draw_card(self):
        return self.deck.draw()

    def resolve_draw(self, drawn_card, swap_position=None):
        current = self.players[self.current_turn]

        if swap_position != None:
            current_grid = self.grids[current]
            old_card = current_grid.swap(swap_position, drawn_card)
            self.deck.discard(old_card)
            return old_card
        else:
            self.deck.discard(drawn_card)
            return drawn_card

    def play_jack(self, pos_a_player, pos_a, pos_b_player, pos_b):
        card_a = self.grids[pos_a_player].get_card(pos_a)
        card_b = self.grids[pos_b_player].get_card(pos_b)
        self.grids[pos_a_player].swap(pos_a, card_b)
        self.grids[pos_b_player].swap(pos_b, card_a)

    def play_queen(self, pos_a_player, pos_a, pos_b_player, pos_b):
        card_a = self.grids[pos_a_player].get_card(pos_a)
        card_b = self.grids[pos_b_player].get_card(pos_b)
        return (card_a, card_b)

    def call_dutch(self):
        self.dutch_caller = self.players[self.current_turn]
        self.advance_turn()

    def advance_turn(self):
        if self.current_turn != len(self.players) - 1:
            self.current_turn += 1
        else:
            self.current_turn = 0

        if self.dutch_caller != None:
            if self.dutch_caller == self.players[self.current_turn]:
                self.round_over = True

    def is_round_over(self):
        return self.round_over

    def score(self):
        totals_dict = {}
        for i in range(len(self.players)):
            totals_dict[self.players[i]] = self.grids[self.players[i]].total_value()
        
        winner = min(totals_dict, key=totals_dict.get)
        return (totals_dict, winner)

r = Round(["Alice", "Bob"])
print(r.initial_peek("Alice", 0, 2))  # should show two real cards
try:
    r.initial_peek("Alice", 1, 3)  # should raise
    print("BUG: should have raised!")
except RuntimeError as e:
    print("correctly blocked:", e)