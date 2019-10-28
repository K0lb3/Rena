HELP = """
__**{prefix}subscribe**__

usage: ``{prefix}subscribe <link> <src> <dst>``
**link**
    a link to the target (facebook, twitter)

**src (optional)**
    the language code of the original language
**dst (optiona)**
    the language code of the target language

Please check [Google Language Codes](https://cloud.google.com/translate/docs/languages) to find the correct language codes.

__examples__
Twitter:
``{prefix}subscribe https://twitter.com/discordapp``
this will lead to the bot reposting all tweets made by DiscordApp in the channel the command was called.

Facebook:
``{prefix}subscribe https://twitter.com/WOTV_FFBE ja en``
this will lead to the bot reposting all tweets made by WOTV FFBE in the channel the command was called.
The reposted tweets will be translated from japanese (ja) to english (en).

Famitsu:
``{prefix}subscribe https://app.famitsu.com/category/game-tips/WOTV_FFBE/ ja en``

Steam:
``{prefix}subscribe https://store.steampowered.com/app/470310/TROUBLESHOOTER_Abandoned_Children/``

__**{prefix}unsubscribe**__

This command can be used to remove a subscription.

usage: ``{prefix}unsubscribe <link> <src> <dst>``

The parameters have to be the same as during the subscription.

__example__
``{prefix}unsubscribe https://twitter.com/WOTV_FFBE ja en``

__**Bot Data**__
"""