from ..card import Card, Suit, Rank
from ..deck import Deck
from . import RulesError

from enum import Enum, auto


class Foundation:
    """
    Ultimate destination for all cards of a given suit. Index -1 is the bottom of
    the pile, and index 0 is the top.
    """

    def __init__(self, suit: Suit):
        self.suit = suit
        self.cards: list[Card] = []

    def add(self, card: Card):
        if card.suit != self.suit:
            raise ValueError("Card does not match foundation suit")
        if len(self.cards) > 0:
            if card.rank != self.cards[0].rank + 1:
                raise ValueError("Card does not follow the previous card in the foundation")
        elif card.rank != Rank.ACE:
            raise ValueError("First card in foundation must be an Ace")
        
        self.cards.insert(0, card)

    def needs(self) -> Card | None:
        if len(self.cards) == 0:
            return Card(self.suit, Rank.ACE)
        elif len(self.cards) == Rank.KING.value:
            return None
        
        return Card(self.suit, self.cards[0].rank + 1)

    def remove(self) -> Card:
        if len(self.cards) == 0:
            raise ValueError("Foundation is empty")
        c = self.cards[0]
        del self.cards[0]
        return c
    
    def top(self) -> Card | None:
        if len(self.cards) == 0:
            return None
        return self.cards[0]
    
    def __len__(self) -> int:
        return len(self.cards)


class Pile:
    """A tableau pile of cards in Klondike Solitaire"""

    def __init__(self, cards: list[Card]):
        """
        Create a new pile that contains the given cards, with the last card at
        the bottom of the pile and the first card at the top. The first card
        will immediately be turned over and added to the revealed cards on top
        of the pile; the rest remain unrevealed and not known to the player
        unless Thoughtful Klondike rules are in effect.
        """
        self.shown: list[Card] = []
        self.hidden: list[Card] = []

        if len(cards) > 0:
            self.shown = [cards[0]]
            if len(cards) > 1:
                self.hidden = cards[1:]

    def __len__(self) -> int:
        return len(self.shown + self.hidden)
    
    def __getitem__(self, key) -> Card:
        return (self.shown + self.hidden)[key]
    
    def take(self, count: int) -> list[Card]:
        """
        Remove the top count cards from the pile's shown cards and return them.
        If there are fewer than count cards in the pile, raises a ValueError.
        """
        if count > len(self.shown):
            raise ValueError("Cannot take {:d} cards; only {:d} cards are revealed".format(count, len(self.shown)))
        cards = self.shown[:count]
        self.shown = self.shown[count:]
        if len(self.shown) == 0 and len(self.hidden) > 0:
            self.shown = [self.hidden.pop()]
        return cards

    def needs(self) -> list[Card]:
        """
        Return a list of all cards that could be used to continue building this
        tableau. This will either be all four kings (if the pile is empty), the
        two cards of the opposite color that could be placed on top of the pile,
        or an empty list if no cards could be placed on the pile (if it
        currently has an Ace on top).
        """
        if len(self.shown) == 0:
            return [Card(s, Rank.KING) for s in Suit]
        elif self.shown[0] == Rank.ACE:
            return []
        else:
            t = self.top()
            if t.is_black():
                return [Card(Suit.DIAMONDS, t.rank - 1), Card(Suit.HEARTS, t.rank - 1)]
            else:
                return [Card(Suit.CLUBS, t.rank - 1), Card(Suit.SPADES, t.rank - 1)]
    
    def give(self, cards: list[Card]):
        """Add the given cards to the top of the revealed section of the pile.
        This is only allowed if the given cards are in alternating colors and
        descending ranks from the top card of the pile. Both will be checked.
        """

        # validate the cards being given first
        bot_given = cards[-1]
        last_card = bot_given

        if len(cards) > 1:
            for c in cards[0:-1]:
                if c.color() == last_card.color() or c.rank != last_card.rank - 1:
                    raise ValueError("Given cards are not a valid stack")
                last_card = c

        # okay, checked the pile, now check that the bottom can actually be
        # added to the top of the pile
        if not self.empty():
            current_top = self.top()
            if bot_given.color() == current_top.color() or bot_given.rank != current_top.rank - 1:
                raise ValueError("Given cards are not a valid stack")
            
        self.shown = cards + self.shown
    
    def top(self) -> Card | None:
        """Return the top card of the pile, or None if this pile is currently
        empty.
        """
        if len(self.shown) == 0:
            if len(self.hidden) > 0:
                # not a valid state, somebody forgot to turn over the top hidden
                # card. This is fixable.
                self.shown = [self.hidden.pop()]
                return self.shown[0]

            return None
        return self.shown[0]
        
    def empty(self) -> bool:
        """Return True if this pile is empty, False otherwise"""
        return len(self.shown) == 0 and len(self.hidden) == 0


