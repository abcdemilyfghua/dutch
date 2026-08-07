from Grid import PlayerGrid
from Cards import Deck 

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
