from Round import Round
from RandomAI import Mordna
import random

def get_yes_no(prompt):
    # keep asking until they type something starting with y or n,
    # return True/False.
    while True:
        answer = input(prompt)
        if answer[0].lower() == "y":
            return True
        elif answer[0].lower() == "n":
            return False
        print("Please enter yes or no.")

def setup_players():
    num_players = int(input("How many players? "))
    players = []
    agents = {}
    for i in range(num_players):
        is_ai = get_yes_no(f"Is player {i+1} an AI? (y/n) ")
        if is_ai:
            name = "Mordna"
            counter = 2
            while name in players:
                name = f"Mordna {counter}"
                counter += 1
            agents[name] = Mordna()
        else:
            name = input(f"Player {i+1} name: ")
            while name in players:
                name = input(f"A player with this name already exists. Try another. Player {i+1} name: ")
            agents[name] = None
        players.append(name)
    return players, agents

def main():
    players, agents = setup_players()
    r = Round(players)

    # Initial peek for everyone before play starts
    for player in players:
        if agents[player] is None:
            print(f"{player}'s turn to peek.")
            # ask for two positions (0-3), call r.initial_peek, print the result
            pos1 = int(input("Which position (0-3) do you want to peek first?"))
            pos2 = int(input("Which position (0-3) do you want to peek next?"))
        else:
            pos1 = random.randint(0, 3)
            pos2 = random.randint(0, 3)
        initial_peeked = r.initial_peek(player, pos1, pos2)
        print(initial_peeked)


    while not r.is_round_over():
        current = r.players[r.current_turn]
        print(f"\n--- {current}'s turn ---")
        print(r.grids[current])  # remember: this shows YOUR OWN cards face down in reality,
                                   # but for now while testing solo, showing everything is fine

        if r.dutch_caller is None:
            if agents[current] is None:
                wants_dutch = get_yes_no(f"{current}, call Dutch instead of drawing? (y/n) ")
            else:
                wants_dutch = agents[current].decide_dutch()
        else:
            wants_dutch = False

        if wants_dutch:
            r.call_dutch()
        else:
            drawn = r.draw_card()
            print(f"You drew: {drawn}")
            
            if agents[current] is None:
                wants_swap = get_yes_no("Swap it into your grid? (y/n) ")
                if wants_swap:
                    pos = int(input("Which position (0-3)? "))
                    discarded = r.resolve_draw(drawn, swap_position=pos)
                else:
                    discarded = r.resolve_draw(drawn, swap_position=None)
            else:
                pos = agents[current].decide_swap_position()
                discarded = r.resolve_draw(drawn, swap_position=pos)

            if discarded.rank == "J":
                if agents[current] is None:
                    use_ability = get_yes_no(f"That was a J. Do you want to blindly swap two cards? (y/n) ")
                else:
                    use_ability = agents[current].decide_use_ability()
                if use_ability:
                    if agents[current] is None:
                        pos_a_player = input("Which player? ")
                        pos_a = int(input("Which position (0-3)? "))
                        pos_b_player = input("Which player? ")
                        pos_b = int(input("Which position (0-3)? "))
                    else:
                        pos_a_player, pos_a, pos_b_player, pos_b = agents[current].decide_targets(players)
                    r.play_jack(pos_a_player, pos_a, pos_b_player, pos_b)
                    print("Swap done.")

            if discarded.rank == "Q":
                if agents[current] is None:
                    use_ability = get_yes_no(f"That was a Q. Do you want to peek at two cards? (y/n) ")
                else:
                    use_ability = agents[current].decide_use_ability()
                if use_ability:
                    if agents[current] is None:
                        pos_a_player = input("Which player? ")
                        pos_a = int(input("Which position (0-3)? "))
                        pos_b_player = input("Which player? ")
                        pos_b = int(input("Which position (0-3)? "))
                    else:
                        pos_a_player, pos_a, pos_b_player, pos_b = agents[current].decide_targets(players)
                    queen_peeked = r.play_queen(pos_a_player, pos_a, pos_b_player, pos_b)
                    print(queen_peeked)

        r.advance_turn()

    totals, winner = r.score()
    print("\n--- Round over ---")
    print(totals)
    print(f"Winner: {winner}")

    for player in players:
        print(f"{player}'s cards: {r.grids[player]}")

if __name__ == "__main__":
    main()