class TurnType(Enum):
    DRAW = auto()
    MOVE_STACK = auto()
    MOVE_ONE = auto()


class CardLocation(Enum):
    TABLEAU = auto()
    FOUNDATION = auto()
    WASTE = auto()


class Action:
    def __init__(self, type: TurnType):
        self.type = type


class DrawAction(Action):
    def __init__(self):
        super().__init__(TurnType.DRAW)

class MoveStackAction(Action):
    def __init__(self, source_pile: int, dest_pile: int, count: int):
        super().__init__(TurnType.MOVE_STACK) 

        if source_pile == dest_pile:
            raise ValueError("Source and destination piles must be different")
        
        if source_pile < 0 or dest_pile < 0:
            raise ValueError("Pile indices must be non-negative")
        
        if count < 1:
            raise ValueError("Stack must have count of at least 1")

        self.source_pile = source_pile
        self.dest_pile = dest_pile
        self.count = count


class MoveOneAction(Action):
    def __init__(self, source: CardLocation, dest: CardLocation, source_pile: int | None=None, dest_pile: int | None=None):
        super().__init__(TurnType.MOVE_ONE)
        self.source = source
        self.source_pile = source_pile
        self.dest = dest
        self.dest_pile = dest_pile

        # TODO: make all these checks in rules validation in game engine as
        # well.

        if self.dest == self.source:
            # it's possible someone will encounter this error while trying to move 1 card between tableaus; they should use the stack move instead
            raise ValueError("Source and destination locations must be different")
        
        if self.dest != CardLocation.TABLEAU and self.dest_pile is not None:
            raise ValueError("Destination pile is only valid for moves to tableau")
        elif self.dest == CardLocation.TABLEAU and self.dest_pile is None:
            raise ValueError("Destination pile is required for moves to tableau")
        if self.source != CardLocation.TABLEAU and self.source_pile is not None:
            raise ValueError("Source pile is only valid for moves from tableau")
        elif self.source == CardLocation.TABLEAU and self.source_pile is None:
            raise ValueError("Source pile is required for moves from tableau")
        
        if self.dest_pile is not None and self.source_pile is not None and self.dest_pile == self.source_pile:
            raise ValueError("Source and destination piles must be different")
        
        # moving to waste is always invalid
        elif self.dest == CardLocation.WASTE:
            raise ValueError("Cannot move card to waste pile")


class Turn:
    def __init__(self, action: Action, player: int=0):
        self.action = action
        self.player = player


