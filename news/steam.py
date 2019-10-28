from .download import download
from discord import Embed
from datetime import datetime
import re
import json
from .famitsu import Article

REQUEST_URL = "http://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appId}&count={count}&format=json&maxlength={length}"


async def get_posts(user: str, after: int = 0) -> tuple:
    # get small list without text
    res = await download(REQUEST_URL.format(appId=user, count=10, length=1))
    posts = json.loads(res)["appnews"]["newsitems"]

    # new posts?
    count = len([1 for x in posts if x["date"] > after])

    if not count:
        return None

    # fetch new posts with full body
    res = await download(REQUEST_URL.format(appId=user, count=count, length=0))
    posts = json.loads(res)["appnews"]["newsitems"]

    new = posts[0]["date"]

    ret = []

    for post in posts[::-1]:
        if post["feed_type"] == 0:
            embeds = await Article(
                (None, post["url"], None, post["title"], post["date"], post["contents"])).create_embeds()
            embeds[0].title = post["title"]
            embeds[0].url = post["url"]
            embeds[0].set_author(
                name=post["author"]
            )
        else:
            # header
            embed = Embed(
                title=post["title"],
                url=post["url"],
            )
            embed.set_author(
                name=post["author"]
            )
            embeds = [embed]
            # content
            apply_content(post["contents"], embeds)
            # timestamp
            embeds[-1].timestamp = datetime.utcfromtimestamp(post["date"])
        ret.append(embeds)
    if len(ret):
        return ret, new
    return None


reImg = re.compile(r"""(\[url=(.+?)\])?\[img\](.+?)\[/img\](\[/url\])?""")
reMDChars = re.compile(r"""([\*_\|])""")
reFORMAT = list(map(lambda x: (re.compile(x[0]), x[1]), [
    (r"""(\[i\](.+?)\[/i\])""", "*{0}*"),  # cursive
    (r"""(\[b\](.+?)\[/b\])""", "**{0}**"),  # fat
    (r"""(\[h\d\](.+?)\[/h\d\])""", "__{0}__"),  # header
    (r"""(<span.+?>(.+?)</span>)""", "{0}"),  # remove span stuff
    (r"""(<a .{0,256}?href="(.{0,256}?)" .{0,256}?rel="noopener noreferrer">(.+?)</a>)""", "[{1}]({0})"),
    (r"""(\[url=(.+?)\](.+?)\[/url\])""", "[{1}]({0})"),
    (r"""(\[url=(.+?)\]\[/url\])""", "({0})"),
    (r"""(\[previewyoutube=(.+?)(;full)?\](\[/previewyoutube\])?)""", "[Youtube](https://www.youtube.com/watch?v={0})"),
    (r"""(\[\\\*\](.+?)\[/\\\*\])""", "\n- {0}\n")
]))
reOther = re.compile(r"(\[/?\w+?\])")


def apply_content(text, embeds):
    embed = embeds[0]
    # split text into parts - [text, img, text, ...]
    split = reImg.split(text)
    for i, item in enumerate(split):
        if i % 5 == 0:  # text
            if not item:
                continue
            # format text
            item = html_to_markdown(item)
            # add text
            add_text(item, embeds)
        elif (i - 3) % 5 == 0:  # img
            # 1 - [url=]
            # 2 - url - link in image
            # 4 - [/url]
            if embed.image.url != Embed.Empty:
                embed = Embed()
                embeds.append(embed)
            embed.set_image(url=item.replace("{STEAM_CLAN_IMAGE}",
                                             "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/clans"))
            embed = Embed()
            embeds.append(embed)

    # clean empty embeds
    i = 0
    while i < len(embeds):
        if (not embeds[i].description) and not (embeds[i].image):
            embeds.pop(i)
        else:
            i += 1


def html_to_markdown(item):
    for char in set(reMDChars.findall(item)):
        item = item.replace(char, f"\\{char}")

    for regex, mdk in reFORMAT:
        for ori, *sub in regex.findall(item):
            item = item.replace(ori, mdk.format(*sub))
    for elem in set(reOther.findall(item)):
        item = item.replace(elem, "")

    return item


def add_text(text, embeds):
    if len(text) == 0:
        return
    embed = embeds[-1]
    old_len = len(embed.description)
    if old_len == 0:
        embed.description = ""
    # short enough
    if len(text) + old_len < 2048 - 1:
        embed.description += "\n" + text
    # too long - text has to be split
    else:
        for x in ["\n", ".", ",", " "]:
            index = text[:2048 - old_len - 2].rfind(x)
            if index != -1:
                break
        embed.description += "\n" + text[:index + 1]

        embeds += [Embed()]
        add_text(text[index + 1:], embeds)
