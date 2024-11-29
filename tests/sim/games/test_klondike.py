import unittest

from sim.games.klondike import State
from sim.deck import Deck
from sim.card import Card

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