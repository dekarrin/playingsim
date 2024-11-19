from ..games.klondike import State, Action
from . import Player as BasePlayer
from .. import cio


class Human(BasePlayer):

    def __init__(self, rules: dict):
        self.rules = rules

    def next_move(self, s: State) -> Action:
        print(s.board())

        moves = [(m, str(m)) for i, m in enumerate(s.legal_moves())]
        moves.append((-1, 'Give Up'))

        m = cio.select('Select move', moves)

        if m == -1:
            return None
        
        return m
    
