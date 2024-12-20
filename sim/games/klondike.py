from ..card import Card, Suit, Rank
from ..deck import Deck
from . import RulesError, Game as BaseGame, Player as BasePlayer, Result, Rules as BaseRules
from .. import cio, UndoAction

from enum import Enum, IntEnum, auto

from typing import Callable


class LocationType(Enum):
    TABLEAU = auto()
    FOUNDATION = auto()
    WASTE = auto()

    def __str__(self) -> str:
        return self.name.title()

class Location:
    def __init__(self, type: LocationType):
        self.type = type

    def __str__(self) -> str:
        return str(self.type)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Location):
            return False
        return self.type == other.type


class LocationList(list[Location]):
    def has_type(self, t: LocationType) -> bool:
        for loc in self:
            if loc.type == t:
                return True
        return False
    
    def where(self, type: Location | str | LocationType | None=None) -> 'LocationList':
        no_filters = type is None
            
        if type is not None:
            if isinstance(type, str):
                type = LocationType[type.upper()] 
            elif isinstance(type, Location):
                type = type.type
            elif not isinstance(type, LocationType):
                raise ValueError("Invalid type value, must be Location, str, or LocationType")

        def cond(loc: Location) -> bool:
            if no_filters:
                return True
            else:
                if type is not None and loc.type != type:
                    return False
                return True

        # filter it by cond
        matches = LocationList()
        for loc in self:
            if cond(loc):
                matches.append(loc)

        return matches
    
    def len(self) -> int:
        return len(self)
    
class CardList(list[Card]):
    def where(self, color: None | Card | str | Suit=None, suit: None | Card | str | Suit=None, rank: None | Card | str | int | Rank=None) -> 'CardList':
        no_filters = color is None and suit is None and rank is None

        if color is not None:
            if isinstance(color, str):
                if color.lower() == "black":
                    color = "black"
                elif color.lower() == "red":
                    color = "red"
                else:
                    raise ValueError("Invalid color string")
            elif isinstance(color, Card):
                color = color.color()
            elif isinstance(color, Suit):
                color = color.color()
            else:
                raise ValueError("Invalid color value, must be Card, str, or Suit")
            
        if suit is not None:
            if isinstance(suit, str):
                suit = Suit.parse(suit)
            elif isinstance(suit, Card):
                suit = suit.suit
            elif not isinstance(suit, Suit):
                raise ValueError("Invalid suit value, must be Card, str, or Suit")
            
        if rank is not None:
            if isinstance(rank, str):
                rank = Rank.parse(rank)
            elif isinstance(rank, int):
                # this is fine, actually, we can directly compare
                pass
            elif isinstance(rank, Card):
                rank = rank.rank
            elif not isinstance(rank, Rank):
                raise ValueError("Invalid rank value, must be Card, str, int, or Rank")

        def cond(c: Card) -> bool:
            if no_filters:
                return True
            else:
                if color is not None and c.color() != color:
                    return False
                if suit is not None and c.suit != suit:
                    return False
                if rank is not None and c.rank != rank:
                    return False
                return True

        # filter it by cond
        matches = CardList()
        for c in self:
            if cond(c):
                matches.append(c)

        return matches
    
    def len(self) -> int:
        return len(self)


class Foundation:
    """
    Ultimate destination for all cards of a given suit. Index -1 is the bottom of
    the pile, and index 0 is the top.
    """

    def __init__(self, suit: Suit):
        self.suit = suit
        self.cards: CardList = CardList()

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
            return Card(Rank.ACE, self.suit)
        elif len(self.cards) == Rank.KING.value:
            return None
        
        return Card(self.cards[0].rank + 1, self.suit)

    def remove(self) -> Card:
        if len(self.cards) == 0:
            raise ValueError("Foundation is empty")
        c = self.cards[0]
        del self.cards[0]
        return c
    
    # TODO: make top be a property or make Deck.top be a method. Same for Pile.
    def top(self) -> Card | None:
        if len(self.cards) == 0:
            return None
        return self.cards[0]
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Foundation):
            return False
        return self.suit == other.suit and self.cards == other.cards
    
    def clone(self) -> 'Foundation':
        f = Foundation(self.suit)
        f.cards = list([c.clone() for c in self.cards])
        return f


