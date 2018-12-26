# Dominion Randomizer #

This program automates the card randomizer process by picking 10 cards from the given sets, as this process can be cumbersome to do manually when shuffling randomizers from many game sets. Run with the desired game sets, or `all`, as parameters to `randomizer.py`.

## Example ##

    python randomizer.py base1e intrigue2e seaside prosperity

## Output ##

    Base
    - Laboratory (Action), Cost(5C)
    - Market (Action), Cost(5C)
    Intrigue
    - Minion (Action, Attack), Cost(5C)
    - Patrol (Action), Cost(5C)
    - Swindler (Action, Attack), Cost(3C)
    Prosperity
    - King's Court (Action), Cost(7C)
    - Vault (Action), Cost(5C)
    Seaside
    - Island (Action, Victory), Cost(4C)
    - Native Village (Action), Cost(2C)
    - Wharf (Action, Duration), Cost(5C)

## Configuration ##

`python randomizer.py [SETS ...]`

Required. Specify the Dominion sets to randomize from. Possible options:

- `base1e`
- `base2e`
- `intrigue1e`
- `intrigue2e`
- `seaside`
- `alchemy`
- `prosperity`
- `cornucopia`
- `hinterlands`
- `darkages`
- `guilds`
- `adventures`
- `empires`
- `nocturne`
- `renaissance`
- `all`

If `all` is selected, cards from all game sets are included.

### Optional Arguments ###

`-n/--number NUMBER`

Number of cards to pick, default 10.

`-w/--weights [WEIGHTS ...]`

Specify weights to apply to each given set for randomization. The weights can be floats and are applied relative to each other.

`-c/--counts [COUNTS ...]`

Specify counts of cards to randomly draw from each given set. The sum of the counts must match the total number of cards being drawn randomly.

`-i/--include [INCLUDE ...]`

Specify cards to include in the output.

`-x/--exclude [EXCLUDE ...]`

Specify cards to exclude from the list of possible cards.

`-f/--filter-types [TYPES ...]`

Filter out cards with specific types from the list of possible cards.

`-e/--events EVENTS`

Number of Event cards to pick, default 0.

`-l/--landmarks LANDMARKS`

Number of Landmark cards to pick, default 0.
