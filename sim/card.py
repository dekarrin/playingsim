from enum import IntEnum, auto
from typing import Any

# Enums implement IntEnum to allow for ordering.

class CustomSuit:
    """
    CustomSuit is a non-standard suit that implements the same methods as Suit,
    allowing it to be used anywhere Suit is expected.
    """

    def __init__(self, name: str, short: str | None=None, value: int | None=0, is_red: bool | None=False):
        self.name = "CUSTOM:" + name
        self._short = short if short is not None else name[0].upper()
        self._value = value if value is not None else 0
        self._is_red = is_red is not None and is_red

    @property
    def value(self) -> int:
        return self._value

    def short(self) -> str:
        return self._short
    
    def black(self) -> bool:
        return not self._is_red
    
    def red(self) -> bool:
        return self._is_red
    
    def color(self) -> str:
        return "red" if self.red() else "black"


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
    
    def short(self) -> str:
        return self.name[0].upper()
    
    def black(self) -> bool:
        return self in (Suit.CLUBS, Suit.SPADES)
    
    def red(self) -> bool:
        return self in (Suit.DIAMONDS, Suit.HEARTS)
    
    def color(self) -> str:
        return "black" if self.black() else "red"
    
    @classmethod
    def parse(cls, s: str, allow_custom: bool=False, short: str | None=None, value: int | None=None, is_red: bool | None=None) -> 'Suit | CustomSuit':
        if s.upper() == 'C' or s.upper() == 'CLUBS':
            return cls.CLUBS
        elif s.upper() == 'D' or s.upper() == 'DIAMONDS':
            return cls.DIAMONDS
        elif s.upper() == 'H' or s.upper() == 'HEARTS':
            return cls.HEARTS
        elif s.upper() == 'S' or s.upper() == 'SPADES':
            return cls.SPADES
        elif allow_custom or short is not None or value is not None or is_red is not None:
            return CustomSuit(s, short, value, is_red)
        else:
            raise ValueError(f"Invalid suit: {s}")
    

class CustomRank:
    """
    CustomRank is a non-standard rank that implements the same methods as Rank,
    allowing it to be used anywhere Rank is expected.
    """

    def __init__(self, name: str, short: str | None=None, value: int | None=None):
        self.name = "CUSTOM:" + name
        self._short = short if short is not None else name[0].upper()
        self._value = value if value is not None else 0

    def __repr__(self) -> str:
        return f"CustomRank({self.name}, short={repr(self._short)}, value={repr(self._value)})"
    
    def __str__(self) -> str:
        return self.name

    def short(self) -> str:
        return self._short
    
    @property
    def value(self) -> int:
        return self._value

