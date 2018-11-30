# Dominion Randomizer #

This program automates the card randomizer process by picking 10 cards from the given sets, as this process can be especially cumbersome to do manually when picking from many game sets. Run with the desired game sets, or `all`, as parameters to `randomizer.py`.

### Example ###

    python randomizer.py base1e intrigue2e seaside prosperity

### Output ###

    Mine (Card), Base, (Action), Cost(5C, 0P, 0D)
    Venture (Card), Prosperity, (Treasure), Cost(5C, 0P, 0D)
    Conspirator (Card), Intrigue, (Action), Cost(4C, 0P, 0D)
    Lurker (Card), Intrigue 2E, (Action), Cost(2C, 0P, 0D)
    Trading Post (Card), Intrigue, (Action), Cost(5C, 0P, 0D)
    Steward (Card), Intrigue, (Action), Cost(3C, 0P, 0D)
    Lookout (Card), Seaside, (Action), Cost(3C, 0P, 0D)
    Fishing Village (Card), Seaside, (Action, Duration), Cost(3C, 0P, 0D)
    Chapel (Card), Base, (Action), Cost(2C, 0P, 0D)
    Masquerade (Card), Intrigue, (Action), Cost(3C, 0P, 0D)

Currently does not handle individual Promo cards or support randomizing landscape-oriented cards.