from enum import IntEnum, auto

# Enums implement IntEnum to allow for ordering.


class Suit(IntEnum):
    """
    Suit is a standard French playing card suit of clubs, diamonds, hearts, or
    spades.
    """

    CLUBS = auto()
    DIAMONDS = auto()
    HEARTS = auto()
    SPADES = auto()

    def __str__(self) -> str:
        return self.name.title()
    
    def black(self) -> bool:
        return self in (Suit.CLUBS, Suit.SPADES)
    
    def red(self) -> bool:
        return self in (Suit.DIAMONDS, Suit.HEARTS)
    
    def color(self) -> str:
        return "black" if self.black() else "red"
    

class Rank(IntEnum):
    """
    Rank is a standard French playing card rank of 1-13, with 1 called Ace and
    11-13 called Jack, Queen, and King.
    """
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    def __str__(self) -> str:
        return self.name.title()
    
    def short(self) -> str:
        if self.value <= 10:
            return str(self.value)
        else:
            return self.name[0].upper()


class Card:
    """
    FrenchCard is the standard playing card with suit of clubs, diamonds,
    hearts, or spades, and rank of Ace through King.
    """

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __str__(self) -> str:
        return f"{self.rank.short()}{self.suit.name[0].upper()}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        
        return self.suit == other.suit and self.rank == other.rank
    
    def __hash__(self) -> int:
        return hash((self.suit, self.rank))
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        
        if self.rank == other.rank:
            return self.suit < other.suit
        else:
            return self.rank < other.rank
        
    def color(self) -> str:
        return self.suit.color()
    
    def is_black(self) -> bool:
        return self.suit.black()
    
    def is_red(self) -> bool:
        return self.suit.red()
    
    def clone(self) -> 'Card':
        return Card(self.suit, self.rank)
    

