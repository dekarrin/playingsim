from .games import Game, Player, RulesError


def play_until_done(game: Game, players: list[Player]):
    if len(players) < game.min_players:
        raise ValueError('Not enough players')
    if len(players) > game.max_players:
        raise ValueError('Too many players')
    
    while game.running:
        p = players[game.current_player]
        m = p.next_move(game.state)
        if m is None:
            print("Player {:d} gave up".format(game.current_player))
            return
        
        try:
            game.take_turn(game.current_player, m)
        except RulesError as e:
            print("Illegal move: {!s}".format(e))
            print("Try again")
