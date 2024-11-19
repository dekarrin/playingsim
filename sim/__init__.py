
class UndoAction:
    def __init__(self):
        pass

    def __eq__(self, other):
        return isinstance(other, UndoAction)
