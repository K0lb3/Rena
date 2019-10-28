import discord
from discord.ext import commands
import os

import sys
import traceback

try:
    # set environ vars for local session
    import settings
except ImportError:
    pass

initial_extensions = ['cog']

bot = commands.Bot(command_prefix="!", description='news bot')
bot.max_messages = 1  # no need to keep an unnecessary amount of messages in the cache
bot.remove_command("help")

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()


@bot.event
async def on_ready():
    print(
        f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    game = discord.Game(name='!help')
    await bot.change_presence(status=discord.Status.online, activity=game)
    print(f'Successfully logged in and booted...!')
    print(*[guild.name for guild in bot.guilds])
    print("------")


@bot.command(name="ping")
async def ping(ctx):
    """
    Simple test to check if the bot is alive or dead.
    """
    await ctx.send("pong")


bot.run(os.environ.get("DISCORD_BOT_TOKEN"), bot=True, reconnect=True)
