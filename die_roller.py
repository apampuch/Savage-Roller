from collections import Counter
from dataclasses import dataclass, field
from random import randint
from typing import Dict, List, Union

import warnings


@dataclass
class RollData:
    die_list: List[int] = field(default_factory=list)   # must be >= 2
    wild_die_size: int = 0                              # if 0, do not roll
    conviction_die: int = 0                             # size of conviction die, if 0, do not roll
    target: int = 4                                     # target we're trying to get
    bonus: int = 0                                      # flat bonus to be added or subtracted
    extra_roll: bool = False                            # roll as an extra, only roll wild die if crit fail is possible
    explode: bool = True                                # explode if true
    total: bool = True                                  # total the dice together if true, return all separately if false

    def __add__(self, other: Union[int, "RollData"]) -> "RollData":
        # if isinstance(other, int):
        #     pass
            
        if isinstance(other, RollData):
            return RollData(
                die_list=self.die_list + other.die_list,
                wild_die_size=self.wild_die_size or other.wild_die_size,
                conviction_die=self.conviction_die or other.conviction_die,
                target=self.target or other.target,
                bonus=self.bonus + other.bonus,
                extra_roll=self.extra_roll or other.extra_roll,
                explode=self.explode or other.explode,
                total=self.total or other.total
            )
        else:
            return NotImplemented

    def __invert__(self):
        for i in range(len(self.die_list)):
            self.die_list[i] = -self.die_list[i]

    def __radd__(self, other):
        return self.__add__(other)


def split_roll_string(roll_string: str) -> List[str]:
    # validate the string
    count = Counter(roll_string)
    # make sure we only have one of d, s, e, n
    number_of_roll_types = len(set(count) & set('dsen'))
    if number_of_roll_types > 1:
        raise ValueError('Cannot mix roll types!')
    for op in {'s', 'e', 'n', 't', 'c'}:
        if count[op] > 1:
            raise ValueError(f'Too many "{op}" operators! (Can only have one.)')

    splitters = {'d', 's', 'e', 'w', 'n', 't', 'c', '+', '-'}

    parts = []
    buffer = ''
    
    for c in roll_string:
        if c in splitters:
            if buffer:
                parts.append(buffer)
                buffer = ''
            parts.append(c)
        else:
            buffer += c
    if buffer:
        parts.append(buffer)

    return parts


def parse_tokens(roll_string: str) -> RollData:
    '''
    Roll operators: May be prefixed with a number, if not, assume 1

    d: roll dice, all explode
    s: roll dice and a single wild die, all explode. Do not total
    e: roll dice, all explode, do not total
    n: roll dice, none explode

    t: check against target number (NYI)
    w: roll wild die, must be used with 's' (following 's')
    c: add conviction (must be put at the end)

    Arithmetic Operators
    +: add to the final total
    -: subtract from the final total
    '''
    tokens = split_roll_string(roll_string)

    # not strictly binary, will assume 1 if left == None
    binary_op_tokens = {'d', 's', 'e', 'n'}
    # will consume left operand
    unary_op_tokens = {'w', 't', 'c'}
    # immediately consume
    consume_tokens = {'+', '-'}

    roll_data = RollData()    
    mode        = '+'     # can only be '+' or '-'
                            # when this changes, we consume
    left:int        = None  # type: ignore
    operator:str    = None  # type: ignore
    right:int       = None  # type: ignore

    def consume():
        nonlocal left, operator, right

        # special case if the operator is None
        if operator is None:
            # if all three are blank, just do nothing and return
            if left is None and right is None:
                return

            # warn if right operand is set because that should not happen
            if right is not None:
                warnings.warn(f'Right operand was set to {right}, this should be impossible.')
                right       = None

            # if none, just add the left operand to the bonus and move on
            if mode == '+':
                roll_data.bonus += left
            else:
                roll_data.bonus -= left

            # clear and return
            left = None
            return

        # enforce binary and unary
        elif operator in binary_op_tokens:
            if left is None or right is None:
                raise ValueError(f'Bad consume: {left}{operator}{right}')
            
            # set dice, deal with negative
            dice = []
            if isinstance(left, int) and isinstance(right, int):
                if mode == '+':
                    dice = [right] * left
                elif mode == '-':
                    dice = [-right] * left
            else:
                raise ValueError(f'Bad left/right operands: {left} and {right}')
            
            match operator:
                case 'd':
                    roll_data.die_list.extend(dice)
                case 's':
                    roll_data.die_list.extend(dice)
                    roll_data.wild_die_size = 6
                    roll_data.total=False
                case 'e':
                    roll_data.die_list.extend(dice)
                    roll_data.extra_roll = True
                    roll_data.total=False
                case 'n':
                    roll_data.die_list.extend(dice)
                    roll_data.explode = False
                case '_':
                    raise ValueError(f'Invalid operator {operator}')

        elif operator in unary_op_tokens:
            if left is not None or right is None:
                raise ValueError(f'Bad consume: {left}{operator}{right}')
            match operator:
                case 'w':
                    roll_data.wild_die_size = right
                case 't':
                    roll_data.target = right
                case 'c':
                    roll_data.conviction_die = right
                case '_':
                    raise ValueError(f'Invalid operator {operator}')

        left        = None  # type: ignore
        operator    = None  # type: ignore
        right       = None  # type: ignore

    for token in tokens:
        # if not an operator
        if token in binary_op_tokens:
            operator = token
            # assume left is 1 if blank
            if left is None:
                left = 1
        elif token in unary_op_tokens:
            if left is not None:
                consume()
            operator = token
        elif token in consume_tokens:
            # consume
            consume()
            # set the mode for the next consume
            mode = token
        else:
            # if the token can't be an int, raise a value error
            if not token.isdigit():
                raise ValueError(f'Invalid token {token}')
                
            # put in left if we have no operator, right if we do
            if operator == None:
                left = int(token)
            else:
                right = int(token)
                consume()

    # may need a final consume at the end, possibly a special one
    # to deal with 1d6+1
    if left is not None:
        consume()

    return roll_data

