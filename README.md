# Rena

A free news bot for Discord developed in python via discord.py.
It supports Facebook, Twitter, Steam, and Famitsu.

[Invite Link](https://discordapp.com/oauth2/authorize?client_id=638372372491010048&scope=bot)
 
## Functions

### !help

Displays a help message that says how the following two commands have to be used.

### !subscribe
 
```!subscribe <link> <src> <dst>```

#### arguments
- link - a link to the target (Facebook, Twitter)
- src - (optional) the language code of the original language
- dst - (optional) the language code of the target language

Please check Google Language Codes to find the correct language codes.

#### examples

##### Twitter
```!subscribe https://twitter.com/discordapp```
this will lead to the bot reposting all tweets made by DiscordApp in the channel the command was called.

##### Facebook
```!subscribe https://twitter.com/WOTV_FFBE ja en```
this will lead to the bot reposting all tweets made by WOTV FFBE in the channel the command was called.
The reposted tweets will be translated from Japanese (ja) to English (en).

##### Famitsu:
```!subscribe https://app.famitsu.com/category/game-tips/WOTV_FFBE/ ja en```

##### Steam:
```!subscribe https://store.steampowered.com/app/470310/TROUBLESHOOTER_Abandoned_Children/```


### !unsubscribe

This command can be used to remove a subscription.

```!unsubscribe <link> <src> <dst>```

The parameters have to be the same as during the subscription.

#### example
```!unsubscribe https://twitter.com/WOTV_FFBE ja en```

## How it works

The bot fetches the data from the sources via different means.
Afterward, the fetched data is formatted into a format that suits discord.




The news from Twitter and Stream are fetched via their respective api.

Facebook's api requirements are too strict for normal developers,
so this bot scraps the content from their webpage.

Famitsu has no api, so web scraping is used here as well.

## Set-Up

Following python modules are required to run this bot:

- ``discord.py`` - Discord interface
- ``pymongo`` - MongoDB interface 
- ``bs4`` - web scrapper library
- ``pygoogletranslation`` - news translation
- ``dnspython`` - requirement for pygoogletranslation
- ``emoji`` - required for seamless translations

Next to the modules following environment variables have to be set.
For testing, this can also be done in settings.py

```python
import os
# twitter login
os.environ["twitter_consumer_key"] = "twitter consumer key"
os.environ["twitter_consumer_secret"] = "twitter consumer secret"
# MongoDB login
os.environ["MDB_USER"] = "mongo db username"
os.environ["MDB_PASS"] = "mongo db password"
# Discord bot login
os.environ["DISCORD_BOT_TOKEN"] = "token of your discord bot"
```
