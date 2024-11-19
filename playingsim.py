#!/usr/bin/env python

import sim.runner
import sim.games.klondike as klondike_game
import sim.player.klondike as klondike_player


def main():
    g = klondike_game.Game()
    p = klondike_player.Human(g.rules)

    sim.runner.play_until_done(g, [p])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
