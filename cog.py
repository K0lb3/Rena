import discord
from discord.ext import commands, tasks

import re
import asyncio

from news import CLIENT, PROVIDERS, get_news, news_thread, translate_news
from text import HELP

reUser = re.compile(r"^.+?\.\w+(\/|\/pg\/)(.+?)\/*>?$")

bot_owner_id = 281201917802315776


class NewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.bulker.start()

    # == NEWS UPDATE ==
    async def do_bulk(self, provider):
        # bulk insert data here
        try:
            print(provider)
            await news_thread(provider, self.bot)
        except Exception as e:
            print(e)

    @tasks.loop(seconds=360.0)
    async def bulker(self):
        async with self.lock:
            for provider in PROVIDERS:
                await self.do_bulk(provider)

    @bulker.before_loop
    async def before_bulker(self):
        print('News waiting...')
        await self.bot.wait_until_ready()

    # == HELP ==
    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed()
        embed.description = HELP.format(prefix=self.bot.command_prefix)
        # general info
        embed.add_field(name="Author", value=f"<@{bot_owner_id}>\nⱲ0lf#1076")
        embed.add_field(name="Library", value="discord.py (Python 🐍)")
        embed.add_field(
            name="Invite Link",
            value=f"[link](https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot)",
        )
        embed.add_field(name="Source Code", value="[Github](https://github.com/K0lb3/Rena)")
        embed.add_field(name="Sponsor", value="[Github Sponsorship](https://github.com/sponsors/K0lb3)\n[Patreon](https://www.patreon.com/k0lb3)" )
        # stats
        embed.add_field(
            name="Servers", value="{} servers".format(len(self.bot.guilds)))
        total_members = sum(len(s.members) for s in self.bot.guilds)
        total_online = sum(
            1 for m in self.bot.get_all_members() if m.status != discord.Status.offline
        )
        unique_members = set(map(lambda x: x.id, self.bot.get_all_members()))

        embed.add_field(
            name="Total Members", value="{} ({} online)".format(total_members, total_online)
        )
        embed.add_field(name="Unique Members",
                        value="{}".format(len(unique_members)))

        # footnote
        embed.set_footer(
            text="Made with discord.py", icon_url="http://i.imgur.com/5BFecvA.png"
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name="unsubscribe")
    async def unsubscribe(self, ctx):
        # check if user is allowed to subscribe
        author_perms = ctx.channel.permissions_for(ctx.author)
        if not (
                author_perms.administrator
                or author_perms.manage_messages
                or author_perms.manage_webhooks
        ):
            await ctx.send(
                "You don't have any of the permissions which are required to use the command.\nThe command can only be used by someone who has at least one of the following permissions in this channel:\nadministrator, managage_messages, manage_webhooks ."
            )

        # parse input
        provider, user_id, src, dst = parse_input(ctx)
        if provider == False:
            await ctx.send("Invalid host.")
            return

        if not await self.check_if_correct(ctx, provider, user_id, src, dst):
            return

        # remove from db
        col = CLIENT[provider][user_id]
        target = ctx.guild.id, ctx.channel.id
        query = {"tl": False} if not dst else {
            "tl": True, "src": src, "dst": dst}

        cursor = col.find_one(query)
        if cursor:
            if target_in_cursor(target, cursor["targets"]):
                cursor["targets"].remove(list(target))
                if len(cursor["targets"]) == 0:
                    col.delete_one(query)
                else:
                    col.update_one(
                        query, {"$set": {"targets": cursor["targets"]}})
                await ctx.send("Your subscription was removed.")
                return
            else:
                await ctx.send("Couldn't find the subscription.")
        else:
            await ctx.send("Couldn't find the subscription.")

    @commands.command(name="subscribe", alias=["s"])
    async def subscribe(self, ctx):
        # check if user is allowed to subscribe
        author_perms = ctx.channel.permissions_for(ctx.author)
        if not (
                author_perms.administrator
                or author_perms.manage_messages
                or author_perms.manage_webhooks
                or ctx.author.id == bot_owner_id
        ):
            await ctx.send(
                "You don't have any of the permissions which are required to use the command.\nThe command can only be used by someone who has at least one one of the following permissions in this channel:\nadministrator, managage_messages, manage_webhooks ."
            )

        # check if bot can post in the channel
        if not ctx.channel.permissions_for(ctx.me).send_messages:
            await ctx.author.send(
                f"I'm not allowed to post in **#{ctx.channel.name}**.\nPlease give me the Send Messages permission."
            )
            return

        # parse input
        provider, user_id, src, dst = parse_input(ctx)
        if provider == False:
            await ctx.send("Invalid host.")
            return

        if not await self.check_if_correct(ctx, provider, user_id, src, dst):
            return

        # test if the data is valid
        try:
            news, last_check = await get_news(provider, user_id, 0)
        except:
            await ctx.send("Invalid input")
            return

        # add to db
        col = CLIENT[provider][user_id]
        target = ctx.guild.id, ctx.channel.id
        query = {"tl": False} if not dst else {
            "tl": True, "src": src, "dst": dst}

        cursor = col.find_one(query)
        if cursor:
            if target_in_cursor(target, cursor["targets"]):
                await ctx.send("This setting is already registered for this channel.")
                return
            cursor["targets"].append(target)
            col.update_one(query, {"$set": {"targets": cursor["targets"]}})
            # send confirmation message
            await ctx.send(
                "The subscription was successfully registered.\nYou will receive posts as soon as the selected user posts on their platform."
            )
        else:
            # create entry
            col.insert_one({**query, "targets": [target]})

        if dst:
            news = translate_news(news, src, dst)
        for embeds in news:
            for embed in embeds:
                await ctx.send(embed=embed)

    async def check_if_correct(self, ctx, provider, user_id, src, dst):
        embed = discord.Embed(description="Is this correct?\nYes - ✅, No - ❌")
        embed.add_field(name="Provider", value=provider)
        embed.add_field(name="User", value=user_id)
        embed.add_field(name="Translation",
                        value=f"{src} -> {dst}" if dst else "/")
        msg = await ctx.send(embed=embed)

        try:
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
        except:
            pass

        def subscribe_check(reaction, user):
            print(user)
            if (
                    reaction.message.id == msg.id
                    and user.id == ctx.author.id
                    and reaction.emoji in ["✅", "❌"]
            ):
                return True
            return False

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=60.0, check=subscribe_check
            )
        except asyncio.TimeoutError:
            await ctx.send(
                "No reaction input of the command caller was detected.\nPlease try again.\n"
            )
            return False

        if reaction.emoji == "❌":
            await ctx.send(
                f"😖\nI'm sorry if it is my fault.\nIf the detected translation parameter is wrong, please check {self.bot.prefix}help."
            )
            return False
        return True


def parse_input(ctx):
    inp = [x.strip(" ")
           for x in ctx.message.content.split(" ") if x.strip(" ")][1:]
    text = inp[0]
    src = "auto"
    dst = ""
    if len(inp) == 3:
        # no translation
        src = inp[1]
        dst = inp[2]

    try:
        provider = [x for x in PROVIDERS if x in text][0]
    except IndexError:
        return False, False, False, False

    if provider in ["facebook", "twitter"]:
        user_id = reUser.match(text)[2]
    elif provider == "famitsu":
        user_id = text.rstrip("/").rsplit("/", 1)[1]
    elif provider == "steam":
        user_id = text[35:].split("/", 1)[0]

    return provider, user_id, src, dst


def target_in_cursor(target, targets):
    for server, channel in targets:
        if server == target[0] and channel == target[1]:
            return True
    return False


def setup(bot):
    bot.add_cog(NewsCog(bot))
