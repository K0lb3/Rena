import pymongo
import os
from .translator import translate

# import the getter for each provider as the provider
from .facebook import get_posts as facebook
from .twitter import get_tweets as twitter
from .famitsu import get_posts as famitsu
from .steam import get_posts as steam

# mongo db login
CLIENT = pymongo.MongoClient(
    f"mongodb+srv://{os.environ.get('MDB_USER')}:{os.environ.get('MDB_PASS')}@cluster0-4dudj.mongodb.net/test?retryWrites=true&w=majority")

PROVIDERS = [
    "facebook", "twitter", "famitsu", "steam"
]


async def get_news(provider, user_id, last_check):
    """
    Simple general function interface to fetch the news.
    All getter functions have to allign to this format.
    """
    func = globals()[provider]
    return await func(user_id, last_check)


async def news_thread(provider, bot):
    """
    This function updates the news for all registered hooks of a specific provider.
    """
    print("Check", provider)
    database = CLIENT[provider]
    # loop through all ids
    for user_id in database.list_collection_names():
        try:
            col = database[user_id]
            last_check = col.find_one({"id": "last_check"})

            if last_check == None:
                # create one
                last_check = {"id": "last_check", "value": 0}
                col.insert_one(last_check)

            # fetch latest news
            print("Fetch News:", provider, user_id, last_check["value"])
            ret = await get_news(provider, user_id, last_check["value"])
            if not ret or not ret[0]:
                # just in case messages are filtered out falsely
                continue
            print("found new stuff")
            news, last_check = ret

            # update last_check
            col.update_one({"id": "last_check"}, {
                "$set": {"value": last_check}})

            # send the news in all requested languages

            # send to channels without translations
            cursor = col.find_one({"tl": False})
            if cursor:
                await send_to_channels(news, cursor, bot)
            # send to channels with their set translation
            for cursor in col.find({"tl": True}):
                await send_to_channels(
                    translate_news(
                        news, cursor["src"], cursor["dst"]),
                    cursor, bot
                )
        except Exception as e:
            print("Crash", user_id, e)
    print("finished", provider)


async def send_to_channels(news, cursor, bot):
    """
    Sends the embeds to the given webhooks.
    Returns webhooks that raised an error.
    """
    defects = []
    for target in cursor["targets"]:
        try:
            guild_id, channel_id = target
            guild = bot.get_guild(guild_id)
            channel = guild.get_channel(channel_id)

            if not channel:
                continue
            is_news = channel.is_news()

            for embeds in news:
                for embed in embeds:
                    try:
                        msg = await channel.send(embed=embed)
                        if is_news:
                            await msg.publish()
                    except Exception as e:
                        if "Not a well formed URL." in str(e):
                            embed.url = None
                            msg = await channel.send(embed=embed)
                            if is_news:
                                await msg.publish()
                        else:
                            print(e)
        except Exception as e:
            print(e)


def translate_news(news, src, dst):
    posts = news
    for embeds in posts:
        for embed in embeds:
            embed.description = translate(embed.description, src, dst)
    return posts
