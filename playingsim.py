#!/usr/bin/env python

import sim.runner
import sim.games.klondike as klondike


def main():
    g = klondike.Game()
    p = klondike.HumanPlayer(g.rules)

    sim.runner.play_until_done(g, [p])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
