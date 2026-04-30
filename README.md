# Introduction
A Savage Worlds die roller built with python, pycord, and sqlite.

Do not run Savage Roller with python3.14, as the event loop thing is broken with pycord.

## Installation
To add Savage Roller to your server, click this link:

https://discord.com/oauth2/authorize?client_id=1415122496339972108

## Running Your Own Instance
You will need to setup a .env file with your own token, public key, and application ID from Discord. See https://guide.pycord.dev/getting-started/creating-your-first-bot#tokens for details.

## Run in Docker
https://hub.docker.com/r/apampuch/savage-roller/

`docker run -d --rm --env-file .env -v HOSTDATAFOLDER:/app/data apampuch/savage-roller:latest`

Use `:Z` after the volume mount if you're using a system with SELinux (Fedora, RHEL, etc.)

# Rolling
Use `/roll` to roll dice. Basic format is `[num][key-operator][die-size]`, if the first `num` is not provided, it assumes 1.

For example, a basic Wild Card trait roll is done with `/roll s10`, which rolls one d10 and one d6, exploding both, and taking the higher of the two. A damage roll could be `/roll 2d6+1`, which rolls two exploding d6 dice, totals their results, then adds 1.

All sub operators come after the key operators, sub operators may be applied in any order. For example, `/roll 3s12w10c6t8-2` rolls 3d12s, plus one d10 wild die which replaces the lowest of the d12s, adds an exploding d6 conviction die to each total, subtracts 2 from each total, and compares each to a target number of 8 to determine success and failure.

## Key Operators
- `d`: **Die Roll** Rolls exploding dice without rolling a wild die. When rolling multiple dice, results of all dice are totaled. This rolls exploding dice by default because dice in Savage Worlds explode by default.
- `s`: **Savage Roll** Rolls exploding dice and a wild die. When rolling multiple dice, the results of all dice are given; the lowest die is replaced with the wild die. This also checks for critical failures. A single wild die is rolled no matter how many dice are rolled. Multiple dice are normally rolled in this manner when firing RoF weapons or using Frenzy.
- `e`: **Extra Roll** Rolls exploding dice. When rolling multiple dice, the results of all dice are given. When rolling a single die, if the result is 1, it also rolls a d6 to check for critical failures. (See page 88 of SWADE for the exact rules, this was up to slight interpretation, but I think I got this edge case right.)
- `n`: **Non-Exploding Dice** Rolls non-exploding dice. When rolling multiple dice, results of all dice are totaled. This is mostly used for rolling damage against objects, rolling the running die, or the Big Red Die.

## Sub Operators
- `w`: **Wild Die Size** Sets the size of the wild die. This is mostly altered by the Master edge.
- `c`: **Conviction Die** Sets the size of the conviction die and rolls it. Most of the time, this will be a d6, so it's usually rolled as `c6`. This can be set to another die size, as some third party products alter the size of the Conviction die. An integer __must__ follow this operator, as each operator requires an integer to be able to function.
- `t`: **Target**: Sets the target for determining success/failure/raise. Used when trying to hit a target's Parry, or when using target numbers instead of the "penalty" system SWADE recommends.
- `+`: Adds dice or flat values. Totaled dice can add dice, non-totaled dice can only have flat values added.
- `-`: As above, but it subtracts instead of adds.

# Characters
Characters are per server, and are mostly used for saving commonly used characters, like PCs. You can store initiative-relevant edges on characters.

Create a character with `/new_character [name]`. Delete them with `/new_character [name]`. Rename them with `/new_character [old_name] [new_name]`.

## Edges
Characters can have edges, though since only initiative-related ones are relevant, they're the only ones that can be applied. They are:
- `quick`
- `levelheaded`
- `levelheaded-imp`
- `tactician`
- `tactician-imp`
- `hesitant` (technically, this is a hindrance, but it functions as a way to modify initiative, so it's included)

All of these edges are functional, that means that a character with Quick will discard cards with a value of 5 or lower until something higher is dealt. Tactician edges are handled with special commands.

Edges can be added with `add_edges [edges]`. Multiple edges can be added if comma separated, but they can't be edges that conflict with each other as per the rules. Improved edges are mutually exclusive with their normal ones; to upgrade, remove the old edge, then add the improved one.

Edges can be removed with `remove_edges [edges]`.

## Bennies
Give bennies (one at a time) with `/give_benny [characters]`. Take them with `/take_benny [characters]`. Set them to a specified amount with `/set_bennies [characters] [number]`.

# Initiative
Initiative lists are per channel and server. This means that you can have multiple initiative lists per server, as long as each one is in a different channel. Most commands can take multiple names as long as they're split with commas, `/fight Lelouche, Suzaku, Karen` will add three characters to initiative: `Lelouch`, `Suzaku`, and `Karen` (leading and trailing whitespace will be stripped). On the other hand, using `/fight Lelouche Suzaku Karen` will just add one character named `Lelouche Suzaku Karen`. (This is purposefully different from the project I based this on because it personally bugged me.)

## Card Values
Some commands require a card value as input. These are represented by short strings, with the first character being the suit, and the following character(s) being the value. Thus, C4 is a Four of Clubs, S10 is the Ten of Spades, HK is the King of Hearts, and RJ is the Red Joker.

## Temporary Characters
When adding characters to a fight, you don't have to use names of characters saved on the server. If you use 
Temporary characters are deleted when a new fight is started, or when they're removed from the initiative list.

To start a fight, use `/fight [characters]`. To add characters to a fight, use `/deal_in [characters]`. To remove characters, use `/deal_out [characters]`.

Starting a new round is simple: use `/new_round`. If you want to deal a character a new card from the deck, use `give_card [character]`. To simply list the current initiative, use `/list_fight`, although most commands will also do this.

Tactician cards are handled in a separate column. To give a character a tactician card, use `/assign_tactician_card [tactician_character] [card_value] [recipient_character]`. 

## Special Initiative Commands
Level Headed and Improved Level Headed technically don't *require* you to use the highest card drawn, but Savage Roller automatically selects it for you when dealing initiative. If you don't want to use that card for some reason (to get the Calculating bonus, for instance), use `/choose_card [character] [unused_card]`, where `unused_card` is one of the cards in the character's Unused Cards column.

Furthermore, those with both Level Headed and Quick might want to choose a card with a rank of 5 or lower if their higher card isn't particularly high, specifically to gamble for an even higher card. To do this, first select the lower card with `/choose_card`, then use `/quick_redraw [character]` to perform the redrawing function of the Quick edge. Note that this function does not actually check if the target character has the Quick edge or not, I trust that you will use this responsibly.

# Planned Features
- Bennies: As explained in SW.
- Parties: Preset lists of characters that can easily be dealt in and given bennies. Will probably have to share unique names with character names.
- Character Rolls: A way to save things like traits and damage rolls to characters. Will also have a way for a user to "control" a character and use their saved rolls.
