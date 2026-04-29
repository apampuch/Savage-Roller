import pprint
import characters
import database

from die_roller import *
from edges import *
from typing import Any, Callable

def new_container():
    return CharacterCardContainer(deck[0], 0)

def get_roll_data(msg):
    roll_data = parse_tokens(msg)
    return roll_savage_dice(roll_data)
    
def test_roll(msg):
    roll_data = parse_tokens(msg)
    roll_results = roll_savage_dice(roll_data)
    return package_roll(msg, roll_data, **roll_results)

# to print colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def run_test(func: Callable, params: tuple, answer: Callable[[Any], bool]):
    try:
        result = func(*params)
    except Exception as e:
        result = e

    # passfail = ''
    
    if answer(result):
        passfail = f'{bcolors.OKGREEN}PASS!{bcolors.ENDC}'
    else:
        passfail = f'{bcolors.FAIL}FAIL: Correct result is {answer}{bcolors.ENDC}'

    paramstring = str(params).lstrip("[").rstrip("]")

    report: str = f'{func.__name__}({paramstring}): {result}: {passfail}'

    print(report)
'''
# good strings
run_test(split_roll_string, ['1d12'], ['1', 'd', '12'])
run_test(split_roll_string, ['1s10'], ['1', 's', '10'])
run_test(split_roll_string, ['1d12t6'], ['1', 'd', '12', 't', '4'])
run_test(split_roll_string, ['1e6'], ['1', 'e', '6'])
run_test(split_roll_string, ['2d6+1'], ['2', 'd', '6', '+', '1'])
run_test(split_roll_string, ['2d8-1'], ['2', 'd', '8', '-', '1'])
run_test(split_roll_string, ['4s12w8'], ['4', 's', '12', 'w', '8'])
run_test(split_roll_string, ['s12w10t5c6+2'], ['s', '12','w', '10', 't', '5', 'c', '+', '2'])

# bad strings im testing anyway
run_test(split_roll_string, ['1w12'], ['1', 'w', '12'])
run_test(split_roll_string, ['wwses'], ['w', 'w', 's', 'e', 's'])
run_test(split_roll_string, ['1p12'], ['1p12'])
'''


# tests for die parsing
#pprint.pp(parse_tokens('1d12'))
#pprint.pp(parse_tokens('s10'))
#pprint.pp(parse_tokens('1d12t6'))
#pprint.pp(parse_tokens('1e6'))
#pprint.pp(parse_tokens('2d6+1'))
#pprint.pp(parse_tokens('2d8-1'))
#pprint.pp(parse_tokens('1-2d8'))
#pprint.pp(parse_tokens('4s12w8'))
#pprint.pp(parse_tokens('10s12w10t5c6+2-3d6'))
#pprint.pp(parse_tokens('3d6-1d4+2d8-4+1d8+1'))

# pprint.pp(test_roll('1d12'))
# pprint.pp(test_roll('s10+2'))
# pprint.pp(test_roll('1d12t6'))
# pprint.pp(test_roll('1e6'))
# pprint.pp(test_roll('2d6+1'))
# pprint.pp(test_roll('2d8-1'))
# pprint.pp(test_roll('1-2d8'))
# pprint.pp(test_roll('4s12w8'))
# pprint.pp(test_roll('10s12w10t5c6+2-3d6'))
# pprint.pp(test_roll('3d6-1d4+2d8-4+1d8+1'))
# pprint.pp(test_roll('2n6+1d6'))

# AST Testing
# print(ASTNode('1d4+6'))
# print(ASTNode('1d4+d12'))
# print(ASTNode('c'))
#print(ASTNode('2d12+d6-15d10+4-3'))
#print(ASTNode('1d4-2-3-4-2d6+d8'))
#print(ASTNode('1d6-2d4+1d6'))
# t = 'c6d4+1'
# pprint.pp(split_roll_string(t))
# print(ASTNode(t))

# bad tests
#pprint.pp(parse_roll_format('12'))  # need at least one operator
#pprint.pp(parse_roll_format('1d12s5'))  # can only do one
#pprint.pp(parse_roll_format('1c6'))  # bad operator
#pprint.pp(parse_roll_format('1w12'))  # bad operator
#pprint.pp(parse_roll_format('1+12'))  # need at least one operator
#pprint.pp(parse_roll_format('1dc6'))
#pprint.pp(parse_roll_format('1z12'))

# do actual rolling
#pprint.pp(get_roll_data('1d12'))
#pprint.pp(get_roll_data('s10'))
#pprint.pp(get_roll_data('1d12t6'))
#pprint.pp(get_roll_data('1e6'))
#pprint.pp(get_roll_data('2d6+1'))
#pprint.pp(get_roll_data('2d8-1'))
#pprint.pp(get_roll_data('4s12w8'))
#pprint.pp(get_roll_data('s12w10t5c6+2'))

#pprint.pp(test_roll('1d12'))
#pprint.pp(test_roll('s4'))
#pprint.pp(test_roll('1e4t6'))
#pprint.pp(test_roll('2d6+1'))
#pprint.pp(test_roll('2n4-1'))
#pprint.pp(test_roll('4s12w8'))
#pprint.pp(test_roll('4e12'))
#pprint.pp(test_roll('s12w10t5c6+2'))
#pprint.pp(test_roll('2d4c6'))

# test initiative edges

# deck = ['S5', 'D5']
# test_container = new_container()
# run_test(hesitant, (deck, test_container), lambda x: test_container.main_card == 'D5' and test_container.other_cards == ['S5'])

