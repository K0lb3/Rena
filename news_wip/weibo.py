import re
import requests


def new_session() -> requests.Session:
    s = requests.Session()
    s.headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0")
    # get tid for sub & subp cookie request
    res = s.post("https://passport.weibo.com/visitor/genvisitor", data={"cb": "gen_callback",
                                                                        "fp": """{"os":"1","browser":"Gecko84,0,0,0","fonts":"undefined","plugins":""}"""})
    tid = re.search(r'"tid":"(.+?)"', res.text)[1]
    # get sub & subp cookies
    res = s.get(f"https://passport.weibo.com/visitor/visitor?a=incarnate&t={tid}&cb=cross_domain&from=weibo")
    # session ready for news feed requests
    return s