class Pile:
    """A tableau pile of cards in Klondike Solitaire"""

    def __init__(self, cards: list[Card] | None=None):
        """
        Create a new pile that contains the given cards, with the last card at
        the bottom of the pile and the first card at the top. The first card
        will immediately be turned over and added to the revealed cards on top
        of the pile; the rest remain unrevealed and not known to the player
        unless Thoughtful Klondike rules are in effect.
        """
        if cards is None:
            cards = []
        
        cards = list(cards)

        self.shown: CardList = CardList()
        self.hidden: CardList = CardList()

        if len(cards) > 0:
            self.shown = [cards[0]]
            if len(cards) > 1:
                self.hidden = cards[1:]

    def __len__(self) -> int:
        return len(self.shown + self.hidden)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Pile):
            return False
        return self.shown == other.shown and self.hidden == other.hidden
    
    def __getitem__(self, key) -> Card:
        return (self.shown + self.hidden)[key]
    
    def take(self, count: int) -> CardList:
        """
        Remove the top count cards from the pile's shown cards and return them.
        If there are fewer than count cards in the pile's shown cards, raises a
        ValueError. Count must be at least 1.
        """
        if count < 1:
            raise ValueError("Count must be at least 1")
        if count > len(self.shown):
            raise ValueError("Cannot take {:d} cards; only {:d} cards are revealed".format(count, len(self.shown)))
        cards = self.shown[:count]
        self.shown = self.shown[count:]
        if len(self.shown) == 0 and len(self.hidden) > 0:
            self.shown = [self.hidden[0]]
            del self.hidden[0]
        return CardList(cards)

    def needs(self) -> CardList:
        """
        Return a list of all cards that could be used to continue building this
        tableau. This will either be all four kings (if the pile is empty), the
        two cards of the opposite color that could be placed on top of the pile,
        or an empty list if no cards could be placed on the pile (if it
        currently has an Ace on top).
        """
        n = []
        if len(self.shown) == 0:
            n = [Card(Rank.KING, s) for s in Suit]
        elif self.shown[0] == Rank.ACE:
            n = []
        else:
            t = self.top()
            if t.is_black():
                n = [Card(t.rank - 1, Suit.DIAMONDS), Card(t.rank - 1, Suit.HEARTS)]
            else:
                n = [Card(t.rank - 1, Suit.CLUBS), Card(t.rank - 1, Suit.SPADES)]
        
        return CardList(n)
    
    def give(self, cards: list[Card]):
        """Add the given cards to the top of the revealed section of the pile.
        This is only allowed if the given cards are in alternating colors and
        descending ranks from the top card of the pile. Both will be checked.
        """

        # validate the cards being given first
        bot_given = cards[-1]
        last_card = bot_given

        if len(cards) > 1:
            for c in reversed(cards[0:-1]):
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
                self.shown = [self.hidden[0]]
                del self.hidden[0]
                return self.shown[0]

            return None
        return self.shown[0]
        
    def empty(self) -> bool:
        """Return True if this pile is empty, False otherwise"""
        return len(self.shown) == 0 and len(self.hidden) == 0
    
    def clone(self) -> 'Pile':
        p = Pile([])
        p.shown = list([c.clone() for c in self.shown])
        p.hidden = list([c.clone() for c in self.hidden])
        return p


class TurnType(IntEnum):
    DRAW = auto()
    MOVE_ONE = auto()
    MOVE_TABLEAU_STACK = auto()

    def __str__(self) -> str:
        return self.name.title()
    
    def __lt__(self, other: 'TurnType') -> bool:
        return self.value < other.value



class TableauPosition(Location):
    def __init__(self, pile: int):
        super().__init__(LocationType.TABLEAU)
        self.pile = pile

    def __str__(self):
        return f"T{self.pile}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TableauPosition):
            return False
        if not super().__eq__(other):
            return False
        return self.pile == other.pile

class WastePosition(Location):
    def __init__(self):
        super().__init__(LocationType.WASTE)

    def __str__(self):
        return "waste pile"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, WastePosition):
            return False
        return super().__eq__(other)


class FoundationPosition(Location):
    def __init__(self, suit: Suit):
        super().__init__(LocationType.FOUNDATION)
        self.suit = suit

    def __str__(self):
        return f"{self.suit.name.lower()} pile"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, FoundationPosition):
            return False
        if not super().__eq__(other):
            return False
        return self.suit == other.suit


class Action:
    def __init__(self, type: TurnType):
        self.type = type

    def __str__(self) -> str:
        return str(self.type)
    
    def __lt__(self, other: 'Action') -> bool:
        if not isinstance(other, Action):
            return False
        return self.type < other.type

    def __eq__(self, other) -> bool:
        if not isinstance(other, Action):
            return False
        return self.type == other.type

    def __hash__(self) -> int:
        return hash(self.type)


class DrawAction(Action):
    def __init__(self):
        super().__init__(TurnType.DRAW)

    def __str__(self):
        return "Draw a card"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DrawAction):
            return False
        return super().__eq__(other)

class MoveTableauStackAction(Action):
    def __init__(self, source_pile: int, dest_pile: int, count: int):
        super().__init__(TurnType.MOVE_TABLEAU_STACK)

        if source_pile == dest_pile:
            raise ValueError("Source and destination piles must be different")
        
        if source_pile < 0 or dest_pile < 0:
            raise ValueError("Pile indices must be non-negative")
        
        if count < 1:
            raise ValueError("Stack must have count of at least 1")

        self.source_pile = source_pile
        self.dest_pile = dest_pile
        self.count = count

    @property
    def source(self) -> Location:
        return TableauPosition(self.source_pile)
    
    @property
    def dest(self) -> Location:
        return TableauPosition(self.dest_pile)

    def __str__(self):
        return "Move T{:d} -> T{:d}, stack of {:d}".format(self.source_pile, self.dest_pile, self.count)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, MoveTableauStackAction):
            return False
        if not super().__eq__(other):
            return False
        if self.source_pile != other.source_pile:
            return False
        if self.dest_pile != other.dest_pile:
            return False
        if self.count != other.count:
            return False
        return True
    
    def splits_stack(self, state: 'State') -> bool:
        """
        Return True if this move splits a stack in the source pile, False
        otherwise. While this is not a rules violation, if the ONLY possible
        moves are to split a stack, and there is no foundation moves that would
        reveal, and the deck has no playable cards, the game is unwinnable in
        that state.
        """
        source_pile = state.tableau[self.source_pile]
        return len(source_pile.shown) > self.count


