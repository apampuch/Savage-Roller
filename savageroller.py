import characters
import discord
import os # default module
from die_roller import *
from dotenv import load_dotenv

load_dotenv() # load all the variables from the env file
bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx: discord.ApplicationContext):
    await ctx.respond("Hey!")

# ROLLS

@bot.slash_command(name="roll", description="Roll a die")
async def roll(ctx: discord.ApplicationContext, msg: str):
    try:
        roll_data = parse_tokens(msg)
        roll_results = roll_savage_dice(roll_data)
        await ctx.respond(package_roll(msg, roll_data, **roll_results))  # type: ignore
    except ValueError as e:
        await ctx.respond(e)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

# INITIATIVE
@bot.slash_command(name="fight", description="Start a new fight")
async def fight(ctx: discord.ApplicationContext, char_names: str):
    chars_list = list(set(map(lambda x: x.strip(), char_names.split(','))))

    try:
        message = "```" + characters.fight(chars_list, ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

@bot.slash_command(name="new_round", description="Starts a new round of combat.")
async def new_round(ctx: discord.ApplicationContext):
    try:
        message = "```" + characters.next_round(ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

@bot.slash_command(name="deal_in", description="Deal in new characters")
async def deal_in(ctx: discord.ApplicationContext, char_names: str):
    chars_list = list(set(map(lambda x: x.strip(), char_names.split(','))))

    try:
        message = "```" + characters.add_to_initiative(chars_list, ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

@bot.slash_command(name="remove", description="Remove a character from the current fight")
async def remove(ctx: discord.ApplicationContext, char_names: str):
    chars_list = list(set(map(lambda x: x.strip(), char_names.split(','))))

    try:
        message = "```" + characters.remove_from_initiative(chars_list, ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

@bot.slash_command(name="give_card", description="Give a characters a new card")
async def give_card(ctx: discord.ApplicationContext, char_name: str):
    try:
        message = "```" + characters.deal_new_card_to_character(char_name, ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

@bot.slash_command(name="list", description="Lists everyone in the current fight")
async def list_fight(ctx: discord.ApplicationContext):
    try:
        message = "```" + characters.show_list(ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise


@bot.slash_command(name="assign_tactician_card", description="Assigns a character a tactician card from another character's tactician card lst.")
async def assign_tactician_card(ctx: discord.ApplicationContext, tactician_character: str, card: str, recipient_character: str):
    try:
        message = "```" + characters.assign_tactician_card(tactician_character, card, recipient_character, ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

@bot.slash_command(name="choose_card", description="Swaps a given character's action card with another one from among their unused cards.")
async def choose_card(ctx: discord.ApplicationContext, char_name: str, card: str):
    try:
        message = characters.choose_card(char_name, card, ctx.guild_id, ctx.channel_id)
        await ctx.respond(message)
    except ValueError as e:
        await ctx.respond(str(e))
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

@bot.slash_command(name="quick_redraw", description="Makes a character redraw cards until their current card is greater than 5.")
async def quick_redraw(ctx: discord.ApplicationContext, char_name: str):
    try:
        message = "```" + characters.quick_redraw(char_name, ctx.guild_id, ctx.channel_id) + "```"
        await ctx.respond(message)
    except Exception:
        await ctx.respond("An error occurred, see the log for details.")
        raise

# CHARACTERS AND BENNIES
@bot.slash_command(name="new_character", description="Create a new character")
async def new_character(ctx: discord.ApplicationContext, char_name: str):
    try:
        message = characters.add_character(char_name, ctx.guild_id, False)
        await ctx.respond(message)
    except ValueError as e:
        await ctx.respond(str(e))
    except Exception:
        await ctx.respond("An error occurred. Character was not created.")

@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, character_name: str):
    try:
        message = characters.remove_character(character_name, ctx.guild_id)
        await ctx.respond(message)
    except LookupError:
        await ctx.respond(f"Character {character_name} does not exist.")

@bot.slash_command(name="rename_character", description="Rename a character")
async def rename_character(ctx: discord.ApplicationContext, old_name: str, new_name: str):
    try:
        message = characters.rename_character(old_name, new_name, ctx.guild_id)
        await ctx.respond(message)
    except ValueError as e:
        await ctx.respond(str(e))
    except Exception:
        await ctx.respond("An error occurred. Character was not created.")

@bot.slash_command(name="add_edges", description="Give a character edges, comma separated")
async def add_edges(ctx: discord.ApplicationContext, character_name: str, edges: str):
    # convert comma separated list to set
    edges_list = set(map(lambda x: x.strip(), edges.split(',')))

    try:
        message = characters.add_edges_to_character(character_name, ctx.guild_id, edges_list)
        await ctx.respond(message)
    except LookupError:
        await ctx.respond(f"Character {character_name} does not exist.")

@bot.slash_command(name="remove_edges", description="Remove an edge from a character")
async def remove_edges(ctx: discord.ApplicationContext, character_name: str, edges: str):
    edges_list = list(map(lambda x: x.strip(), edges.split(',')))
    
    try:
        deleted_rowcount = characters.remove_edges_from_character(character_name, ctx.guild_id, edges_list)
        await ctx.respond(f"Deleted {deleted_rowcount} edges.")
    except LookupError:
        await ctx.respond(f"Character {character_name} does not exist.")

# BACKLASH
@bot.slash_command(name="tarot_backlash", description="Draw cards from tarot deck to start backlash")
async def tarot_backlash(ctx: discord.ApplicationContext, msg: str):
    await ctx.respond("NYI")

bot.run(os.getenv("TOKEN")) # run the bot with the token
