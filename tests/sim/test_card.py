import unittest


from sim.deck import Deck
from sim.card import Card, Rank, Suit

class TestCard(unittest.TestCase):

    def test_init(self):
        cases = [
            {
                'name': 'added ranks',
                'rank': Rank.ACE + 1,
                'suit': Suit.HEARTS,
                'expect': Card(Rank.TWO, Suit.HEARTS),
            },
        ]

        for c in cases:
            with self.subTest(name=c['name']):
                actual = Card(c['rank'], c['suit'])
                self.assertEqual(actual, c['expect'])
                