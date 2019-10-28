import emoji
from pygoogletranslation import Translator
import re
from http.client import HTTPException

emoji_delimiters = ("{[", "]}")
reEmoji = re.compile(r'(\{\[\s*([\w\d]+)s*\]\})')
reLink = re.compile(r'\[(.{1,64}?)\] {0,1}\((.+?)\)')


def translate(text, src, dst):
    if not text or src == dst:
        return text
    translator = Translator()
    translator = Translator(service_urls=['translate.google.com'])
    try:
        # save hidden links
        links = reLink.findall(text)
        # replace emojis
        str_demoji = emoji.demojize(text, delimiters=emoji_delimiters)
        # translate
        tran = translator.translate(str_demoji, src=src, dest=dst).text
        # fix emojis
        for match in reEmoji.findall(tran):
            tran = tran.replace(match[0], emoji.emojize(f":{match[1].lower()}:"))
        # fix hidden links
        offset = 0
        for i, match in enumerate(reLink.finditer(tran)):
            b, e = match.regs[0]
            insert = f"[{match[1]}]({links[i][1]})"
            tran = f"{tran[:b + offset]}{insert}{tran[e + offset:]}"
            offset += len(insert) - e + b
        return tran
    except HTTPException:
        return translate(text, src, dst)
    except:
        pass
    return text


if __name__ == "__main__":
    text = '✨リリースまであと【7日】✨\n\n[FFBE幻影戦争](https://twitter.com/hashtag/FFBE幻影戦争) の配信日まで、あと1週間‼️\n\nそこで本日より、モデルチーム制作の記念画像とともにカウントダウン🕑を実施します😀\n\n今日は、リリシュ(CV [内山夕実](https://twitter.com/hashtag/内山夕実))、ラマダ(CV [安野希世乃](https://twitter.com/hashtag/安野希世乃))、リアート（CV [芹澤優](https://twitter.com/hashtag/芹澤優)）、キトン(CV [石川由依](https://twitter.com/hashtag/石川由依))のリオニスの女戦士が登場⚔️'
    print(translate(text, 'ja', 'en'))