class MoveOneAction(Action):
    def __init__(self, source: Location, dest: Location):
        super().__init__(TurnType.MOVE_ONE)
        self.source = source
        self.dest = dest

        # TODO: make all these checks in rules validation in game engine as
        # well.

        if self.dest.type == self.source.type:
            # only legal same-location would be tableau to tableau move, which
            # is handled by MoveStackAction
            if self.dest.type == LocationType.TABLEAU:
                raise ValueError("Use MoveTableauStackAction to move cards between tableau piles")
            raise ValueError("Source and destination locations must be different")
        
        # moving to waste is always invalid
        elif self.dest.type == LocationType.WASTE:
            raise ValueError("Cannot move card to waste pile")
        
    def __str__(self):
        return f"Move {self.source} card to {self.dest}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, MoveOneAction):
            return False
        if not super().__eq__(other):
            return False
        if self.source != other.source:
            return False
        if self.dest != other.dest:
            return False
        return True

class State:
    def __init__(self, tableau: list[Pile], foundations: dict[Suit, Foundation], stock: Deck, waste: Deck, current_stock_pass: int, pass_limit: int=0, draw_count: int=0):
        self.tableau = tableau
        self.foundations = foundations
        self.stock = stock
        self.waste = waste
        self.current_stock_pass = current_stock_pass
        self.pass_limit = pass_limit
        self.draw_count = draw_count

    def meaningfully_increases_dests_for(self, c: Card | list[Card], where_dest_type: LocationType | Location | str | None=None, playable_from_prior: bool=False) -> bool:
        playable_dests = self.playable_destinations(c)
        if where_dest_type is not None:
            playable_dests = playable_dests.where(where_dest_type)
        playable_to_count = playable_dests.len()
        playable_count = 0

        cards = c
        if isinstance(c, Card):
            cards = [c]
        
        for c in cards:
            playable_count += self.find_playable_singles(color=c, rank=c, in_waste=False).len()
            playable_count += self.accessible_stock_cards.where(color=c, rank=c).len()
        
        if playable_from_prior:
            playable_count -= 1
        
        return playable_to_count <= playable_count
    
    
    def has_useful_moves(self) -> bool:
        """
        Returns None if it cannot be determined due to passes.
        """

        if not (self.current_stock_pass > 1 or (len(self.stock) == 0 and self.pass_limit != 1)):
            return None
        
        moves = self.legal_moves()
    
        if len(moves) == 0:
            return False
        
        # definition of no useful moves remaining using only knowledge that
        # player would have, generalized to multiple decks. NOT generalized
        # to 1-pass limit over stock; this relies on knowledge of stock,
        # which would be impossible to gain as it depends on having been
        # through it at least once.

        single_card_moves: list[MoveOneAction] = [m for m in moves if m.type == TurnType.MOVE_ONE]
        stack_moves: list[MoveTableauStackAction] = [m for m in moves if m.type == TurnType.MOVE_TABLEAU_STACK]

        from_foundation_moves = [m for m in single_card_moves if m.source.type == LocationType.FOUNDATION]
        tableau_to_foundation_moves = [m for m in single_card_moves if m.source.type == LocationType.TABLEAU and m.dest.type == LocationType.FOUNDATION]
        full_stack_moves = [m for m in stack_moves if not m.splits_stack(self)]
        split_stack_moves = [m for m in stack_moves if m.splits_stack(self)]

        has_useful_moves = False

        # - For all moves from a foundation, it is not true that:
        #   - The move is to a tableau pile
        #   - AND the card being moved is not an Ace, as pulling an ace from
        #     a foundation is never useful.
        #   - AND:
        #     - The move would reveal a card which is playable to tableau.
        #     - OR after the card is moved, the number of playable-to cards
        #       of that card's color and rank is less than or equal to the
        #       number of then-playable opposite color and -1 rank cards in
        #       stock or tableau or foundation.
        for m in from_foundation_moves:

            # Check that the move is to a tableau pile and the card is not
            # an Ace.

            moved_card = self.foundation_from_location(m.source).top()

            if m.dest.type == LocationType.TABLEAU and moved_card.rank != Rank.ACE:
                st_after_move = self.after(m)

                # did it reveal another card playable to tableau from same
                # foundation?
                pos: FoundationPosition = m.source
                revealed_card = st_after_move.foundation_from_location(pos).top()
                if st_after_move.playable_destinations(revealed_card).has_type(LocationType.TABLEAU):
                    has_useful_moves = True
                    break

                # otherwise, would the move meaningfully increase the number
                # of playable-to cards of that rank and color?
                opp = Card(moved_card.rank - 1, Suit.CLUBS if moved_card.suit.red() else Suit.DIAMONDS)
                if st_after_move.meaningfully_increases_dests_for(opp):
                    has_useful_moves = True
                    break

        if has_useful_moves:
            return True
        
        # - AND For all moves to foundation from tableau, it is not true that:
        #   - the move reveals a hidden card
        #   - OR the move reveals a non-hidden card such that:
        #     - revealed card is itself is playable to foundation
        #     - OR reaveled card is playable to another stack
        #       - AND the revealed card is not a king on an empty.
        #     - OR game state is changed such that the total number of cards
        #       of revealed card's color and rank that can be played to
        #       would be less than equal to the number of currently playable
        #       opposite color and -1 rank cards in stock or tableau or
        #       foundation.
        #   - OR the move changes game state such that the number of playable-to
        #     foundation piles of that card's exact rank and suit would be less
        #     than/equal to the number of currently playable cards of the same
        #     suit with rank +1 in stock or tableau. For simplicity,
        #     we assume that a move from foundation-foundation would itself always be
        #     a useless move, as the overall game state wouldn't advance, so
        #     we do not consider it.
        for m in tableau_to_foundation_moves:
            t = self.tableau_from_location(m.source)

            # does it reveal a hidden card? it will if it's the last
            # non-hidden card from the tableau, and tableau has at least one
            # hidden card. don't check for an empty-cell reveal; that is
            # handled by another check.
            if len(t.hidden) > 0 and len(t.shown) == 1:
                has_useful_moves = True
                break

            st_after_move = self.after(m)

            # does it reveal a non-hidden card...
            if len(t.shown) > 1:
                revealed_card = t.shown[1]
                playable_dests = st_after_move.playable_destinations(revealed_card)

                #  ...that is playable to foundation?
                if playable_dests.has_type(LocationType.FOUNDATION):
                    has_useful_moves = True
                    break
                
                # ...or that is playable to another stack and is not the king on an empty?
                elif (not len(t.hidden) == 0 or not revealed_card.rank == Rank.KING) and playable_dests.has_type(LocationType.TABLEAU):
                    has_useful_moves = True
                    break

                # otherwise, would the move meaningfully increase the number
                # of playable-to cards of revealed cards rank and color?
                # TODO: modularize this? at least two are identical, there
                # is one in block above
                opp = Card(moved_card.rank - 1, Suit.CLUBS if moved_card.suit.red() else Suit.DIAMONDS)
                if st_after_move.meaningfully_increases_dests_for(opp):
                    has_useful_moves = True
                    break

            # otherwise, would the move meaningfully increase the number of
            # playable-to foundation piles of moved card's rank and suit?
            next = Card(t.top().rank + 1, t.top().suit)
            if st_after_move.meaningfully_increases_dests_for(next, where_dest_type=LocationType.FOUNDATION):
                has_useful_moves = True
                break

        if has_useful_moves:
            return True

        # - AND For all full-stack moves from tableau, it is not true that
        #   - the move reveals a hidden card
        #   - OR the move reveals a blank space such that the total number of
        #     blank spaces would be less than/equal to the number of currently
        #     playable kings in stock or tableau or foundation, AND the top of
        #     stack is not a king.
        for m in full_stack_moves:
            t = self.tableau_from_location(m.source)
            st_after_move = self.after(m)

            # does it reveal a hidden card? it will if there's anything
            # under it
            if len(t.hidden) > 0:
                has_useful_moves = True
                break

            # or, does it reveal a space that lets more kings play, and it
            # isn't itself a king?
            elif t.top().rank != Rank.KING and st_after_move.meaningfully_increases_dests_for(Card.kings()):
                has_useful_moves = True
                break

        if has_useful_moves:
            return True

        # - AND For all non-full-stack moves from tableau, it is not true that:
        #   - the move reveals a non-hidden card such that the total number of that
        #     particular rank and color of card that can be played to would be
        #     less than/equal to the number of currently playable opposite color
        #     and -1 rank cards in stock or tableau or foundation, excluding the
        #     top of the moved stack.
        #   - OR the move reveals a non-hidden card which:
        #     - Itself is playable to foundation
        #     - OR is playable to another stack
        #       - AND the revealed card is not a king on an empty.
        for m in split_stack_moves:
            t = self.tableau_from_location(m.source)
            st_after_move = self.after(m)
            t_after_move = st_after_move.tableau_from_location(m.source)
            revealed_card = t_after_move.top()

            # does it reveal a card that would increase playable-to slots?
            opp = Card(moved_card.rank - 1, Suit.CLUBS if moved_card.suit.red() else Suit.DIAMONDS)
            if st_after_move.meaningfully_increases_dests_for(opp, playable_from_prior=True):
                has_useful_moves = True
                break

            playable_dests = st_after_move.playable_destinations(revealed_card)

            # does it reveal a card that is playable to a foundation?
            if playable_dests.has_type(LocationType.FOUNDATION):
                has_useful_moves = True
                break

            # otherwise, does it reveal a non-king on an empty slot that is
            # playable to another stack?
            if (not len(t_after_move.hidden) == 0 or not revealed_card.rank == Rank.KING) and playable_dests.has_type(LocationType.TABLEAU):
                has_useful_moves = True
                break

        if has_useful_moves:
            return True

        # - AND For all accessible cards from stock, it is not true that:
        #   - it is playable to tableau or foundation
        for c in self.accessible_stock_cards:
            if self.playable_destinations(c).len() > 0:
                has_useful_moves = True
                break

        return has_useful_moves

    @property
    def remaining_stock_flips(self) -> int:
        return self.pass_limit - self.current_stock_pass if self.pass_limit > 0 else -1
    
    @property
    def accessible_stock_cards(self) -> CardList:
        """
        Return the stock cards that the player could currently access, either by
        drawing to it via zero or one flip or by it being the current face-up
        card. Note that this will only include cards the player has drawn at
        least once.
        """

        accessibles = CardList()

        # Include the card currently in the waste pile, if there is one:
        if len(self.waste) > 0:
            accessibles.append(self.waste.top)

        if len(self.stock) > 0 and self.current_stock_pass > 1:
            # Include every nth card remaining in stock, where n is the draw_count:
            for i in range(0, len(self.stock), self.draw_count):
                idx = i + self.draw_count - 1
                if idx >= len(self.stock):
                    idx = len(self.stock) - 1
                accessibles.append(self.stock[idx])

        # if there are waste-pile cards under the top one that could be revealed
        # with a flip (DEFINED AS len(waste) > draw_count),
        # we need to also
        # simulate flipping the waste pile and checking cards accessible that
        # way.
        if len(self.waste) >= self.draw_count and (self.pass_limit < 1 or self.remaining_stock_flips > 0):
            original_top = len(self.waste) - 1
            next_waste = self.waste.clone()

            shifted_waste = len(self.waste) % self.draw_count != 0
            if shifted_waste and self.current_stock_pass > 1 and len(self.stock) > 0:
                # we have seen the remainder of stock and the flip would shift
                # things so add all cards that would become accessible on next
                # flip, including rest of stock.
                stock_copy = self.stock.clone()
        
                for _ in range(self.draw_count):
                    if len(stock_copy) == 0:
                        break
                    c = stock_copy.draw()
                    next_waste.insert(0, c)

            next_waste.flip()
            next_stock = next_waste
            # only go up to draw count - 1 because we don't want to include the
            # bottom stock card twice.
            for i in range(0, len(next_stock)-self.draw_count, self.draw_count):
                idx = i + self.draw_count - 1
                if idx == original_top:
                    # don't include the top card twice
                    continue
                accessibles.append(next_stock[idx])
            
            # already did last-card check, don't need to do so again.

        return accessibles
    
    def foundation_from_location(self, loc: FoundationPosition) -> Foundation:
        """
        Not yet generalized for multiple locations, may be updated in future.
        """
        if loc.type != LocationType.FOUNDATION:
            raise ValueError("Location must be a foundation")
        
        if loc.suit not in self.foundations:
            raise ValueError("No foundation pile for suit {!s}".format(loc.suit))
        
        return self.foundations[loc.suit].clone()
    
    def tableau_from_location(self, loc: TableauPosition) -> Pile:
        if loc.type != LocationType.TABLEAU:
            raise ValueError("Location must be a tableau pile")
        
        if loc.pile < 0 or loc.pile >= len(self.tableau):
            raise ValueError("No tableau pile at index {:d}".format(loc.pile))
        
        return self.tableau[loc.pile].clone()
        
    def play_area_from_location(self, loc: Location) -> Pile | Foundation | tuple[Deck, Deck]:
        """
        Returns the play area corresponding to the given location. Depending on
        loc's type, this will either be a tableau Pile, a Foundation, or a tuple
        containing the current waste and stock pile in that order.
        """
        if loc.type == LocationType.TABLEAU:
            return self.tableau_from_location(loc)
        elif loc.type == LocationType.FOUNDATION:
            return self.foundation_from_location(loc)
        elif loc.type == LocationType.WASTE:
            return (self.waste, self.stock)
        else:
            raise ValueError("Invalid location type")

    def after(self, action: Action) -> 'State':
        """
        Returns a copy of what State this one will become if the given action is
        taken.
        """
        g = Game(draw_count=self.draw_count, stock_pass_limit=self.pass_limit, deck=None, num_piles=len(self.tableau))
        g.tableau = list(p.clone() for p in self.tableau)
        g.foundations = {s: f.clone() for s, f in self.foundations.items()}
        g.waste = self.waste.clone()
        g.stock = self.stock.clone()
        g.current_stock_pass = self.current_stock_pass
        return g.state_with_turn_applied(action)
    
    def clone(self) -> 'State':
        return State(
            tableau=[t.clone() for t in self.tableau],
            foundations={s: f.clone() for s, f in self.foundations.items()},
            stock=self.stock.clone(),
            waste=self.waste.clone(),
            current_stock_pass=self.current_stock_pass,
            pass_limit=self.pass_limit,
            draw_count=self.draw_count,
        )
    
    def playable_destinations(self, c: Card) -> LocationList:
        """
        Return a list of all locations where the given card could be legally
        played to in this state.
        """
        locs = LocationList()
        
        # foundation piles
        for s, f in self.foundations.items():
            if c == f.needs():
                locs.append(FoundationPosition(s))
        
        # tableau piles
        for i, t in enumerate(self.tableau):
            if c in t.needs():
                locs.append(TableauPosition(i))
        
        return locs
    
    def top_of(self, loc: Location) -> Card | None:
        """
        Return the top card at the given location, or None if there is no card
        there.
        """
        if loc.type == LocationType.TABLEAU:
            t = self.tableau_from_location(loc)
            return t.top()
        elif loc.type == LocationType.FOUNDATION:
            f = self.foundation_from_location(loc)
            return f.top()
        elif loc.type == LocationType.WASTE:
            return self.waste.top
        else:
            raise ValueError("Invalid location type")
    
    def find_playable_singles(self, color: None | Card | str | Suit=None, suit: None | Card | str | Suit=None, rank: None | Card | str | int | Rank=None, in_foundations: bool=True, in_tableau: bool=True, in_waste: bool=True) -> LocationList:
        """
        Return the locations of all cards that are currently playable as a
        single card (i.e. excluding the backs of multi-card stacks) that match
        the given conditions (color, suit, and/or rank). If no conditions are
        given, all playable single card locations are returned.

        Note that if in_waste is enabled, it will check only the top card in
        the waste pile, and will not consider any further ones.
        """
        no_filters = color is None and suit is None and rank is None

        if color is not None:
            if isinstance(color, str):
                if color.lower() == "black":
                    color = "black"
                elif color.lower() == "red":
                    color = "red"
                else:
                    raise ValueError("Invalid color string")
            elif isinstance(color, Card):
                color = color.color()
            elif isinstance(color, Suit):
                color = color.color()
            else:
                raise ValueError("Invalid color value, must be Card, str, or Suit")
            
        if suit is not None:
            if isinstance(suit, str):
                suit = Suit.parse(suit)
            elif isinstance(suit, Card):
                suit = suit.suit
            elif not isinstance(suit, Suit):
                raise ValueError("Invalid suit value, must be Card, str, or Suit")
            
        if rank is not None:
            if isinstance(rank, str):
                rank = Rank.parse(rank)
            elif isinstance(rank, int):
                # this is fine, actually, we can directly compare
                pass
            elif isinstance(rank, Card):
                rank = rank.rank
            elif not isinstance(rank, Rank):
                raise ValueError("Invalid rank value, must be Card, str, int, or Rank")

        def cond(c: Card) -> bool:
            if no_filters:
                return True
            else:
                if color is not None and c.color() != color:
                    return False
                if suit is not None and c.suit != suit:
                    return False
                if rank is not None and c.rank != rank:
                    return False
                return True

        locs = LocationList()

        # build list of all possible locations then filter by condition

        # foundation piles
        if in_foundations:
            for s, _ in self.foundations.items():
                locs.append(FoundationPosition(s))

        # tableau piles
        if in_tableau:
            for i in range(len(self.tableau)):
                locs.append(TableauPosition(i))

        # waste pile
        if in_waste:
            locs.append(WastePosition())

        # filter it by cond
        matches = LocationList()
        for loc in locs:
            c = self.top_of(loc)
            if c is not None and cond(c):
                matches.append(loc)

        return matches
    
    def board(self, reveal_hidden=False) -> str:
        """
        Return a string representation of the current state of the board. This
        is useful for debugging and for displaying the current state of the game
        to a human player.
        """

        card_width = 2
        border_width = 1
        empty_char = '░'
        back_char = '▒'
        border_char = '|'

        board = ''

        # add foundation piles
        foundation_offset = (card_width + border_width) * 3
        board += ' ' * foundation_offset
        for s in Suit:
            f = self.foundations[s]
            if f.top() is None:
                board += empty_char + s.short()
            else:
                board += str(f.top())
            board += ' ' * border_width
        board += '\n'

        # add a blank line
        board += '\n'

        border = border_char * border_width
        back = back_char * card_width
        empty_slot = empty_char * card_width
        for i in range(len(self.tableau)):
            board += "T" + str(i) + " "
        board += '\n'
        # add tableau piles, smallest to largest, vertically
        tallest_pile = max([len(t) for t in self.tableau])
        for i in range(tallest_pile):
            for t in self.tableau:
                if len(t) <= i:
                    if i == 0:
                        board += empty_slot
                    else:
                        board += ' ' * card_width
                else:
                    # are we on a hidden one or displayed one? we want to start
                    # at the back, so start at hidden (if present)
                    if i >= len(t.hidden):
                        # we are actually on a SHOWN card
                        shown_index = i - len(t.hidden)
                        board += str(t.shown[-(shown_index+1)])
                    else:
                        # we are on a hidden card. easy.
                        if reveal_hidden:
                            board += str(t.hidden[-(i+1)])
                        else:
                            board += back
                board += ' '
            board += '\n'

        # empty line
        board += '\n'

        # stock and waste
        board += '|'
        if len(self.stock) > 0:
            board += str(len(self.stock)).zfill(2)
        else:
            board += empty_slot
        board += '| '
        disp_waste = self.draw_count
        if disp_waste > len(self.waste):
            disp_waste = len(self.waste)
        
        board += "TOP:"
        for i, c in enumerate(self.waste.top_n(disp_waste, or_fewer=True)):
            board += str(c)
            if i+1 < disp_waste:
                board += border
        board += '\n'

        if self.has_useful_moves() is False:
            board += "(NO MOVES DETECTED)\n"

        return board

    def legal_moves(self) -> list[Action]:
        """
        Return a list of all legal moves that can be made in the current state.
        """
        moves = []

        # add draw action
        if len(self.stock) > 0 or (len(self.waste) > 0 and (self.pass_limit < 1 or self.current_stock_pass < self.pass_limit)):
            moves.append(DrawAction())

        # can we move from waste pile? add that one next if so
        if len(self.waste) > 0:
            card = self.waste.top

            # to tableau
            for i, dest in enumerate(self.tableau):
                if card in dest.needs():
                    moves.append(MoveOneAction(WastePosition(), TableauPosition(i)))

            # to foundation
            for s in Suit:
                if card == self.foundations[s].needs():
                    moves.append(MoveOneAction(WastePosition(), FoundationPosition(s)))
        
        # check tableau piles for single-card moves to foundation
        for idx, source in enumerate(self.tableau):
            if len(source.shown) == 0:
                continue
            for s in Suit:
                if source.shown[0] == self.foundations[s].needs():
                    moves.append(MoveOneAction(TableauPosition(idx), FoundationPosition(s)))
        
        
        # check all tableau piles for stack moves. iterate on destinations bc
        # piles can legally take one of up to four cards, usually two, whereas
        # piles can give any number of cards up to their revealed stack size.
        tableau_moves = list()
        for idx, dest in enumerate(self.tableau):
            legal_stack_bots = dest.needs()

            # now check if any other tableau pile has a stack with a legal card
            # at any position.
            for from_idx, source in enumerate(self.tableau):
                if from_idx == idx:
                    continue

                for card_idx, candidate in enumerate(source.shown):
                    if candidate in legal_stack_bots:
                        tableau_moves.append(MoveTableauStackAction(from_idx, idx, card_idx+1))
                        # not possible to have multiple moves from the same
                        # source in Klondike, no need to check the rest
                        break

        # sort them so we actually get in FROM order first, followed by TO
        tableau_moves.sort(key=lambda m: (m.source_pile, m.dest_pile))
        moves.extend(tableau_moves)

        # check foundation piles for moves
        for s in Suit:
            f = self.foundations[s]
            if len(f) == 0:
                continue
            card = f.top()

            for i, dest in enumerate(self.tableau):
                if card in dest.needs():
                    moves.append(MoveOneAction(FoundationPosition(s), TableauPosition(i)))
        
        return moves
    