class Game:
    """
    The state of a game of Klondike Solitaire
    """

    def __init__(self, draw_count: int=1, stock_pass_limit: int=0, deck: Deck | None=None, num_piles: int=7):
        self.random_deck: bool = deck is None
        if deck is None:
            deck = Deck()
            deck.shuffle()
        
        self.starting_deck = list(deck)
        self.draw_count = draw_count
        self.stock_pass_limit = stock_pass_limit
        self.tableau: list[Pile] = []
        self.foundations: dict[Suit, Foundation] = {s: [] for s in Suit}
        self.stock: Deck = deck
        self.waste: Deck = Deck(cards=[])

        # build the tableau
        for pile_idx in range(num_piles):
            p = Pile(reversed(self.stock.draw_n(pile_idx+1)))
            self.tableau.append(p)

        # pull first hand
        self.draw_stock()

    def draw_stock(self):
        # TODO: limit by passes
        if len(self.stock) == 0:
            # if we have waste, flip it first if we can
            if len(self.waste) == 0:
                raise RulesError("Stock and waste piles are empty")
            self.stock = self.waste
        
        for _ in range(self.draw_count):
            if len(self.stock) == 0:
                continue
            c = self.stock.draw()
            self.waste.insert(0, c)

    def move_tableau_stack(self, source_pile: int, dest_pile: int, count: int):
        if source_pile < 0 or source_pile >= len(self.tableau):
            raise ValueError("Invalid source tableau pile")
        
        if dest_pile < 0 or dest_pile >= len(self.tableau):
            raise ValueError("Invalid destination tableau pile")
        
        if count < 1:
            raise ValueError("Stack must have count of at least 1")
        
        source_tableau = self.tableau[source_pile]
        dest_tableau = self.tableau[dest_pile]
        
        if count > len(source_tableau.shown):
            raise RulesError("Cannot move more cards than are shown in the source pile")
        
        cur_bot = source_tableau.shown[count - 1]
        next_needed = dest_tableau.needs()
        if cur_bot not in next_needed:
            raise RulesError("Cannot move stack with bottom card {:s} to tableau[{:d}]; legal cards are {:s}".format(str(cur_bot), dest_pile, ', '.join([str(c) for c in next_needed])))
        
        cards = self.tableau[source_pile].take(count)
        self.tableau[dest_pile].give(cards)

    def move_tableau_card(self, source_pile: int, dest: CardLocation):
        if dest == CardLocation.TABLEAU:
            raise RulesError("Use move_tableau_stack to move cards to tableau")
        elif dest == CardLocation.WASTE:
            raise RulesError("Cannot move cards to waste pile")
        elif dest == CardLocation.FOUNDATION:
            if source_pile < 0 or source_pile >= len(self.tableau):
                raise ValueError("Invalid source tableau pile")

            t = self.tableau[source_pile]
            card = t.top()
            # get the foundation to move it to
            f = self.foundations[card.suit]
            expected = f.needs()
            if card != expected:
                raise RulesError("Cannot add {:s} to {:s} foundation pile; legal cards are {:s}".format(str(card), f.suit.name, str(expected)))
            
            c = t.take(1)[0]
            f.add(c)
        else:
            raise ValueError("Invalid destination location")
        
    def move_waste_card(self, dest: CardLocation, dest_pile: int | None=None):
        """
        Move the card at the top of the waste pile to the given location.
        """
        if dest != CardLocation.TABLEAU and dest_pile is not None:
            raise ValueError("Destination pile is only valid for moves to tableau")
        
        if dest == CardLocation.TABLEAU:
            if dest_pile is None:
                raise ValueError("Destination pile is required for moves to tableau")
            if dest_pile < 0 or dest_pile >= len(self.tableau):
                raise ValueError("Invalid destination tableau pile")
            
            t = self.tableau[dest_pile]
            card = self.waste.top

            if card not in t.needs():
                raise RulesError("Cannot add {:s} to tableau[{:d}]; legal cards are {:s}".format(str(card), dest_pile, ', '.join([str(c) for c in t.needs()])))
            
            c = self.waste.draw()
            t.give([c])
        elif dest == CardLocation.FOUNDATION:
            card = self.waste.top
            # get the foundation to move it to
            f = self.foundations[card.suit]
            expected = f.needs()
            if card != expected:
                raise RulesError("Cannot add {:s} to {:s} foundation pile; legal cards are {:s}".format(str(card), f.suit.name, str(expected)))
            
            c = self.waste.draw()
            f.add(c)
        else:
            raise RulesError("Waste pile cards may only be moved to a tableau or foundation pile")
        
    def move_foundation_card(self, source_suit: Suit, dest: CardLocation, dest_pile: int):
        if dest == CardLocation.TABLEAU:
            if dest_pile is None:
                raise ValueError("Destination pile is required for moves to tableau")
            if dest_pile < 0 or dest_pile >= len(self.tableau):
                raise ValueError("Invalid destination tableau pile")
            
             = self.tableau[dest_pile]

            if card not in t.needs():
                raise RulesError("Cannot add {:s} to tableau[{:d}]; legal cards are {:s}".format(str(card), dest_pile, ', '.join([str(c) for c in t.needs()])))
            
            c = self.waste.draw()
            t.give([c])
        elif dest == CardLocation.WASTE:
            raise RulesError("Cannot move cards from foundation to waste")
        elif dest == CardLocation.FOUNDATION:
            raise RulesError("Cannot move cards from foundation to foundation")
        else:
            raise ValueError("Invalid destination location")
            
            


    @property
    def running(self) -> bool:
        # win cond is here - all cards in foundation piles
        return not all([len(cs) == 13 for cs in self.foundation.values()])

    @property
    def hand(self) -> Deck:
        # return the currently viewed card(s) from the waste pile. Only the top
        # card is playable.
        return Deck(self.waste.top_n(self.draw_count, or_fewer=True))

    @property
    def rules(self) -> dict:
        return {
            'draw_count': self.draw_count,
            'stock_pass_limit': self.stock_pass_limit,
            'deck': {
                'type': 'random' if self.random_deck else 'fixed',
                'cards': [str(c) for c in self.starting_deck.cards]
            },
            'num_piles': len(self.tableau)
        }
    
    @property
    def state(self) -> dict:
        # come back to this; tableau needs supplementary info
        return {
            'tableau': [list(p.shown) for p in self.tableau],
            'foundation': {s.name: list(self.foundations[s].cards) for s in self.foundations},
            'stock': len(self.stock),
            'waste': len(self.waste)
        }
    
    @property
    def max_players(self) -> int:
        return 1
    
    @property
    def min_players(self) -> int:
        return 1
    