'''
This just rolls a die and does nothing else, no bonuses or anything.
'''
def roll_die(die_num: int, explode: bool = True) -> int:
    total = 0
    current_roll = die_num  # set to the max so we get at least one roll
    while current_roll == die_num:
        # if positive
        if die_num > 0:
            current_roll = randint(1, die_num)
        # if negative, we're subtracting
        elif die_num < 0:
            current_roll = randint(die_num, -1)

        # just return if we aren't exploding
        if not explode:
            return current_roll
        
        total += current_roll

    return total

'''
Rolls the trait dice (aka non wild dice), plus wild die and conviction die as needed.
'''
def roll_savage_dice(roll_data: RollData) -> Dict[str, Union[int, List[int]]]:
    # validate inputs
    for die in roll_data.die_list:
        if die < 2 and die > -2:
            raise ValueError("Die must have at least two sides!")
    if roll_data.wild_die_size != 0 and roll_data.wild_die_size < 2:
        raise ValueError("Wild die must have at least two sides, or zero if not rolling!")
    if len(roll_data.die_list) < 1:
        raise ValueError("Must roll at least two dice!")
    if roll_data.conviction_die != 0 and roll_data.conviction_die < 2:
        raise ValueError("Conviction die must a positive number greater than two, or zero if not rolling!")

    # get conviction roll
    conviction_roll = 0
    if roll_data.conviction_die != 0:
        conviction_roll = roll_die(roll_data.conviction_die, explode=True)

    # roll all trait rolls
    # technically this is used for damage rolls too, the name "trait roll" is used to separate it from the wild roll
    trait_rolls = []
    for die in roll_data.die_list:
        trait_rolls.append(roll_die(die, explode=roll_data.explode))

    # roll wild die
    wild_roll = 0
    if roll_data.wild_die_size != 0:
        wild_roll = roll_die(roll_data.wild_die_size, explode=roll_data.explode)
    # handle extra roll
    # only applies if the character rolls a single trait die
    # otherwise, we check for crit fail in the packaging function
    if roll_data.extra_roll and len(roll_data.die_list) == 1 and trait_rolls[0] == 1:
        wild_roll = roll_die(6, explode=False)

    # another function will package these results into a nice clean string
    return {
        'trait_rolls': trait_rolls,
        'wild_roll': wild_roll,
        'conviction_roll': conviction_roll
    }

'''
Writes the roll result in a pretty string message.
'''
def package_roll(
    roll_msg: str,
    roll_data: RollData,
    trait_rolls: List[int],
    wild_roll: int,
    conviction_roll: int
    ) -> str:
    
    original_trait_rolls = trait_rolls[::]
    report = f'{roll_msg}: '

    # if we're totaling, total all dice together, ignore wild die
    if roll_data.total:
        t = 0
        for roll in trait_rolls:
            t += roll

        t += roll_data.bonus + conviction_roll

        report += str(t)

        report += f'\nOriginal Rolls: {original_trait_rolls}'
        if conviction_roll > 0:
            report += f'\nConviction Roll: {conviction_roll}'
    
    # if not, handle like a normal trait roll
    else:
        # check if it's a critical failure
        crit_fail = False
        
        # check against the total number of dice if rolling more than 1
        if len(roll_data.die_list) > 1:
            # array of dice to check for 1
            check_dice = trait_rolls[::]
            
            # by both my own and ChatGPT's interpretation of the rules on page 88,
            # you don't roll an extra d6 when extras roll mutiple trait dice with RoF weapons and stuff
            # therefore, only add this if it's a wild card doing it
            if not roll_data.extra_roll:
                check_dice.append(wild_roll)

            more_than_half = len(check_dice) // 2 + 1
            ones = check_dice.count(1)
            if ones >= more_than_half:
                crit_fail = True
                    
        # otherwise, check against the wild die
        else:
            if trait_rolls[0] == 1 and wild_roll == 1:
                crit_fail = True
        
        # replace the lowest trait roll with the wild die if wild die is higher
        # only do this if it's not an extra roll so we don't accidentally trigger successes when checking for extra crit fails
        if wild_roll > 1 and not roll_data.extra_roll:
            lowest_trait = min(trait_rolls)
            if wild_roll > lowest_trait:
                trait_rolls[trait_rolls.index(lowest_trait)] = wild_roll

        results_string = ''
        # apply bonuses and add results to array
        for roll in trait_rolls:
            final_roll = roll + roll_data.bonus + conviction_roll

            # success: <= -1 = failure, 0 = success, >= 1 = raises
            success = (final_roll - roll_data.target) // 4

            results_string += f'{final_roll} '

            if success <= -1:
                results_string += '(Failure), '
            elif success == 0:
                results_string += '(Success), '
            elif success == 1:
                results_string += '(1 Raise), '
            else:
                results_string += f'({success} Raises), '

        # rstrip the comma and space from the end
        results_string = results_string.rstrip(', ')

        report += results_string
        if crit_fail:
            report = '**CRIT FAIL!** ' + report
            
        # add raw original rolls
        report += f'\nOriginal Rolls: {original_trait_rolls}'
            
        if wild_roll > 0:
            report += f'\nWild Die: {wild_roll}'
        if conviction_roll > 0:
            report += f'\nConviction Roll: {conviction_roll}'

    return report

