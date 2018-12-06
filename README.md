# Dominion Randomizer #

This program automates the card randomizer process by picking 10 cards from the given sets, as this process can be especially cumbersome to do manually when picking from many game sets. Run with the desired game sets, or `all`, as parameters to `randomizer.py`.

### Example ###

    python randomizer.py base1e intrigue2e seaside prosperity

### Output ###

    Base
    - Cellar (Action), Base, Cost(2C, 0P, 0D)
    - Chancellor (Action), Base, Cost(3C, 0P, 0D)
    - Market (Action), Base, Cost(5C, 0P, 0D)
    Intrigue
    - Diplomat (Action, Reaction), Intrigue, Cost(4C, 0P, 0D)
    - Mill (Action, Victory), Intrigue, Cost(4C, 0P, 0D)
    - Replace (Action, Attack), Intrigue, Cost(5C, 0P, 0D)
    Prosperity
    - City (Action), Prosperity, Cost(5C, 0P, 0D)
    - Goons (Action, Attack), Prosperity, Cost(6C, 0P, 0D)
    Seaside
    - Caravan (Action, Duration), Seaside, Cost(4C, 0P, 0D)
    - Ghost Ship (Action, Attack), Seaside, Cost(5C, 0P, 0D)

Currently does not handle individual Promo cards or support randomizing landscape-oriented cards.