class Rank(IntEnum):
    """
    Rank is a standard French playing card rank of 1-13, with 1 called Ace and
    11-13 called Jack, Queen, and King. Note: for consistency purposes, the
    TEN rank's short name is 'X' rather than 10, so all ranks are a single
    character.
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
        if self.value == 1:
            return 'A'
        elif self.value < 10:
            return str(self.value)
        elif self.value == 10:
            return 'X'
        else:
            return self.name[0].upper()
        
    @classmethod
    def parse(cls, s: str, allow_custom: bool=False, short: str | None=None, value: int | None=None) -> 'Rank | CustomRank':
        if s.upper() in ['A', 'ACE', 'ONE', '1']:
            return cls.ACE
        elif s.upper() == '2' or s.upper() == 'TWO':
            return cls.TWO
        elif s.upper() == '3' or s.upper() == 'THREE':
            return cls.THREE
        elif s.upper() == '4' or s.upper() == 'FOUR':
            return cls.FOUR
        elif s.upper() == '5' or s.upper() == 'FIVE':
            return cls.FIVE
        elif s.upper() == '6' or s.upper() == 'SIX':
            return cls.SIX
        elif s.upper() == '7' or s.upper() == 'SEVEN':
            return cls.SEVEN
        elif s.upper() == '8' or s.upper() == 'EIGHT':
            return cls.EIGHT
        elif s.upper() == '9' or s.upper() == 'NINE':
            return cls.NINE
        elif s.upper() == '10' or s.upper() == 'TEN' or s.upper() == 'X':
            return cls.TEN
        elif s.upper() == 'J' or s.upper() == 'JACK':
            return cls.JACK
        elif s.upper() == 'Q' or s.upper() == 'QUEEN':
            return cls.QUEEN
        elif s.upper() == 'K' or s.upper() == 'KING':
            return cls.KING
        elif allow_custom or short is not None or value is not None:
            return CustomRank(s, short, value)
        else:
            raise ValueError(f"Invalid rank: {s}")


class Card:
    """
    FrenchCard is the standard playing card with suit of clubs, diamonds,
    hearts, or spades, and rank of Ace through King.
    """

    def __init__(self, rank: Rank | CustomRank | int | Any, suit: Suit | CustomSuit | int | Any):
        if isinstance(rank, Rank):
            self.rank = rank
        elif isinstance(rank, CustomRank):
            self.rank = rank
        elif isinstance(rank, int):
            self.rank = Rank(rank)
        else:
            self.rank = CustomRank(str(rank))

        if isinstance(suit, Suit):
            self.suit = suit
        elif isinstance(suit, CustomSuit):
            self.suit = suit
        elif isinstance(suit, int):
            self.suit = Suit(suit)
        else:
            self.suit = CustomSuit(str(suit))

    @classmethod
    def kings(cls) -> list['Card']:
        return [Card(Rank.KING, s) for s in Suit]
    
    @classmethod
    def queens(cls) -> list['Card']:
        return [Card(Rank.QUEEN, s) for s in Suit]
    
    @classmethod
    def jacks(cls) -> list['Card']:
        return [Card(Rank.JACK, s) for s in Suit]
    
    @classmethod
    def tens(cls) -> list['Card']:
        return [Card(Rank.TEN, s) for s in Suit]
    
    @classmethod
    def nines(cls) -> list['Card']:
        return [Card(Rank.NINE, s) for s in Suit]
    
    @classmethod
    def eights(cls) -> list['Card']:
        return [Card(Rank.EIGHT, s) for s in Suit]
    
    @classmethod
    def sevens(cls) -> list['Card']:
        return [Card(Rank.SEVEN, s) for s in Suit]
    
    @classmethod
    def sixes() -> list['Card']:
        return [Card(Rank.SIX, s) for s in Suit]
    
    @classmethod
    def fives(cls) -> list['Card']:
        return [Card(Rank.FIVE, s) for s in Suit]
    
    @classmethod
    def fours(cls) -> list['Card']:
        return [Card(Rank.FOUR, s) for s in Suit]
    
    @classmethod
    def threes(cls) -> list['Card']:
        return [Card(Rank.THREE, s) for s in Suit]
    
    @classmethod
    def twos(cls) -> list['Card']:
        return [Card(Rank.TWO, s) for s in Suit]
    
    @classmethod
    def aces(cls) -> list['Card']:
        return [Card(Rank.ACE, s) for s in Suit]
    
    @classmethod
    def of_hearts(cls) -> list['Card']:
        return [Card(r, Suit.HEARTS) for r in Rank]
    
    @classmethod
    def of_diamonds(cls) -> list['Card']:
        return [Card(r, Suit.DIAMONDS) for r in Rank]
    
    @classmethod
    def of_clubs(cls) -> list['Card']:
        return [Card(r, Suit.CLUBS) for r in Rank]
    
    @classmethod
    def of_spades(cls) -> list['Card']:
        return [Card(r, Suit.SPADES) for r in Rank]

    def __str__(self) -> str:
        return f"{self.rank.short()}{self.suit.short()}"
    
    def __repr__(self) -> str:
        return f"<{self.rank.name} of {self.suit.name}>"
    
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
        return Card(self.rank, self.suit)
    
    @classmethod
    def parse(cls, s: str) -> 'Card':
        if len(s) != 2:
            raise ValueError(f"Invalid card: {s}")
        
        return Card(Rank.parse(s[0]), Suit.parse(s[1]))
    