# deck = ['D5', 'S5']
# test_container = new_container()
# run_test(hesitant, (deck, test_container), lambda x: test_container.main_card == 'D5' and test_container.other_cards == ['S5'])

# deck = ['BJ', 'D5']
# test_container = new_container()
# run_test(hesitant, (deck, test_container), lambda x: test_container.main_card == 'BJ' and test_container.other_cards == ['D5'])

# deck = ['D6', 'D5', 'C4', 'S3', 'H2', 'SA']
# test_container = new_container()
# run_test(quick, (deck, test_container), lambda x: test_container.main_card == 'D6' and test_container.other_cards == [])

# deck = ['D5', 'C4', 'S3', 'H2', 'SA']
# test_container = new_container()
# run_test(quick, (deck, test_container), lambda x: test_container.main_card == 'SA' and test_container.other_cards == ['D5', 'C4', 'S3', 'H2'])

# deck = ['D5', 'C4', 'S3', 'H2']
# test_container = new_container()
# run_test(quick, (deck, test_container), lambda x: test_container.main_card == 'H2' and test_container.other_cards == ['D5', 'C4', 'S3'])

# deck = ['S5', 'D5']
# test_container = new_container()
# run_test(levelheaded, (deck, test_container), lambda x: test_container.main_card == 'S5' and test_container.other_cards == ['D5'])

# deck = ['S5', 'D5', 'S6']
# test_container = new_container()
# run_test(levelheaded_imp, (deck, test_container), lambda x: test_container.main_card == 'S6' and test_container.other_cards == ['S5', 'D5'])

# database tests
# characters.add_character("Johnny Test", 123)
# print(characters.add_edges_to_character("Johnny Test", 123, set(["hesitant", "Good at Killing"])))
# print(characters.add_edges_to_character("Johnny Test", 123, set(["quick"])))
# print(characters.add_edges_to_character("Johnny Test", 123, set(["tactician", "tactician-imp"])))
# print(characters.add_edges_to_character("Johnny Test", 123, set(["tactician"])))
# print(characters.add_edges_to_character("Johnny Test", 123, set(["tactician-imp"])))

# print(characters.remove_edges_from_character("Johnny Test", 123, ["quick"]))

# test that we can create an initiative list at all
# characters.add_character("Johnny Test", 123)
# characters.add_character("Not In This Guild", 999)
# characters.add_character("Joe Tactician", 123)
# characters.add_character("Billy Quick", 123)
# characters.add_character("Mindy Slow", 123)
# characters.add_character("Teddy Steady", 123)
# characters.add_character("Andrew Everything", 123)

# characters.add_edges_to_character("Joe Tactician", 123, set(["tactician"]))
# characters.add_edges_to_character("Billy Quick", 123, set(["quick"]))
# characters.add_edges_to_character("Mindy Slow", 123, set(["hesitant"]))
# characters.add_edges_to_character("Teddy Steady", 123, set(["levelheaded"]))
# characters.add_edges_to_character("Andrew Everything", 123, set(["tactician-imp", "quick", "levelheaded-imp"]))

# characters.add_character("Mooks", 123, True)

# test that deleting an initiative list deletes temporary character
# test that creating an initiative list in a channel where one exists deletes the already existing one

# database.new_list(123, 0)
# database.insert_into_list(["Johnny Test", "Mooks"], 123, 0)

# database.new_list(123, 0)
# database.insert_into_list(["Billy Quick", "Redshirts"], 123, 0)

# test creating a temp character in two lists, then deleting only one list, ensuring that the temporary character remains
# database.new_list(123, 0)
# database.insert_into_list(["Johnny Test", "Mooks"], 123, 0)
# database.new_list(456, 0)
# database.insert_into_list(["Johnny Test", "Mooks"], 456, 0)
# database.new_list(123, 0)
# database.insert_into_list(["Billy Quick", "Redshirts"], 123, 0)

# test tabulation
# char_list = [
#     characters.Character("Test Johnson", "AS", 0, ["A Big Idiot", "Cracksmoker"]), 
#     characters.Character("Joe Mook", "2C", 0, unused_cards=["ZZ, AB"]), 
#     characters.Character("Ron Redshirt", "AH", 0)
#     ]
# init_list = characters.InitiativeList(list(PlayingCardDeck), char_list)

# print(init_list.make_initiative_chart())

# test all edges
# database.new_list(123, 0)
# database.delete_list(123,0)

# print(characters.fight(["Johnny Test", "Joe Tactician", "Billy Quick", "Mindy Slow", "Teddy Steady", "Andrew Everything", "Mooks"], 123, 0))
# print(characters.deal_new_card_to_character("Johnny Test", 123, 0))

# print(characters.fight(["Mooks"], 123, 1))
# characters.remove_from_initiative(["Mooks"], 123, 1)
# characters.remove_from_initiative(["Mooks"], 123, 0)

# test rename
# print(characters.rename_character("Johnny Tested", "Johnny Test", 123))

# print(characters.fight(["Johnny Test", "Joe Tactician", "Billy Quick", "Mindy Slow", "Teddy Steady", "Andrew Everything", "Mooks"], 123, 0))
# print()
# print(characters.next_round(123, 0))

# print(characters.choose_card("Billy Quick", "D5", 123, 0))
# print(characters.choose_card("Billy Quick", "D10", 123, 0))
# print(characters.choose_card("Billy Quick", "X10", 123, 0))
# print(characters.quick_redraw("Mooks", 123, 0))
# print(characters.assign_tactician_card("Joe Tactician", "S10", "Johnny Test", 123, 0))
print(characters.assign_tactician_card("Joe Tactician", "S10", "Johnny Test", 999, 0))
