import unittest

from sim.games.klondike import State, Pile
from sim.deck import Deck
from sim.card import Card

class TestPile(unittest.TestCase):

    def test_take(self):
        cases = [
            {
                'name': 'empty, no count specified',
                'expect_exception': {'type': ValueError, 'msg': "Count must be at least 1"},
            },
            {
                'name': 'empty, count specified',
                'count': 1,
                'expect_exception': {'type': ValueError, 'msg': "only 0 cards are revealed"},
            },
            {
                'name': 'reveal hidden',
                'count': 2,
                'shown': ['AC', '2C'],
                'hidden': ['3C', '4C', '5C'],
                'expect': ['AC', '2C'],
                'expect_shown': ['3C'],
                'expect_hidden': ['4C', '5C'],
            },
            {
                'name': 'reveal slot',
                'count': 2,
                'shown': ['AC', '2C'],
                'hidden': [],
                'expect': ['AC', '2C'],
                'expect_shown': [],
                'expect_hidden': [],
            },
            {
                'name': 'take top only',
                'count': 1,
                'shown': ['AC', '2C', '3C'],
                'hidden': ['4C', '5C', '6C'],
                'expect': ['AC'],
                'expect_shown': ['2C', '3C'],
                'expect_hidden': ['4C', '5C', '6C'],
            },
        ]

        for c in cases:
            name = c.get('name', '<none>')
            shown = c.get('shown', [])
            hidden = c.get('hidden', [])
            count = c.get('count', 0)
            expect_exception = c.get('expect_exception', None)
            expect = c.get('expect', [])
            expect_hidden = c.get('expect_hidden', None)
            expect_shown = c.get('expect_shown', None)


            expect_exc_type = None
            expect_exc_msg = None
            if expect_exception is not None:
                expect_exc_type = expect_exception.get('type', Exception)
                expect_exc_msg = expect_exception.get('msg', '')

            shown = [Card.parse(c) for c in shown]
            hidden = [Card.parse(c) for c in hidden]
            expect = [Card.parse(c) for c in expect]

            if expect_hidden is not None:
                expect_hidden = [Card.parse(c) for c in expect_hidden]
            if expect_shown is not None:
                expect_shown = [Card.parse(c) for c in expect_shown]

            with self.subTest(name=name):
                p = Pile()
                p.shown = shown
                p.hidden = hidden

                if expect_exception is not None:
                    with self.assertRaisesRegex(expect_exc_type, expect_exc_msg):
                        p.take(count)
                else:
                    actual = p.take(count)
                    self.assertEqual(actual, expect)
                    if expect_hidden is not None:
                        self.assertEqual(p.hidden, expect_hidden, "resulting hidden does not match")
                    if expect_shown is not None:
                        self.assertEqual(p.shown, expect_shown, "resulting shown does not match")

class TestState(unittest.TestCase):

    def test_accessible_stock_cards(self):
        cases = [
            {
                'name': 'empty, draw 1',
                'stock': [],
                'waste': [],
                'draw': 1,
                'current_pass': 2,
                'expect': [],
            },
            {
                'name': 'empty, draw 2',
                'stock': [],
                'waste': [],
                'draw': 2,
                'current_pass': 2,
                'expect': [],
            },
            {
                'name': 'simple case, draw 3',
                'stock': ['7C', '8C', '9C'],
                'waste': ['AC', '2C', '3C', '5C', '6C'],
                'expect': ['AC', '9C', '3C', '7C'],
                'draw': 3,
                'current_pass': 2,
            },
            {
                'name': 'simple case, draw 3, first pass',
                'stock': ['7C', '8C', '9C'],
                'waste': ['AC', '2C', '3C', '5C', '6C'],
                'expect': ['AC', '3C'],
                'draw': 3,
                'current_pass': 1,
            },
            {
                'name': 'real-game case, draw 3, non-first pass',
                'stock': ['5H', '2D', 'KH'],
                'waste': ['2S', 'AD', '4D', '5D', '6C', 'JC', '7H', '7S', '4S', '9D', '5C', '5S', '9C', '8D', '3H', '3D', '6S', 'JD', '6H', '3C'],
                'expect': ['2S', 'KH', 'JD', '3H', '5S', '4S', 'JC', '4D', '5H'],
                'draw': 3,
                'current_pass': 2,
            },
            {
                'name': 'real-game case, draw 3, first pass',
                'stock': ['5H', '2D', 'KH'],
                'waste': ['2S', 'AD', '4D', '5D', '6C', 'JC', '7H', '7S', '4S', '9D', '5C', '5S', '9C', '8D', '3H', '3D', '6S', 'JD', '6H', '3C'],
                'expect': ['2S', 'JD', '3H', '5S', '4S', 'JC', '4D'],
                'draw': 3,
                'current_pass': 1,
            },
        ]

        for c in cases:
            name = c.get('name', '<none>')
            stock = c.get('stock', [])
            waste = c.get('waste', [])
            limit = c.get('limit', 0)
            draw = c.get('draw', 1)
            stock_pass = c.get('current_pass', 1)
            expect = c.get('expect', [])

            stock = Deck([Card.parse(c) for c in stock])
            waste = Deck([Card.parse(c) for c in waste])
            expect = [Card.parse(c) for c in expect]

            with self.subTest(name=name):
                st = State([], {}, stock, waste, stock_pass, limit, draw)

                actual = st.accessible_stock_cards
                self.assertEqual(actual, expect)