import characters
import discord
import os # default module
from die_roller import *
from dotenv import load_dotenv
from enum import Enum

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
        await ctx.respond(package_roll(msg, roll_data, **roll_results))
    except ValueError as e:
        await ctx.respond(e)
    except Exception:
        await ctx.respond("Some other error happened, see the log for details.")
        raise
    
# INITIATIVE

@bot.slash_command(name="fight", description="Start a new fight")
async def fight(ctx: discord.ApplicationContext, characters: str):
    await ctx.respond("NYI")

@bot.slash_command(name="deal", description="Deal in new characters")
async def deal(ctx: discord.ApplicationContext, characters: str):
    await ctx.respond("NYI")

@bot.slash_command(name="remove", description="Remove a character from the current fight")
async def remove(ctx: discord.ApplicationContext, characters: str):
    await ctx.respond("NYI")

@bot.slash_command(name="card", description="Give characters a card")
async def card(ctx: discord.ApplicationContext, characters: str):
    await ctx.respond("NYI")

@bot.slash_command(name="list", description="Lists everyone in the current fight")
async def card(ctx: discord.ApplicationContext):
    await ctx.respond("NYI")

@bot.slash_command(name="give_tactician_card", description="Gives a chraracter in the current fight a tactician card")
async def give_tactician_card(ctx: discord.ApplicationContext, card_number: int, character: str):
    await ctx.respond("NYI")

# CHARACTERS AND BENNIES
@bot.slash_command(name="new_character", description="Create a new character")
async def new_character(ctx: discord.ApplicationContext, character_name: str):
    try:
        characters.add_character(character_name, ctx.guild_id, False)
        await ctx.respond(f"Created character {character_name}.")
    except Exception:
        await ctx.respond("An error occurred. Character was not created.")

@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, character_name: str):
    try:
        characters.delete_character(character_name, ctx.guild_id)
        await ctx.respond(f"Deleted character {character_name}.")
    except LookupError:
        await ctx.respond(f"Character {character_name} does not exist.")

@bot.slash_command(name="add_edges", description="Give a character edges, comma separated")
async def add_edges(ctx: discord.ApplicationContext, character_name: str, edges: str):
    edges_list = set(map(lambda x: x.strip(), edges.split(',')))

    try:
        invalid = characters.add_edges_to_character(character_name, ctx.guild_id, edges_list)
        if len(invalid) == 0:
            await ctx.respond("Successfully added edges")
        else:
            await ctx.respond("The following edges are invalid (valid ones were added):" + str(invalid))
    except LookupError:
        await ctx.respond(f"Character {character_name} does not exist.")

@bot.slash_command(name="remove_edges", description="Remove an edge from a character")
async def remove_edges(ctx: discord.ApplicationContext, character_name: str, edges: str):
    edges_list = set(map(lambda x: x.strip(), edges.split(',')))
    
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
