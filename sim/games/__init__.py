

class RulesError(Exception):
    pass


class PlayableGame:

    def take_turn(self, player: int, move: any) -> None:
        """
        Take turn executes the given move for the given player. The move
        argument will depend on the game being played.
        """
        raise NotImplementedError()
    
    @property
    def running(self) -> bool:
        """Return whether the game is still running. Return False if the game
        is over or in a draw state where it cannot continue."""
        raise NotImplementedError()
    
    @property
    def rules(self) -> dict:
        """
        Return a dict containing information about parameters of the current
        game that may difer from others of the same type. For instance, whether
        turn 3 or turn 1 is set in Klondike solitaire.
        """
        raise NotImplementedError()
    
    @property
    def state(self) -> any:
        """
        Return an object containing information about the current state of the
        game. An AI or human player can use this to make decisions about the
        next turn.
        """
        raise NotImplementedError()
    
    @property
    def max_players(self) -> int:
        """Return the maximum number of players that can play this game."""
        return 0
    
    @property
    def min_players(self) -> int:
        """Return the minimum number of players that can play this game."""
        return 0
    