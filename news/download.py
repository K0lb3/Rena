import aiohttp

session = aiohttp.ClientSession()


async def download(url: str = "", headers: dict = {}, data=b"", method="get") -> str:
    """
    Multiple purpose async download function that should be used everywhere where it's possible.
    """
    if headers:
        headers = {str(key): str(val) for key, val in headers.items()}
    if method.lower() == "get":
        async with session.get(url, headers=headers) as r:
            content = await r.content.read()
    elif method.lower() == "post":
        async with session.post(url, headers=headers, data=data) as r:
            content = await r.content.read()
    return content
