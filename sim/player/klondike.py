from ..games.klondike import State, Action


class Human:

    def __init__(self, rules: dict):
        self.rules = rules

    def next_move(self, s: State) -> Action:
        print(s.board())