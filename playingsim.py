#!/usr/bin/env python

import sim.runner
import sim.games.klondike as klondike
from sim.card import Card
from sim.deck import Deck
import sys

import argparse
import random

def play_klondike(draw_count: int=1, stock_pass_limit: int=0, deck_seed: str | None=None, num_piles: int=7):
    deck = None
    if deck_seed is not None:
        random.seed(deck_seed)
        deck = Deck()
        deck.shuffle()

    g = klondike.Game(draw_count, stock_pass_limit, deck_seed, num_piles)
    p = klondike.HumanPlayer(g.rules)

    sim.runner.play_until_done(g, [p])


def main():
    parser = argparse.ArgumentParser(description='Play game sims')

    subs = parser.add_subparsers(dest='game', help='Game to play', required=True, metavar='GAME')
    subs: argparse._SubParsersAction

    klon_parser = subs.add_parser('klondike', help='Play Klondike solitaire')
    klon_parser: argparse.ArgumentParser
    klon_parser.add_argument('-d', '--draw', type=int, default=1, help='Set number of cards that are be drawn at once from the deck. Typical values are 1 or 3.')
    klon_parser.add_argument('-p', '--piles', type=int, default=7, help='Set number of tableau piles to use. Typical value is 7 for a 1-deck game.')
    klon_parser.add_argument('-l', '--limit', type=int, default=0, help='Set the number of times the stock pile can be cycled. Default is 0, which is unlimited.')
    klon_parser.add_argument('-s', '--seed', type=str, default=None, help='Set the seed for the random number generator. This allows for reproducible games.')
    args = parser.parse_args()

    if args.game.lower() == 'klondike':
        play_klondike(args.draw, args.limit, args.seed, args.piles)
    else:
        print(f"Unknown game: {args.game}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
