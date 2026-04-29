# Introduction
A Savage Worlds die roller built with python, pycord, and sqlite.

Do not run Savage Roller with python3.14, as the event loop thing is broken with pycord.

# Run in Docker
`sudo docker run --env-file .env savage-roller`

# Rolling
Use `/roll` to roll dice. Basic format is `[num][key-operator][die-size]`, if the first `num` is not provided, it assumes 1.

For example, a basic Wild Card trait roll is done with `/roll s10`, which rolls one d10 and one d6, exploding both, and taking the higher of the two. A damage roll could be `/roll 2d6+1`, which rolls two exploding d6 dice, totals their results, then adds 1.

All sub operators come after the key operators, sub operators may be applied in any order. For example, `/roll 3s12w10c6t8-2` rolls 3d12s, plus one d10 wild die which replaces the lowest of the d12s, adds an exploding d6 conviction die to each total, subtracts 2 from each total, and compares each to a target number of 8 to determine success and failure.

## Key Operators
`d`: **Die Roll** Rolls exploding dice without rolling a wild die. When rolling multiple dice, results of all dice are totaled. This rolls exploding dice by default because dice in Savage Worlds explode by default.
`s`: **Savage Roll** Rolls exploding dice and a wild die. When rolling multiple dice, the results of all dice are given; the lowest die is replaced with the wild die. This also checks for critical failures. A single wild die is rolled no matter how many dice are rolled. Multiple dice are normally rolled in this manner when firing RoF weapons or using Frenzy.
`e`: **Extra Roll** Rolls exploding dice. When rolling multiple dice, the results of all dice are given. When rolling a single die, if the result is 1, it also rolls a d6 to check for critical failures. (See page 88 of SWADE for the exact rules, this was up to slight interpretation, but I think I got this edge case right.)
`n`: **Non-Exploding Dice** Rolls non-exploding dice. When rolling multiple dice, results of all dice are totaled. This is mostly used for rolling damage against objects, rolling the running die, or the Big Red Die.

## Sub Operators
`w`: **Wild Die Size** Sets the size of the wild die. This is mostly altered by the Master edge.
`c`: **Conviction Die** Sets the size of the conviction die and rolls it. Most of the time, this will be a d6, so it's usually rolled as `c6`. This can be set to another die size, as some third party products alter the size of the Conviction die. An integer __must__ follow this operator, as each operator requires an integer to be able to function.
`t`: **Target**: Sets the target for determining success/failure/raise. Used when trying to hit a target's Parry, or when using target numbers instead of the "penalty" system SWADE recommends.
`+`: Adds dice or flat values. Totaled dice can add dice, non-totaled dice can only have flat values added.
`-`: As above, but it subtracts instead of adds.

# Characters
Characters are per server. You can store initiative-relevant edges on characters.

# Initiative
Initiative lists are per channel and server.
You can either use characters stored in your server. If a character isn't found in the initiative list, they're added as a temporary character.
Temporary characters are deleted when a new fight is started, or when they're removed from the initiative list.