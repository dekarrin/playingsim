
from . import card


class Deck:
    """A deck of cards"""

    def __init__(self, cards: list[card.Card] | None=None):
        """
        Create a new deck of cards. If cards is not provided, creates a standard
        52-card deck.
        """

        if cards is None:
            cards = [card.Card(s, r) for r in card.Rank for s in card.Suit]

        self.cards = cards
    
    def __add__(self, other) -> "Deck":
        if not isinstance(other, Deck):
            raise TypeError("Can only add a Deck to another Deck")
        return Deck(self.cards + other.cards)
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __getitem__(self, key) -> card.Card:
        return self.cards[key]
    
    def shuffle(self):
        """Shuffle the deck"""
        import random
        random.shuffle(self.cards)

    def draw(self) -> card.Card:
        """Draw a card from the deck"""
        return self.cards.pop()
    