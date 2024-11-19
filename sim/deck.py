
from . import card


class Deck:
    """
    A deck of cards, implemented as a list of Card objects where the top of the
    deck (the next card drawn) is the first element of the list. This class can
    generally be substituted anywhere a list of Card objects is expected.
    """

    def __init__(self, cards: list[card.Card] | None=None):
        """
        Create a new deck of cards. If cards is not provided, creates a standard
        52-card deck.
        """

        if cards is None:
            cards = [card.Card(s, r) for r in card.Rank for s in card.Suit]

        self.cards = cards

    def __str__(self) -> str:
        return f"Deck({str(self.cards)})"
    
    def __repr__(self) -> str:
        return f"Deck({repr(self.cards)})"
    
    def shuffle(self):
        """Shuffle the deck. Note according to docs for random.shuffle, if we
        end up shuffling things with more than some card limit (TODO: 2080 says
        the AI, sounds about right, double check in future), it will start
        repeating its period. Probably not a concern, but wanted to note it for
        possible future silly simulations."""
        import random
        random.shuffle(self.cards)

    def draw(self) -> card.Card:
        """Draw a card from the deck"""
        if len(self) < 1:
            raise ValueError("No cards left in the deck")
        c = self.cards[0]
        self.cards.remove(c)
        return c
    
    @property
    def top(self) -> card.Card | None:
        """The top card of the deck or None if the deck is empty."""
        return self.cards[0] if len(self) > 0 else None
    
    @property
    def bottom(self) -> card.Card:
        """The bottom card of the deck or None if the deck is empty."""
        return self.cards[-1] if len(self) > 0 else None

    @property
    def empty(self) -> bool:
        """Return whether this deck is out of cards."""
        return len(self) == 0
    
    def draw_n(self, n: int=1, or_fewer: bool=False) -> list[card.Card]:
        """
        Draw multiple cards from the deck, and return them in the order they
        would be drawn.
        """
        if n > len(self):
            if or_fewer:
                n = len(self)
                if n == 0:
                    return []
            else:
                raise ValueError("Not enough cards in the deck")
            
        drawn = self.cards[:n]
        self.cards = self.cards[n:]
        return drawn
    
    def top_n(self, n: int=1, or_fewer: bool=False) -> list[card.Card]:
        """
        Return the top n cards of the deck, in the order they would be drawn.
        """
        if n > len(self):
            if or_fewer:
                n = len(self)
                if n == 0:
                    return []
            else:
                raise ValueError("Not enough cards in the deck")
        
        return self.cards[:n]
    
    def clone(self) -> 'Deck':
        """Return a copy of this deck"""
        return Deck([c.clone() for c in self.cards])
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __getitem__(self, key) -> card.Card:
        return self.cards[key]
    
    def append(self, card: card.Card):
        """Add a card to the deck"""
        self.cards.append(card)

    def count(self, card: card.Card) -> int:
        """Return the number of cards in the deck that match the given card"""
        return self.cards.count(card)

    def index(self, card: card.Card, **kwargs) -> int:
        """Return the index of the first card in the deck that matches the given
        card"""
        return self.cards.index(card, **kwargs)
    
    def extend(self, cards: 'list[card.Card] | Deck'):
        """Add multiple cards to the deck"""
        if isinstance(cards, Deck):
            self.extend(cards.cards)
        else:
            self.cards.extend(cards)

    def insert(self, index: int, x: 'card.Card | list[card.Card] | Deck'):
        """Insert a card at the given index"""
        if isinstance(x, card.Card):
            self.cards.insert(index, x)
        elif isinstance(x, list):
            if index > len(self.cards):
                index = len(self.cards)
            old_cards = self.cards
            self.cards = old_cards[:index] + x
            if index < len(old_cards):
                self.cards += old_cards[index:]
        elif isinstance(x, Deck):
            self.insert(index, x.cards)
        else:
            raise TypeError("Can only insert a Card, list of Cards, or Deck")

    def pop(self, index: int=-1) -> card.Card:
        """Remove and return the card at the given index"""
        return self.cards.pop(index)

    def remove(self, card: card.Card):
        """Remove the first instance of the given card from the deck"""
        self.cards.remove(card)

    def reverse(self):
        """Reverse the order of the cards in the deck"""
        self.cards.reverse()

    def sort(self, key=None, reverse: bool=False):
        """Sort the cards in the deck"""
        self.cards.sort(key=key, reverse=reverse)
    
