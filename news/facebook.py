import re
from datetime import datetime

from bs4 import BeautifulSoup
from discord import Embed

from .download import download

reExposedLink = re.compile(r'(\w+)[\(\[: ]+(https?:\/\/.+?[ \)\]])')


async def get_posts(user: str, after: int = 0) -> tuple:
    posts = []

    # request posts
    # html = open('html2.html','rb').read().decode('utf8')#
    html = await download(REQUEST_URL.format(user), headers=REQUEST_HEADERS)
    # parse html via BeatifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    new = after
    # loop over every found post
    for post in soup.select('div._1dwg'):
        try:
            # extract data from the post
            header, content, media = post.contents[-1].contents[:3]
            color = 0x0000FF
            # HEADER
            # name and titile
            h = header.select_one('span.fcg')
            title = h.text
            name = h.contents[0].contents[0].text
            # post link and url
            h = header.select_one('span.fsm').contents[0]
            url = h['href']
            timestamp = int(h.contents[0]['data-utime'])

            if timestamp <= after:
                continue  # first post is a pinned old message

            if timestamp > new:
                new = timestamp

            embed = Embed(
                title=title,
                url=f"https://www.facebook.com{url}",
                color=color,
            )
            embed.set_author(
                name=name,
                url=f"https://twitter.com/{user}",
                icon_url=header.select_one('img')["src"],
            )
            embeds = [embed]

            # CONTENT
            def text(item):
                return item if isinstance(item, str) else item.text

            if content.contents:
                embed.description = '\n'.join(
                    text(c) for c in content.contents[0].contents if text(c) not in ['...', 'See More'])
                # replace exposed links with embeded links
                for match in reExposedLink.finditer(embed.description):
                    embed.description = embed.description.replace(match[0], f"[{match[1]}]({match[2]}) ")

                # split too long text
                if len(embed.description) > 2048:
                    sections = []
                    description = embed.description
                    while len(description) > 2048:
                        last_sentence_end = description[:2048].rfind(".") + 1
                        sections.append(description[0:last_sentence_end])
                        description = description[last_sentence_end:].lstrip(' ').lstrip('\t').lstrip('\n')
                    sections.append(description)

                    embed.description = sections[0]
                    for section in sections:
                        embed = Embed(description=section, color=color)
                        embeds.append(embed)
            # MEDIA
            images = media.select('img')
            if images:
                embed.set_image(url=images[0]['src'])
                # create new embeds which show the images
                for img in images[1:]:
                    if img['src'].endswith(('.png', '.jpg', '.jpeg')):
                        embed = Embed(color=color)
                        embed.set_image(url=img['src'])
                        embeds.append(embed)
            else:
                embed.set_image(url="https://i.imgur.com/RG8vDmV.png")

            # final touch
            embed.timestamp = datetime.utcfromtimestamp(timestamp)
            posts.append(embeds)

            # debugging
            # import requests
            # from discord import Webhook, RequestsWebhookAdapter

            # webhook = Webhook.partial(512930867526631445, '9Hbqz-8TOJ0T9gUwzCiXlACmmjihQUbfPBKNs_NAHwYlIqSYJALeD7vOKmK4TMglVM65', adapter=RequestsWebhookAdapter())
            # webhook.send(embeds = embeds, username='Foo')
            # print()
        except:
            continue
    if len(posts):
        return posts[::-1], new
    return None


REQUEST_URL = "https://www.facebook.com/{}/posts/?ref=page_internal&mt_nav=1"
REQUEST_HEADERS = {
    'accept-encoding': 'gzip',
    'accept-language': 'en-US,en;q=0.9,en-US;q=0.8,en;q=0.7',
    'upgrade-insecure-requests': 1,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36'
}

if __name__ == '__main__':
    get_posts('LangrisserEN', 0)
