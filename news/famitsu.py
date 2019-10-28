import re
from datetime import datetime

from discord import Embed

from .download import download
from .twitter import get_tweets

reArticles = re.compile(
    r'''<li class="stress-outer"><div class="article-main">.+?href="(.+?)".+?src="(.+?)".+?title="(.+?)">.+?<.+?date">(.+?)<\/span>''')
reContent = re.compile(
    r'''<div id="entry-body">(.+?)(<div class='news_section'>|<div class="social-btn lower">)''')
reSubHeader = re.compile(r'''<h\d>(.+?)</h\d>''')
reImg = re.compile(
    r'''<img class="lazy.+?data-lazy-type="image" data-lazy-src="(.+?)".+?>''')
reTwitterBox = re.compile(
    r'''<blockquote class="twitter-tweet".+?>.+?"(https:\/\/twitter.com\/([^\(\)<>]+?)\/status\/(.+?))("|\?.+?").+<\/blockquote>''')

HEADER = 0
TEXT = 1
IMAGE = 2
EMBED = 3


async def get_posts(user: str, after: int = 0) -> tuple:
    # download the page and parse the titles
    html = (await download(f"https://app.famitsu.com/category/game-tips/{user}/")).decode("utf8")
    articles = [Article(a) for a in reArticles.finditer(html)]

    # check which article is new
    new_articles = [
        article
        for article in articles
        if article.date.timestamp() > after
    ]

    if new_articles:
        return [await a.create_embeds() for a in new_articles][::-1], int(new_articles[0].date.timestamp())
    return None


def fix_html_text(text):
    def convert_bracket(match):
        GROUP = {
            "a": " ",
            "p": "\n",
            "b": "**",
            "del": "~~",
            "i": "*",
            "lt": "<",
            "nbsp": " ",
            "gt": ">",
            "amp": "&",
            "quot": "\"",
            "apos": "\'",
            "copy": "©",
            "reg": "®",
            "#039": "\'",
            "cent": "¢",
            "pound": "£",
            "yen": "¥",
            "euro": "€",
        }
        return GROUP.get(match[1], "")

    return re.sub(r"<\/?(.+?)>|\&(.+);", convert_bracket, text)


class Article:
    def __init__(self, args):
        self.link = args[1]
        self.img = args[2]
        self.title = args[3]
        self.date = datetime.fromisoformat(args[4]) if isinstance(args[4], str) else datetime.utcfromtimestamp(args[4])
        self.data = args[5] if len(args) == 6 else None

    async def load_content(self):
        if self.data:
            content = self.data
        else:
            html = await download(self.link).read().decode("utf8")
            content = reContent.findall(html)[0][0]

        data = []
        # split into article parts via sub headers
        split_content = reSubHeader.split(content)
        data.append((TEXT, split_content[0]))
        for i in range(1, len(split_content), 2):
            data.append((HEADER, split_content[i]))
            data.extend(await parse_text(split_content[i + 1]))

        return data

    async def create_embeds(self):
        embed = Embed(title=self.title, description="", url=self.link)
        embeds = [embed]
        for typ, text in await self.load_content():
            if isinstance(text, str):
                text = fix_html_text(text)
                if len(text) < 2:
                    continue
            if typ == HEADER:
                if len(embed.description) + len(text) + 6 < 2048:
                    embed.description += f"\n\n__{text}__"
                else:
                    embed = Embed(description=f"__{text}__")
                    embeds.append(embed)
            elif typ == TEXT:
                if len(embed.description) + len(text) + 1 < 2048:
                    embed.description += f"\n{text}"
                else:
                    embed = Embed(description=f"{text}")
                    embeds.append(embed)
            elif typ == IMAGE:
                embed.set_image(url=text)
                embed = Embed(description="")
                embeds.append(embed)
            elif typ == EMBED:
                for e in text:
                    embeds.append(e)
                embed = Embed(description="")
                embeds.append(embed)

        for embed in embeds:
            embed.color = 0xff148c
        embed.timestamp = self.date

        return embeds


async def parse_text(text):
    ret = []
    # check images
    split_text = reImg.split(text)
    if len(split_text) > 1:
        ret.extend(await parse_text(split_text[0]))
        for j in range(1, len(split_text), 2):
            ret.append((IMAGE, split_text[j]))
            ret.extend(await parse_text(split_text[j + 1]))
        return ret
    # check twitter
    split_text = reTwitterBox.split(text)
    if len(split_text) > 1:
        ret.extend(await parse_text(split_text[0]))
        for j in range(1, len(split_text), 5):
            ret.append(
                (EMBED, await get_tweets(split_text[j + 1], int(split_text[j + 2]) - 1)[0][0]))
            ret.extend(await parse_text(split_text[j + 4]))
        return ret

    return [(TEXT, text)]


if __name__ == "__main__":
    get_posts("wotv_ffbe")
