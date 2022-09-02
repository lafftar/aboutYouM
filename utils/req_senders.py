import asyncio
import functools
import re
from asyncio import sleep
from random import choice
import aiohttp
import anyio
import httpx
from aiohttp import client_exceptions

from utils.tls_launcher import TLSLauncher
from utils.tools import print_req_info


async def send_req(req_obj: functools.partial, num_tries: int = 5) -> \
        httpx.Response | aiohttp.ClientResponse | None:
    """
    Central Request Handler. All requests should go through this.
    :param num_tries:
    :param req_obj:
    :return:
    """
    for _ in range(num_tries):
        try:
            item = await req_obj()
            return item
        except (
                # httpx errors
                httpx.ConnectTimeout, httpx.ProxyError, httpx.ConnectError,
                httpx.ReadError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError,

                # aiohttp errors
                asyncio.exceptions.TimeoutError, client_exceptions.ClientHttpProxyError,
                client_exceptions.ClientProxyConnectionError,
                client_exceptions.ClientOSError,
                client_exceptions.ServerDisconnectedError,

                # any io errors
                anyio.ClosedResourceError
                ) as e:
            print(e)
            await sleep(2)
    return


def robot_cookie(cookie: str, parent_domain: str):
    items = cookie.split(';')
    SameSite = HttpOnly = Secure = Domain = Path = Expires = Comment = MaxAge = CookieName = CookieValue \
        = Size = Sessionkey = Version = Priority = None
    CookieName = CookieValue = None
    idx = len(items) - 1
    while idx >= 0:
        item = items[idx].strip()
        idx -= 1
        if not item:
            continue
        SameSiteMatched = re.match(r'^SameSite(.*)?', item, re.I)
        HttpOnlyMatched = SameSiteMatched or re.match(r'^HttpOnly(.*)$', item, re.I)
        SecureMatched = HttpOnlyMatched or re.match(r'^Secure(.*)$', item, re.I)
        DomainMatched = SecureMatched or re.match(r'^Domain(.*)?', item, re.I)
        PathMatched = DomainMatched or re.match(r'^Path(.*)?', item, re.I)
        ExpiresMatched = PathMatched or re.match(r'^Expires(.*)?', item, re.I)
        CommentMatched = ExpiresMatched or re.match(r'^Comment(.*)?', item, re.I)
        MaxAgeMatched = ExpiresMatched or re.match(r'^Max-Age=(.*)?', item, re.I)
        VersionMatched = MaxAgeMatched or re.match(r'^Version=(.*)?', item, re.I)
        PriorityMatched = VersionMatched or re.match(r'^priority=(.*)?', item, re.I)
        matched = SameSiteMatched or HttpOnlyMatched or SecureMatched or DomainMatched or PathMatched or \
                  ExpiresMatched or CommentMatched or MaxAgeMatched or VersionMatched or PriorityMatched
        if matched:
            val = matched.groups(0)[0].lstrip('=')
            if matched == SameSiteMatched:
                SameSite = val if val.lower() in ['strict', 'lax', 'none'] else None
            elif matched == HttpOnlyMatched:
                HttpOnly = True
            elif matched == SecureMatched:
                Secure = True
            elif matched == DomainMatched:
                Domain = val
            elif matched == PathMatched:
                Path = val
            elif matched == PathMatched:
                Path = val
            elif matched == ExpiresMatched:
                Expires = val
            elif matched == CommentMatched:
                Comment = val
            elif matched == MaxAgeMatched:
                MaxAge = val
            elif matched == VersionMatched:
                Version = val
            elif matched == PriorityMatched:
                Priority = val
        else:
            CookieMatched = re.match(r'^(.[^=]*)=(.*)?', item, re.I)
            if CookieMatched:
                CookieName, CookieValue = CookieMatched.groups(0)

    Sessionkey = True if not Expires else False
    Size = (len(CookieName) if CookieName else 0) + (len(CookieValue) if CookieValue else 0)

    Domain = parent_domain if CookieName and not Domain else Domain
    Path = '/' if CookieName and not Path else Path
    Priority = 'Medium' if CookieName and not Priority else Priority.title() if Priority else 'Medium'

    Cookie = {
        CookieName: CookieValue,
        'Name': CookieName,
        'Value': CookieValue,
        'Domain': Domain,
        'Path': Path,
        'Expires': Expires,
        'Comment': Comment,
        'MaxAge': MaxAge,
        'SameSite': SameSite,
        'HttpOnly': HttpOnly,
        'Secure': Secure,
        'Size': Size,
        'Sessionkey': Sessionkey,
        'Version': Version,
        'Priority': Priority
    }
    return Cookie if CookieName else None


async def tls_send(req: httpx.Request, client: httpx.AsyncClient, proxies: str = '') -> httpx.Response | None:
    """
    Just for the TLS.
    :param proxies:
    :param client:
    :param req:
    :return:
    """
    old_url = str(req.url)
    req.headers['poptls-url'] = old_url
    # {choice(TLS_PORTS)}
    req.url = httpx.URL(f'http://localhost:8082')
    if proxies:
        req.headers['poptls-proxy'] = proxies

    # adding redirects, so we can build history on the resp object
    req.headers['poptls-allowredirect'] = 'false'
    res: httpx.Response = await send_req(functools.partial(client.send, req), num_tries=5)
    req.headers.pop('poptls-url')
    req.headers.pop('poptls-proxy', None)
    req.headers.pop('Poptls-Allowredirect', None)
    req.url = old_url

    # set cookies on the client, for some reason carcraftz doesn't play well with this
    if res and res.headers:
        for key, val in res.headers.multi_items():
            if key.lower() != 'set-cookie':
                continue
            cookie = robot_cookie(val, parent_domain=httpx.URL(res.url).host)
            # print(dumps(cookie, indent=4))

            # delete from jar if there
            try:
                client.cookies.delete(
                    name=cookie['Name'],
                    domain=cookie['Domain'],
                    path=cookie['Path']
                )
            except KeyError:
                pass  # is not in jar

            # set in jar
            client.cookies.set(
                name=cookie['Name'],
                value=cookie['Value'],
                domain=cookie['Domain'],
                path=cookie['Path']
            )
    return res


if __name__ == "__main__":
    async def test_2():
        # ja3 with tls send - 334da95730484a993c6063e36bc90a47
        # w/o - b05c33775f03314cf829b168d5b35c20
        async with TLSLauncher():
            async with httpx.AsyncClient() as c:
                req = httpx.Request(
                    method='GET',
                    url="https://tls.peet.ws/api/all",
                    headers={
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "accept-language": "en-CA,en-US;q=0.7,en;q=0.3",
                        "accept-encoding": "gzip, deflate, br",
                        "upgrade-insecure-requests": "1",
                        "sec-fetch-dest": "document",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-site": "none",
                        "sec-fetch-user": "?1",
                        "te": "trailers"
                    }
                )
                res = await tls_send(req, client=c)
                # res = await send_req(functools.partial(
                #     c.send,
                #     req
                # ))
                print_req_info(res, True, True)


    asyncio.run(test_2())
