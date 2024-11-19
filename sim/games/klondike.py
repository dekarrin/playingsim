from ..card import Card, Suit, Rank
from ..deck import Deck
from . import RulesError, Game as BaseGame, Player as BasePlayer
from .. import cio, UndoAction

from enum import Enum, IntEnum, auto


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
    
    def clone(self) -> 'Foundation':
        f = Foundation(self.suit)
        f.cards = list([c.clone() for c in self.cards])
        return f


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
        cards = list(cards)

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
                self.shown = [self.hidden.pop()]
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

class TableauPosition(Location):
    def __init__(self, pile: int):
        super().__init__(LocationType.TABLEAU)
        self.pile = pile

    def __str__(self):
        return f"T{self.pile}"


class WastePosition(Location):
    def __init__(self):
        super().__init__(LocationType.WASTE)

    def __str__(self):
        return "waste pile"


class FoundationPosition(Location):
    def __init__(self, suit: Suit):
        super().__init__(LocationType.FOUNDATION)
        self.suit = suit

    def __str__(self):
        return f"{self.suit.name.lower()} pile"


class Action:
    def __init__(self, type: TurnType):
        self.type = type

    def __str__(self) -> str:
        return str(self.type)
    
    def __lt__(self, other: 'Action') -> bool:
        if not isinstance(other, Action):
            return False
        return self.type < other.type

    def __eq__(self, other: 'Action') -> bool:
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

    def __str__(self):
        return "Move T{:d} -> T{:d}, stack of {:d}".format(self.source_pile, self.dest_pile, self.count)


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


class State:
    def __init__(self, tableau: list[Pile], foundations: dict[Suit, Foundation], stock: Deck, waste: Deck, current_stock_pass: int, pass_limit: int=0, draw_count: int=0):
        self.tableau = tableau
        self.foundations = foundations
        self.stock = stock
        self.waste = waste
        self.current_stock_pass = current_stock_pass
        self.pass_limit = pass_limit
        self.draw_count = draw_count

    @property
    def remaining_stock_flips(self) -> int:
        return self._pass_limit - self.current_stock_pass if self._pass_limit > 0 else -1
    
    def clone(self) -> 'State':
        return State(
            tableau=[t.clone() for t in self.tableau],
            foundations={s: f.clone() for s, f in self.foundations.items()},
            stock=self.stock.clone(),
            waste=self.waste.clone(),
            current_stock_pass=self.current_stock_pass,
            pass_limit=self._pass_limit
        )
    
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
        for i, c in enumerate(self.waste.top_n(disp_waste, or_fewer=True)):
            board += str(c)
            if i+1 < disp_waste:
                board += border
        board += '\n'

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
            
            act: MoveTableauStackAction = action
            self.move_tableau_stack(act.source_pile, act.dest_pile, act.count)
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
                continue
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
    def running(self) -> bool:
        # TODO: return False if no more moves, get them from legal_moves and
        # exclude non-bottom stack moves for calculation purposes.
        # win cond is here - all cards in foundation piles
        return not all(f.needs() is None for f in self.foundations.values())

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
                'cards': [str(c) for c in self.starting_deck]
            },
            'num_piles': len(self.tableau)
        }
    
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
    