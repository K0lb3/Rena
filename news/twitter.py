import json
from datetime import datetime
from urllib.parse import urlencode
from .download import download

from discord import Embed
import base64
import os


class Twitter:
    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    async def get_token(self):
        tokenCredential = base64.urlsafe_b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode("utf8")).rstrip(
            b"=").decode("utf8")
        self.token = json.loads(await download(
            url="https://api.twitter.com/oauth2/token",
            headers={
                "Authorization": "Basic " + tokenCredential,
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
            },
            data="grant_type=client_credentials".encode("utf8"),
            method="POST"))["access_token"]

    async def get_timeline(self, **kwargs):
        """
            user_id	:	"The ID of the user for whom to return results",
            screen_name :	"The screen name of the user for whom to return results.		noradio",
            since_id : 	"Returns results with an ID greater than (that is, more recent than) the specified ID. There are limits to the number of Tweets that can be accessed through the API. If the limit of Tweets has occured since the since_id, the since_id will be forced to the oldest ID available.		12345",
            count :	"Specifies the number of Tweets to try and retrieve, up to a maximum of 200 per distinct request. The value of count is best thought of as a limit to the number of Tweets to return because suspended or deleted content is removed after the count has been applied. We include retweets in the count, even if include_rts is not supplied. It is recommended you always send include_rts=1 when using this API method.",		
            max_id :	"Returns results with an ID less than (that is, older than) or equal to the specified ID.		54321",
            trim_user : 	"When set to either true , t or 1 , each Tweet returned in a timeline will include a user object including only the status authors numerical ID. Omit this parameter to receive the complete user object.		true",
            exclude_replies :	"This parameter will prevent replies from appearing in the returned timeline. Using exclude_replies with the count parameter will mean you will receive up-to count tweets — this is because the count parameter retrieves that many Tweets before filtering out retweets and replies.		true",
            include_rts : "",
        """
        await self.get_token()
        if "tweet_mode" not in kwargs:
            kwargs['tweet_mode'] = 'extended'

        return json.loads(await download(
            url=f"https://api.twitter.com/1.1/statuses/user_timeline.json?{urlencode(kwargs)}",
            headers={
                "Authorization": f'Bearer {self.token}'
            },
            method="GET"))


twitter = Twitter(os.environ.get("twitter_consumer_key"), os.environ.get("twitter_consumer_secret"))


def set_media(self, media):
    if media['type'] in ['photo', 'animated_gif']:
        self.set_image(url=media['media_url'])
    elif media['type'] == 'video':
        bitrate = 0
        for v in media['video_info']['variants']:
            if 'bitrate' in v and v['bitrate'] > bitrate:
                bitrate = v['bitrate']
                video = v
        self.set_image(url=media['media_url'])
        if self.description:
            self.description += f"\n[🎞]({v['url']})"
        else:
            self.description = f"[🎞]({v['url']})"
    else:
        print(media['id'], media['type'])


setattr(Embed, 'set_media', set_media)


async def get_tweets(user_id: str, last_check: int):
    if last_check:
        tweets = await twitter.get_timeline(screen_name=user_id, since_id=last_check)
    else:
        tweets = await twitter.get_timeline(screen_name=user_id)

    if len(tweets):
        # return embeds, latest_id
        return [tweet_to_embed(tweet) for tweet in tweets[::-1] if not tweet.get("in_reply_to_status_id", None)], \
               tweets[0]['id']
    else:
        return None


def tweet_to_embed(tweet: dict) -> list:
    retweet = 'retweeted_status' in tweet
    if retweet:
        user = tweet['retweeted_status']['user']
    else:
        user = tweet['user']
    color = int(user['profile_link_color'].replace('#', ''), 16)
    timestamp = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')

    embed = Embed(
        title='Tweet' if not retweet else f"{tweet['user']['name']} retweeted {user['name']}",
        url=f"https://twitter.com/{tweet['user']['screen_name']}/status/{tweet['id_str']}",
        color=color,
    )
    embed.set_author(
        name=user['name'],
        url=f"https://twitter.com/{user['screen_name']}",
        icon_url=user['profile_image_url'],
    )
    embeds = [embed]

    # text
    if retweet:
        tweet = tweet['retweeted_status']

    offset = 0
    text = tweet['full_text']
    entities = tweet['entities']

    for entity in entities['hashtags']:
        b, e = entity['indices']
        insert = f"[{entity['text']}](https://twitter.com/hashtag/{entity['text']})"
        text = f"{text[:b + offset]}{insert}{text[e + offset:]}"
        offset += len(insert) - e + b

    for entity in entities['user_mentions']:
        b, e = entity['indices']
        insert = f"[{entity['name']}](https://twitter.com/{entity['screen_name']})"
        text = f"{text[:b + offset]}{insert}{text[e + offset:]}"
        offset += len(insert) - e + b

    for entity in entities['urls']:
        b, e = entity['indices']
        insert = f"[{entity['display_url']}]({entity['expanded_url']})"
        text = f"{text[:b + offset]}{insert}{text[e + offset:]}"
        offset += len(insert) - e + b

    b, e = tweet['display_text_range']
    embed.description = text[b:e + offset]

    if 'extended_entities' in tweet and 'media' in tweet['extended_entities']:
        embed.set_media(tweet['extended_entities']['media'][0])
        # create new embeds which show the images
        for media in tweet['extended_entities']['media'][1:]:
            embed = Embed(color=color)
            embed.set_media(media)
            embeds.append(embed)

        if embed.image.url.endswith('.gif'):
            embed.set_image(url="https://i.imgur.com/RG8vDmV.png")
    else:
        embed.set_image(url="https://i.imgur.com/RG8vDmV.png")

    # final touch
    embed.timestamp = timestamp

    # debugging
    # import requests
    # from discord import Webhook, RequestsWebhookAdapter
    # webhook = Webhook.partial(512930867526631445, '9Hbqz-8TOJ0T9gUwzCiXlACmmjihQUbfPBKNs_NAHwYlIqSYJALeD7vOKmK4TMglVM65', adapter=RequestsWebhookAdapter())
    # webhook.send(embeds = embeds, username='Foo')
    # print()

    return embeds