class Rules(BaseRules):
    def __init__(self, draw_count: int, stock_pass_limit: int, starting_deck: Deck, random_deck: bool, num_piles: int):
        super().__init__(Game)
        self.draw_count = draw_count
        self.stock_pass_limit = stock_pass_limit
        self.starting_deck = starting_deck
        self.random_deck = random_deck
        self.num_piles = num_piles
        
        deck_info = self.get('deck', None)
        self._starting_deck = deck_info.get('cards', None) if deck_info is not None else None
        self._random_deck = deck_info.get('type', 'random') == 'random' if deck_info is not None else True
        self._num_piles = self.get('num_piles', 7)

    def as_dict(self) -> dict:
        return {
            'draw_count': self.draw_count,
            'stock_pass_limit': self.stock_pass_limit,
            'deck': {
                'type': 'random' if self.random_deck else 'fixed',
                'cards': [str(c) for c in self.starting_deck]
            },
            'num_piles': len(self.tableau)
        }


class Game(BaseGame):
    """
    The state of a game of Klondike Solitaire
    """

    def __init__(self, draw_count: int=1, stock_pass_limit: int=0, deck: Deck | None=None, num_piles: int=7):
        self.random_deck: bool = deck is None
        if deck is None:
            deck = Deck()
            deck.shuffle()
        
        self.starting_deck = list(deck.cards)
        self.draw_count = draw_count
        self.stock_pass_limit = stock_pass_limit
        self.current_stock_pass = 1
        self.tableau: list[Pile] = []
        self.foundations: dict[Suit, Foundation] = {s: Foundation(s) for s in Suit}
        self.stock: Deck = deck
        self.waste: Deck = Deck(cards=[])
        self.history: list[State] = []

        # build the tableau
        for pile_idx in range(num_piles):
            p = Pile(reversed(self.stock.draw_n(pile_idx+1)))
            self.tableau.append(p)
        
        self.history.append(self.state)

    @classmethod
    def from_rules(cls, rules: Rules) -> 'Game':
        g = Game(draw_count=rules.draw_count, stock_pass_limit=rules.stock_pass_limit, deck=rules.starting_deck, num_piles=rules.num_piles)
        g.random_deck = rules.random_deck
        return g

    def take_turn(self, player: int, action: Action):
        """
        Performs the given turn, if it is legal. If not, a RulesError will be
        raised. If there is a problem with an argument, a ValueError will be
        raised.
        """
        if player != 0:
            raise RulesError("Klondike Solitaire is a single-player game; player index must be 0")
        
        if action.type == TurnType.DRAW:
            if not isinstance(action, DrawAction):
                raise ValueError("DrawAction required for DRAW turn type")
            
            self.draw_stock()
        elif action.type == TurnType.MOVE_TABLEAU_STACK:
            if not isinstance(action, MoveTableauStackAction):
                raise ValueError("MoveTableauStackAction required for MOVE_TABLEAU_STACK turn type")
            
            self.move_tableau_stack(action.source_pile, action.dest_pile, action.count)
        elif action.type == TurnType.MOVE_ONE:
            if not isinstance(action, MoveOneAction):
                raise ValueError("MoveOneAction required for MOVE_ONE turn type")
            
            act: MoveOneAction = action
            if act.source.type == LocationType.TABLEAU:
                if not isinstance(act.source, TableauPosition):
                    raise ValueError("TableauPosition required for source location")
                self.move_tableau_card(act.source.pile, act.dest)
            elif act.source.type == LocationType.WASTE:
                self.move_waste_card(act.dest)
            elif act.source.type == LocationType.FOUNDATION:
                self.move_foundation_card(act.source.suit, act.dest)
            else:
                raise ValueError("Invalid source location")

    def draw_stock(self):
        if len(self.stock) == 0:
            # if we have waste, flip it first if we can
            if len(self.waste) == 0:
                raise RulesError("Stock and waste piles are empty")
            elif self.stock_pass_limit > 0 and self.current_stock_pass >= self.stock_pass_limit:
                raise RulesError("Already did {:d} stock pass{:s} this game".format(self.current_stock_pass, '' if self.current_stock_pass == 1 else 'es'))
            self.stock = self.waste
            self.stock.flip()
            self.current_stock_pass += 1
            self.waste = Deck(cards=[])
        
        for _ in range(self.draw_count):
            if len(self.stock) == 0:
                break
            c = self.stock.draw()
            self.waste.insert(0, c)

        self.history.append(self.state)

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

        self.history.append(self.state)

    def move_tableau_card(self, source_pile: int, dest: Location):
        if dest.type == LocationType.TABLEAU:
            raise RulesError("Use move_tableau_stack to move cards to tableau")
        elif dest.type == LocationType.WASTE:
            raise RulesError("Cannot move cards to waste pile")
        elif dest.type == LocationType.FOUNDATION:
            fdest: FoundationPosition = dest

            if source_pile < 0 or source_pile >= len(self.tableau):
                raise ValueError("Invalid source tableau pile")

            t = self.tableau[source_pile]
            card = t.top()
            
            # get the foundation to move it to
            f = self.foundations[fdest.suit]
            expected = f.needs()
            if card != expected:
                raise RulesError("Cannot add {:s} to {:s} foundation pile; legal cards are {:s}".format(str(card), f.suit.name, str(expected)))
            
            c = t.take(1)[0]
            f.add(c)
        else:
            raise ValueError("Invalid destination location")
        
        self.history.append(self.state)
        
    def move_waste_card(self, dest: Location):
        """
        Move the card at the top of the waste pile to the given location.
        """
        
        if dest.type == LocationType.TABLEAU:
            tdest: TableauPosition = dest

            if tdest.pile is None:
                raise ValueError("Destination pile is required for moves to tableau")
            if tdest.pile < 0 or tdest.pile >= len(self.tableau):
                raise RulesError("Invalid destination tableau pile; legal piles are 0 through {:d}".format(len(self.tableau)-1))
            
            t = self.tableau[tdest.pile]
            card = self.waste.top

            if card not in t.needs():
                raise RulesError("Cannot add {:s} to tableau[{:d}]; legal cards are {:s}".format(str(card), tdest.pile, ', '.join([str(c) for c in t.needs()])))
            
            c = self.waste.draw()
            t.give([c])
        elif dest.type == LocationType.FOUNDATION:
            fdest: FoundationPosition = dest

            card = self.waste.top
            # get the foundation to move it to
            f = self.foundations[fdest.suit]
            expected = f.needs()
            if card != expected:
                raise RulesError("Cannot add {:s} to {:s} foundation pile; legal cards are {:s}".format(str(card), f.suit.name, str(expected)))
            
            c = self.waste.draw()
            f.add(c)
        else:
            raise RulesError("Waste pile cards may only be moved to a tableau or foundation pile")
        
        self.history.append(self.state)
        
    def move_foundation_card(self, suit: Suit, dest: Location):
        if dest.type == LocationType.TABLEAU:
            tdest: TableauPosition = dest

            if tdest.pile is None:
                raise ValueError("Destination pile is required for moves to tableau")
            if tdest.pile < 0 or tdest.pile >= len(self.tableau):
                raise RulesError("Invalid destination tableau pile; legal piles are 0 through {:d}".format(len(self.tableau)-1))
            
            t = self.tableau[tdest.pile]

            card = self.foundations[suit].top()
            if card not in t.needs():
                raise RulesError("Cannot add {:s} to tableau[{:d}]; legal cards are {:s}".format(str(card), tdest.pile, ', '.join([str(c) for c in t.needs()])))
            
            c = self.waste.draw()
            t.give([c])
        elif dest.type == LocationType.WASTE:
            raise RulesError("Cannot move cards from foundation to waste")
        elif dest.type == LocationType.FOUNDATION:
            raise RulesError("Cannot move cards from foundation to foundation")
        else:
            raise ValueError("Invalid destination location")
        
        self.history.append(self.state)

    def undo(self):
        if len(self.history) < 2:
            raise RulesError("At start of game; nothing to undo")
        
        self.history.pop()
        last = self.history[-1]
        
        # restore all state from the last state
        self.tableau = list(p.clone() for p in last.tableau)
        self.foundations = {s: f.clone() for s, f in last.foundations.items()}
        self.waste = last.waste.clone()
        self.stock = last.stock.clone()
        self.current_stock_pass = last.current_stock_pass

    @property
    def outcome(self) -> Result | None:
        pass
        # TODO: fill this in
            

    @property
    def running(self) -> bool:
        # TODO: return False if no more moves, get them from legal_moves and
        # exclude non-bottom stack moves for calculation purposes.
        # win cond is here - all cards in foundation piles

        win_condition_met = all(f.needs() is None for f in self.foundations.values())
        if win_condition_met:
            return False
        
        # we can't determine if the game is unwinnable without looking ahead at
        # stock, which will only be player knowledge if they've been through it
        # at least once. Ergo, no-useful-move detection can only be done if the
        # pass limit is > 1 and the stock has been gone through at least once.
        
        # TODO: enable this after validation
        #elif self.has_useful_moves() is False:
        #    return False
        
        return True
            
    @property
    def hand(self) -> Deck:
        # return the currently viewed card(s) from the waste pile. Only the top
        # card is playable.
        return Deck(self.waste.top_n(self.draw_count, or_fewer=True))

    @property
    def rules(self) -> Rules:
        return Rules(
            draw_count=self.draw_count,
            stock_pass_limit=self.stock_pass_limit,
            starting_deck=[str(c) for c in self.starting_deck],
            random_deck=self.random_deck,
            num_piles=len(self.tableau),
        )
    
    @property
    def state(self) -> State:
        return State(
            tableau=[t.clone() for t in self.tableau],
            foundations={s: f.clone() for s, f in self.foundations.items()},
            stock=self.stock.clone(),
            waste=self.waste.clone(),
            current_stock_pass=self.current_stock_pass,
            pass_limit=self.stock_pass_limit,
            draw_count=self.draw_count
        )

    def state_with_turn_applied(self, action: Action) -> State:
        """
        Get the state that would result from playing the given move, without
        changing self.
        """

        # NOTE: do NOT call state.after here, as it will call this function
        self.take_turn(self.current_player, action)
        s = self.state.clone()
        self.undo()
        return s
    
    @property
    def max_players(self) -> int:
        return 1
    
    @property
    def min_players(self) -> int:
        return 1
    
    @property
    def current_player(self) -> int:
        """Return the index of the player whose turn it is."""
        return 0
    

class HumanPlayer(BasePlayer):

    def __init__(self, rules: dict):
        self.rules = rules

    def next_move(self, s: State) -> Action:
        cio.clear()
        print(s.board())

        moves = [(m, str(m)) for m in s.legal_moves()]

        non_number_options = [
            ('U', -1, 'Undo'),
            ('C', -2, 'Give up'),
        ]

        m = cio.select('Select move', moves, non_number_options)

        if m == -2:
            return None
        elif m == -1:
            return UndoAction()
        else:
            return m
    