from ..card import Card, Suit
from ..deck import Deck


class Pile:
    """One of seven piles of cards in Klondike Solitaire"""

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
                self.hidden = cards[1:-1]

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
            
        self.shown = self.shown + cards
    
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
    

# moves possible in Klondike Solitaire:
# - draw from stock to waste (or flip over the waste pile, if it is empty)
# - add to tableau, either 1 from waste top, 1 from foundation pile, or other tableau.
# - add to foundation, either from waste top or tableau pile.


class Move:
    def __init__(self, source: str, dest: str, count: int):
        self.source = source
        self.dest = dest
        self.count = count


class Game:
    """
    The state of a game of Klondike Solitaire
    """

    def __init__(self, draw_count: int=1, stock_pass_limit: int=0, deck: Deck | None=None, num_piles: int=7):
        self.random_deck: bool = deck is None
        if deck is None:
            deck = Deck()
            deck.shuffle()
        
        self.starting_deck = deck
        self.draw_count = draw_count
        self.stock_pass_limit = stock_pass_limit
        self.tableau: list[Pile] = []
        self.foundation: dict[Suit, list[Card]] = {s: [] for s in Suit}
        self.stock: Deck = deck
        self.waste: Deck = Deck(cards=[])

        # build the tableau
        for pile_idx in range(num_piles):
            p = Pile(self.stock.draw_n(pile_idx+1))
            self.tableau.append(p)

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
        return {
            'tableau': [list(p.shown) for p in self.tableau],
            'foundation': {s.name: list(cs) for s, cs in self.foundation.items()},
            'stock': len(self.stock),
            'waste': len(self.waste)
        }