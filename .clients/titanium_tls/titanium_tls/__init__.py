import sys, json, ctypes, functools, requests, time, os, platform, re, logging, random, base64, math, brotli, datetime
from cloudscraper import User_Agent
from collections import OrderedDict
try:
    from beta_hawk import hawk_cf as hawk_cf_client
except:
    pass
from urllib.parse import urlparse
from requests.structures import CaseInsensitiveDict
from requests_wrapper import RequestsWrapper
from .exceptions import (
    MacError,
    ProxyError,
    DecodeError,
    ConnectionError,
    UnknownException,
    ClientHelloLength,
    RequestInitException,
    RequestReadException,
    RequestSendException,
    TimeoutError
)

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
IOS_USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1'
DEFAULT_CLIENT_HELLO = 'HelloChrome_Auto'
DEFAULT_BROWSER_TYPE = 'Chrome'

SUPPORTED_CLIENT_HELLO_ID = [
    "None",
    "HelloGolang",
    "HelloCustom",
    "HelloRandomized",
    "HelloRandomizedALPN",
    "HelloRandomizedNoALPN",
    "HelloFirefox_Auto", # HelloFirefox_92
    "HelloFirefox_55",
    "HelloFirefox_56",
    "HelloFirefox_63",
    "HelloFirefox_65",
    "HelloFirefox_92",
    "HelloChrome_Auto", # HelloChrome_101
    "HelloChrome_58", 
    "HelloChrome_62",
    "HelloChrome_70",
    "HelloChrome_72",
    "HelloChrome_83",
    "HelloChrome_93",
    "HelloChrome_96",
    "HelloChrome_101",
    "HelloIOS_Auto", # HelloIOS_15_1_1
    "HelloIOS_11_1",
    "HelloIOS_12_1",
    "HelloIOS_14_7_1",
    "HelloIOS_15",
    "HelloIOS_15_1_1"
]

SUPPORTED_CLIENT_SPEC = [
    "aba0c0035182dcd5", # Chrome 93/94
    "8466c4390d4bc355", # Chrome 93/94
    "55e90113ae203739", # iOS 15 HTTP1
    "145040ece68be128", # iOS 15
    "133e933dd1dfea90", # iOS 14
    "833fb25fb38a093b", # iOS 14 / macOS 10
]

# http2_frames configs
HTTP2_CONFIGS = {
    'Chrome': {
        'SettingMaxConcurrentStreams': 1000,
        #'SettingMaxFrameSize': 16384, # not set
        'SettingMaxHeaderListSize': 262144,
        #'SettingEnablePush': 0, # not set
        'InitialWindowSize': 6291456,
        'HeaderTableSize': 65536,
        'WindowUpdate': 15663105
    },
    'Firefox': {
        'SettingMaxConcurrentStreams': 0,
        'SettingMaxFrameSize': 16384,
        'SettingMaxHeaderListSize': 0,
        #'SettingEnablePush': 0, # not set
        'InitialWindowSize': 131072,
        'HeaderTableSize': 65536,
        'WindowUpdate': 12451840
    },
    'IOS': {
        'SettingMaxConcurrentStreams': 100,
        #'SettingMaxFrameSize': 16384, # not set
        'SettingMaxHeaderListSize': 0,
        #'SettingEnablePush': 0, # not set
        'InitialWindowSize': 2097152,
        'HeaderTableSize': 0,
        'WindowUpdate': 10485760
    },
    'Custom': {} # put your HelloCustom values here / now using Default config
}


class TitaniumHawk:

    # ------------------------------------------------------------------------------- #
    # TLS-Cloudflare integrated module with HawkAIO-Cloudflare API
    # ------------------------------------------------------------------------------- #

    def __init__(self, *args, **kwargs) -> None:

        self.api_key:str = kwargs.get('api_key', '')
        self.debug:bool = kwargs.get('debug', False)

    # ------------------------------------------------------------------------------- #
    # Check for Captcha challenge
    # ------------------------------------------------------------------------------- #

    def is_New_Captcha_Challenge(self, response) -> bool:
        try:
            return (
                    response.headers.get('Server', '').startswith('cloudflare')
                    and response.status_code == 403
                    and re.search(
                        r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/?\w?/?\w?/orchestrate/.*/v1',
                        response.text,
                        re.M | re.S
                    )
                    and re.search(r'window._cf_chl_opt', response.text, re.M | re.S)
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Check for IUAM challenge
    # ------------------------------------------------------------------------------- #

    def is_New_IUAM_Challenge(self, response) -> bool:
        try:
            return (
                    response.headers.get('Server', '').startswith('cloudflare')
                    and response.status_code in [429, 503]
                    and re.search(
                        r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/?\w?/?\w?/orchestrate/jsch/v1',
                        response.text,
                        re.M | re.S
                    )
                    and re.search(r'window._cf_chl_opt', response.text, re.M | re.S)
            )
        except AttributeError:
            pass

        return False

    # ------------------------------------------------------------------------------- #
    # Check for block (Captcha or IUAM)
    # ------------------------------------------------------------------------------- #

    def is_Cloudflare_Block(self, response) -> dict:

        is_IUAM = self.is_New_IUAM_Challenge(response)
        is_Captcha = self.is_New_Captcha_Challenge(response)

        return {
            'IUAM': is_IUAM,
            'Captcha': is_Captcha
        }

    # ------------------------------------------------------------------------------- #
    # Solve Cloudflare challenge if block detected
    # ------------------------------------------------------------------------------- #

    def solve_Challenge(self, session:requests.sessions.Session, response):

        check_Cloudflare = self.is_Cloudflare_Block(response)

        start_solve_time = time.time()

        if check_Cloudflare['Captcha'] or check_Cloudflare['IUAM']:
            logging.info('Solving Cloudflare challenge...')

        if check_Cloudflare['Captcha']:
            if self.debug:
                print('Cloudflare Captcha detected.')

            response = hawk_cf_client.CF_2(
                adapter=session,
                original=response,
                key=self.api_key,
                captcha=True,
                debug=self.debug
            ).solve()

        if check_Cloudflare['IUAM']:
            if self.debug:
                print('Cloudflare IUAM detected.')

            response = hawk_cf_client.CF_2(
                adapter=session,
                original=response,
                key=self.api_key,
                captcha=False,
                debug=self.debug
            ).solve()

        response.solve_time = time.time() - start_solve_time

        return response

class Session(requests.sessions.Session):

    # ------------------------------------------------------------------------------- #
    # TLS Session creation
    # ------------------------------------------------------------------------------- #

    def __init__(self, *args, **kwargs):

        self.version = 2

        # Brotli decoding
        self.allow_brotli = kwargs.pop('allow_brotli', False)

        # Session-related
        self.debug = self.tls_debug = kwargs.pop('debug', False) # Requests Debug
        self.proxies:dict = kwargs.pop('proxies', {}) # Session Proxies
        self.headers:dict = kwargs.pop('headers', None) # Session Headers
        self.cookies = []
        self.adapters = OrderedDict()

        self.auth = kwargs.pop('auth', None)
        self.cert = None # You can not set this
        self.max_redirects = 10 # Default Golang - You can not set this
        self.params = kwargs.pop('params', {})
        self.stream = False #Â No available functions to do this
        self.trust_env = kwargs.pop('trust_env', True) # WIP
        self.verify = kwargs.pop('verify', True) # WIP
        self.hooks = kwargs.pop('hooks', {'response': []}) # You can use requestPostHook/requestPreHook for this - This is just to follow Requests structure

        self.user_agent = User_Agent(
            allow_brotli=self.allow_brotli,
            browser=kwargs.pop('browser', None)
        )

        if not self.headers:
            self.headers = self.user_agent.headers
        else:
            self.user_agent = None

        # TLS-related
        self.client_hello:str = kwargs.pop('client_hello', DEFAULT_CLIENT_HELLO).strip().lower() # Session Client Hello
        self.client_spec:str = kwargs.pop('client_spec', '').strip().lower() # Session Client Spec - you can apply this instead of using JA3
        self.browser_type:str = kwargs.pop('browser_type', DEFAULT_BROWSER_TYPE).strip() # Browser type for configurations
        self.ja3:str = kwargs.pop('ja3', '').strip() # Session JA3

        # Cloudflare/CloudScraper-related
        self.interpreter = 'default'
        self.delay = kwargs.pop('delay', None) # Cloudflare solving delay
        self.ssl_context = None # You can not set this
        self.cipherSuite = None # You can not set this

        hawk_api_key = kwargs.pop('hawk_api_key', '')

        self.requestPreHook = kwargs.pop('requestPreHook', None)
        self.requestPostHook = kwargs.pop('requestPostHook', None)
        self.solve_on_post = kwargs.pop('solve_on_post', False)
        self.cloudflare_provider = kwargs.pop('provider', 'hawk').lower()
        self.solve_cloudflare = kwargs.pop('cloudflare', False) # Option to solve Cloudflare
        self.cloudflare_instance = None # Cloudflare solving instance

        captcha_args = kwargs.pop('captcha', {})

        self.captcha = {
            'User-Agent': self.headers['User-Agent'],
            'provider': captcha_args.get('provider', '2captcha'),
            'api_key': captcha_args.get('api_key', '')
        }

        if self.solve_cloudflare:
            self.cloudflare_instance = TitaniumHawk(api_key=hawk_api_key, debug=self.debug) # Create Cloudflare instance with HawkAIO API key

            if not self.requestPostHook:
                self.requestPostHook = self.cloudflare_instance.solve_Challenge

        # Else
        self.get = functools.partial(self.perform_request, 'GET')
        self.put = functools.partial(self.perform_request, 'PUT')
        self.post = functools.partial(self.perform_request, 'POST')
        self.head = functools.partial(self.perform_request, 'HEAD')
        self.patch = functools.partial(self.perform_request, 'PATCH')
        self.delete = functools.partial(self.perform_request, 'DELETE')
        self.options = functools.partial(self.perform_request, 'OPTIONS')

        self.requests_wrapper = RequestsWrapper.get_instance()

    # ------------------------------------------------------------------------------- #
    # Raise exception whenever occurs
    # ------------------------------------------------------------------------------- #

    def raise_exception(self, exception, msg):
        sys.tracebacklimit = 0
        raise exception(msg)

    # ------------------------------------------------------------------------------- #
    # Picks cookies from response Cookie Jar and set them into session
    # ------------------------------------------------------------------------------- #

    def set_cookies_from_client_cookiejar_to_session_cookiejar(self, response_cookiejar) -> list:

        cookieob_cookies = []

        if response_cookiejar == None:
            return cookieob_cookies

        for cookie in response_cookiejar:
            cookieob_cookies.append(
                {
                    "name": cookie["Name"],
                    "value": cookie["Value"],
                    "domain": cookie["Domain"],
                    "path": cookie["Path"]
                }
            )

        self.cookies = cookieob_cookies

        return cookieob_cookies

    def set_cookie(self, name, value, domain, path):

        for cookie in self.cookies:
            if cookie["name"] == name and cookie["domain"] == domain:
                self.delete_cookie(name, domain)

        self.cookies.append(
            {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path
            }
        )

    def delete_cookie(self, name, domain):

        for cookie in self.cookies:
            if cookie["name"] == name and cookie["domain"] == domain:
                self.cookies.remove(cookie)

    def get_cookie(self, name, domain):

        for cookie in self.cookies:
            if cookie["name"] == name and cookie["domain"] == domain:
                return cookie

        return 0

    def clear_cookies(self):

        self.cookies = []

    # ------------------------------------------------------------------------------- #
    # Converts client response headers to readable headers
    # ------------------------------------------------------------------------------- #

    def get_response_data(self, response) -> list:

        headers = {}

        for value in response['Headers']:
            headers[value] = response['Headers'][value][0]

        cookiejar_cookies = self.set_cookies_from_client_cookiejar_to_session_cookiejar(response['JarCookies'])

        if self.tls_debug and headers.get('Location'):
            print(f'Redirects are disabled. Redirect detected. ({headers.get("Location")})')

        return [
            CaseInsensitiveDict(headers),
            cookiejar_cookies
        ]

    # ------------------------------------------------------------------------------- #
    # Parses proxy and set it to Request options
    # ------------------------------------------------------------------------------- #

    def get_request_proxy(self, proxy, *args, **kwargs):

        if proxy != {} and type(proxy) == dict:
            proxy_http:str = proxy['http'] if kwargs.get('selectHTTPSProxy', False) == False else proxy['https'] # IDK this might be useful

            if proxy_http.startswith('http://') == False:
                proxy = f'http://{proxy_http}'
            else:
                proxy = proxy_http

            if '@' in proxy:
                split_proxy = proxy.split('http://')[1]
                username = split_proxy.split('@')[0].split(':')[0]
                password = split_proxy.split('@')[0].split(':')[1]
                ip = split_proxy.split('@')[1].split(':')[0]
                port = split_proxy.split('@')[1].split(':')[1]
                proxy = f'http://{username}:{password}@{ip}:{port}'

        return proxy

    # ------------------------------------------------------------------------------- #
    # Randomize headers on request - Also adds headers to randomize more
    # ------------------------------------------------------------------------------- #

    def randomize_header_order(self, request_headers:dict, headers_to_randomize:list):

        def get_random_pos(index, busy_pos):

            while True:
                randomized_pos = random.randint(0, index)

                if randomized_pos in busy_pos:
                    continue
                else:
                    break

            return randomized_pos

        if len(headers_to_randomize) == 0:
            return request_headers

        default_headers = {
            'Date': datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            'DNT': '1',
            'Device-Memory': random.choice(['0.25', '0.5', '1', '2', '4', '8']),
            'Early-Data': '1',
            'ECT': '4g',
            'Width': '1920',
            'Viewport-Width': '320',
            'Age': str(random.randint(5, 200)),
            'Allow': ", ".join(random.sample(['GET', 'POST', 'HEAD', 'OPTIONS', 'PATCH', 'DELETE', 'PUT'], 2))
        }

        header_index = 0
        headers_pos = {}
        no_randomize_pos = []
        randomize_pos = []

        busy_pos = []
        new_headers_pos = {}
        new_request_headers = {}

        for header in request_headers:
            if header.lower() == 'cookie':
                continue
            headers_pos[header_index] = {"name": header, "value": request_headers[header]}
            header_index += 1

        for default_header in default_headers:
            headers_to_randomize.append(default_header)
            headers_pos[header_index] = {"name": default_header, "value": default_headers[default_header]}
            header_index += 1

        if 'Cookie' in CaseInsensitiveDict(request_headers):
            headers_pos[header_index] = {"name": "Cookie", "value": CaseInsensitiveDict(request_headers).get('Cookie')}
            header_index += 1

        if self.tls_debug:
            print(f'{len(headers_to_randomize)} headers to be randomized. Possible combinations: {math.factorial(len(headers_to_randomize))}')

        for pos in headers_pos:
            if headers_pos[pos]["name"] not in headers_to_randomize:
                no_randomize_pos.append(pos)
            else:
                randomize_pos.append(pos)

        for nrp in no_randomize_pos:
            new_headers_pos[nrp] = headers_pos[nrp]
            busy_pos.append(nrp)

        for rp in randomize_pos:
            new_pos = get_random_pos(header_index, busy_pos)
            new_headers_pos[new_pos] = headers_pos[rp]
            busy_pos.append(new_pos)

        for n in range(0, header_index):
            for np in busy_pos:
                if np == n:
                    new_request_headers[new_headers_pos[np]["name"]] = new_headers_pos[np]["value"]

        return new_request_headers

    # ------------------------------------------------------------------------------- #
    # Start TLS Request
    # ------------------------------------------------------------------------------- #

    def perform_tls_request(self, options):

        options_data = json.dumps(options)
        args = ctypes.c_char_p(str(options_data).encode('utf-8'))

        if self.tls_debug:
            print('Performing request.')
            print(options)

        raw_response = tls.Request(args)

        response = json.loads(raw_response)

        return response

    # ------------------------------------------------------------------------------- #
    # Returns encoding from given HTTP Header Dict
    # ------------------------------------------------------------------------------- #

    def _parse_content_type_header(self, header):

        tokens = header.split(';')
        content_type, params = tokens[0].strip(), tokens[1:]
        params_dict = {}
        items_to_strip = "\"' "

        for param in params:
            param = param.strip()

            if param:
                key, value = param, True
                index_of_equals = param.find("=")

                if index_of_equals != -1:
                    key = param[:index_of_equals].strip(items_to_strip)
                    value = param[index_of_equals + 1:].strip(items_to_strip)

                params_dict[key.lower()] = value

        return content_type, params_dict

    def get_encoding_from_headers(self, headers):

        content_type = headers.get('content-type')

        if not content_type:
            return None

        content_type, params = self._parse_content_type_header(content_type)

        if 'charset' in params:
            return params['charset'].strip("'\"")

        if 'text' in content_type:
            return 'ISO-8859-1'

        if 'application/json' in content_type:
            # Assume UTF-8 based on RFC 4627: https://www.ietf.org/rfc/rfc4627.txt since the charset was unset
            return 'utf-8'

    # ------------------------------------------------------------------------------- #
    # Decode Brotli on older versions of urllib3 manually
    # ------------------------------------------------------------------------------- #

    def decodeBrotli(self, resp):
        if requests.packages.urllib3.__version__ < '1.25.1' and resp.headers.get('Content-Encoding') == 'br':
            if self.allow_brotli and resp._content:
                resp._content = brotli.decompress(resp.content)
            else:
                logging.warning(
                    f'You\'re running urllib3 {requests.packages.urllib3.__version__}, Brotli content detected, '
                    'Which requires manual decompression, '
                    'But option allow_brotli is set to False, '
                    'We will not continue to decompress.'
                )

        return resp

    # ------------------------------------------------------------------------------- #
    # Create Response Object
    # ------------------------------------------------------------------------------- #

    def create_response(self, options):

        r = self.perform_tls_request(options)

        client_response = requests.models.Response()
        client_response.options = options
        client_response.error = str(r['Error'])
        client_response.error_msg = str(r['ErrorMsg'])
        client_response.success = bool(r['Success'])

        if not client_response.success:
            if client_response.error == "Error initiating request.":
                exception = RequestInitException
            elif client_response.error == "Error occurred sending the request.":
                if "error with proxy" in str(client_response.error_msg).lower():
                    exception = ProxyError
                elif "error decoding message" in str(client_response.error_msg).lower():
                    exception = DecodeError
                elif "dial tcp" in str(client_response.error_msg).lower():
                    exception = ConnectionError
                elif 'proxy' in str(client_response.error_msg).lower():
                    exception = ProxyError
                elif 'bad record mac' in str(client_response.error_msg).lower():
                    exception = MacError
                elif 'unexpected clienthello length' in str(client_response.error_msg).lower():
                    exception = ClientHelloLength
                elif 'timeout' in str(client_response.error_msg).lower():
                    exception = TimeoutError
                else:
                    exception = RequestSendException
            elif client_response.error == "Error reading body. Check headers.":
                exception = RequestReadException
            else:
                exception = UnknownException

            if self.tls_debug:
                print(f'An exception occurred: [{exception.__name__} => {r}]')

            self.raise_exception(
                exception,
                client_response.error_msg if client_response.error_msg != '' else client_response.error
            )

        response_data = self.get_response_data(r)

        client_response.url = str(r['URL'])
        client_response._content = str(r['Body']).encode()
        client_response.status_code = int(r['StatusCode'])
        client_response.connection = None
        client_response.raw_headers = r['Headers']

        try:
            client_response.go_request = json.loads(base64.b64decode(r['Request']))
        except Exception as e:
            client_response.go_request = e

        client_response.headers = response_data[0]
        client_response.cookies = response_data[1]
        client_response.encoding = self.get_encoding_from_headers(client_response.headers)

        if self.tls_debug:
            print({
                'url': client_response.url,
                'status_code': client_response.status_code,
                'raw_headers': client_response.raw_headers,
                'cookies': client_response.cookies
            })

        return client_response

    # ------------------------------------------------------------------------------- #
    # Initialize request
    # ------------------------------------------------------------------------------- #

    def perform_request(self, method:str, url:str, *args, **kwargs):
        return self.decodeBrotli(
            self.prepare_request(method, url, *args, **kwargs)
        )

    def prepare_request(self, method:str, url:str, *args, **kwargs):

        if self.tls_debug:
            print(f'Initializing {method} request.')

        # ------------------------------------------------------------------------------- #
        # Pre-Hook the request via user defined function
        # ------------------------------------------------------------------------------- #

        if self.requestPreHook:
            (method, url, args, kwargs) = self.requestPreHook(
                self,
                method,
                url,
                *args,
                **kwargs
            )

        # ------------------------------------------------------------------------------- #
        # Request data
        # ------------------------------------------------------------------------------- #

        body = kwargs.get('json', None)
        form = kwargs.get('data', None)
        params = kwargs.get('params', None)
        timeout:int = kwargs.get('timeout', 25)
        allow_redirects:bool = kwargs.get('allow_redirects', True)
        show_redirects:bool = kwargs.get('show_redirects', False)
        discardResponse:bool = kwargs.get('discardResponse', False)
        selectHTTPSProxy:bool = kwargs.get('selectHTTPSProxy', False)

        # ------------------------------------------------------------------------------- #
        # Set basic headers and proxy - Convert OrderedDict/CaseInsensitiveDict to normal dict
        # ------------------------------------------------------------------------------- #

        headers:dict = kwargs.get(
            'headers', self.headers
        )

        if type(headers) != dict: # This might break your code if you are not setting headers properly
            headers = dict(headers)

        proxy = self.get_request_proxy(
            kwargs.get('proxies', self.proxies),
            selectHTTPSProxy=selectHTTPSProxy
        )

        # ------------------------------------------------------------------------------- #
        # Create Request OPTIONS Object
        # ------------------------------------------------------------------------------- #

        headers_dict = {}

        if type(headers) == OrderedDict:
            # Structure must be OrderedDict([("key1", "value1"), ("key2", "value2")])
            for key in headers:
                headers_dict[key] = headers[key]
        else:
            headers_dict = headers

        header_order = [] # Needed for Golang to order headers

        for h in headers_dict:
            header_order.append(str(h).lower())

        options = {
            "Method": method,
            "URL": url,
            "Headers": headers_dict,
            "HeaderOrder": header_order,
            "AllowRedirects": allow_redirects,
            "ShowRedirects": True if self.tls_debug is True else show_redirects,
            "SessionCookies": self.cookies,
            "ClientHello": self.client_hello,
            "ClientSpec": self.client_spec,
            "Proxy": "",
            "Timeout": timeout,
            "JA3": kwargs.get('ja3', self.ja3),
            "HTTP2Frame": HTTP2_CONFIGS[self.browser_type]
        }

        # ------------------------------------------------------------------------------- #
        # Set proxies - self-explanatory
        # ------------------------------------------------------------------------------- #

        if proxy != {}:
            options.update({'Proxy': proxy})

        # ------------------------------------------------------------------------------- #
        # Form data - Check for OCTET (will be encoded in base64 then decoded in Client)
        # ------------------------------------------------------------------------------- #

        if form is not None:
            if type(form) == bytes:
                if CaseInsensitiveDict(options['Headers'])['Content-Type'] == 'application/octet-stream':
                    form = base64.b64encode(form).decode('utf-8')
                    options.update({'BytesForm': form})
                else:
                    form = form.decode('utf-8')
                    options.update({'Form': form})
            else:
                options.update({'Form': form})

        # ------------------------------------------------------------------------------- #
        # JSON body - Check for OCTET (will be encoded in base64 then decoded in Client)
        # ------------------------------------------------------------------------------- #

        if body is not None:
            if type(body) == dict:
                body = json.dumps(separators=(',', ':'), obj=body)
            if type(body) == bytes:
                if CaseInsensitiveDict(options['Headers'])['Content-Type'] == 'application/octet-stream':
                    body = base64.b64encode(body).decode('utf-8')
                    options.update({'BytesForm': body})
                else:
                    body = body.decode('utf-8')
                    options.update({'Body': body})
            else:
                options.update({'Body': body})

        # ------------------------------------------------------------------------------- #
        # Query params
        # ------------------------------------------------------------------------------- #

        params_dict = {}

        if params is not None:
            if type(params) == str:
                params_list = params.split('?')[1].split('&') if '?' in params else params.split('&')
                for param in params_list:
                    params_dict[param.split('=')[0].strip()] = param.split('=')[1].strip()
                url = url + f'?{params}' if '?' not in params else url + params
                options.update({'URL': url})
            else:
                params_dict = params
                parsed_url = urlparse(url)
                initial_query_string = str(parsed_url.query)
                query_string = str(parsed_url.query)

                for q in params:
                    query_string += f'&{q}={params[q]}'

                if str(initial_query_string).strip().rstrip() == '':
                    url = url + '?' + query_string[1:]
                else:
                    url = url.split(initial_query_string)[0] + query_string

                options.update({'URL': url})

        # ------------------------------------------------------------------------------- #
        # discardResponse doesn't show body response but just headers/statuscode/cookies/...
        # ------------------------------------------------------------------------------- #

        if discardResponse == True:
            if options['Method'] != 'HEAD':
                options.update({'Method': 'HEAD'})

            if CaseInsensitiveDict(options['Headers']).get('method', None) is not None:
                options['Headers']['method'] = 'HEAD'

        # ------------------------------------------------------------------------------- #
        # Check headers order
        # ------------------------------------------------------------------------------- #

        if options['Method'] == 'GET':
            master_header_order = [
                "method",
                "authority",
                "scheme",
                "path",
		        "host",
		        "connection",
		        "device-memory",
		        "viewport-width",
		        "rtt",
		        "downlink",
		        "ect",
		        "sec-ch-ua",
                "x-kpsdk-cd",
                "x-kpsdk-ct",
		        "sec-ch-ua-mobile",
		        "sec-ch-ua-full-version",
		        "sec-ch-ua-arch",
		        "sec-ch-ua-platform",
		        "sec-ch-ua-platform-version",
		        "sec-ch-ua-model",
		        "upgrade-insecure-requests",
		        "user-agent",
		        "accept",
                "x-anticsrftoken",
                "x-requested-with",
		        "sec-fetch-site",
		        "sec-fetch-mode",
		        "sec-fetch-user",
		        "sec-fetch-dest",
		        "referer",
		        "accept-encoding",
		        "accept-language",
		        "cookie"
            ]
        else:
            master_header_order = [
                "method",
                "authority",
                "scheme",
                "path",
		        "host",
		        "connection",
                "content-length",
                "cache-control",
                "surrogate-control",
		        "sec-ch-ua",
                "x-kpsdk-cd",
                "x-kpsdk-ct",
                "content-type",
                "x-anticsrftoken",
                "x-requested-with",
		        "sec-ch-ua-mobile",
                "user-agent",
                "cf-challenge",
                "sec-ch-ua-platform",
                "accept",
                "origin",
		        "sec-ch-ua-full-version",
		        "sec-ch-ua-arch",
		        "sec-ch-ua-platform",
		        "sec-ch-ua-platform-version",
		        "sec-ch-ua-model",
		        "sec-fetch-site",
		        "sec-fetch-mode",
		        "sec-fetch-user",
		        "sec-fetch-dest",
		        "referer",
		        "accept-encoding",
		        "accept-language",
		        "cookie"
            ]

        headers_changed = False

        if kwargs.get('order_headers', False) == True:
            if 'User-Agent' not in CaseInsensitiveDict(options['Headers']):
                options['Headers']['User-Agent'] = self.headers['User-Agent']

                if 'user-agent' not in header_order:
                    header_order.append('user-agent')
                    headers_changed = True

            if 'Cookie' not in CaseInsensitiveDict(options['Headers']):
                options['Headers']['cookie'] = ""

                if 'cookie' not in header_order:
                    header_order.append('cookie')
                    headers_changed = True

            try:
                if headers_changed: # Order headers just in case they are not following correct order
                    header_order = sorted(header_order, key=lambda x: master_header_order.index(x))
            except Exception as e:
                if self.tls_debug:
                    print(f'Cannot re-order headers: {e}')
                pass

        # ------------------------------------------------------------------------------- #
        # Get and return response from Client
        # ------------------------------------------------------------------------------- #

        #options['Headers'] = OrderedDict(options['Headers'])

        start_time = time.time()

        attempts = 0
        response = None
        while attempts < 10:
            try:
                response = self.create_response(options)

                if response.status_code > 500:
                    self.requests_wrapper.rotate_proxy(self)
                    continue
                break
            except Exception as e:
                self.requests_wrapper.rotate_proxy(self)
                pass
            finally:
                attempts += 1

        if response is None:
            return

        response.elapsed = self.elapsed = datetime.timedelta(seconds=time.time() - start_time)

        if self.tls_debug:
            print(f'Request is successful: <[{response.ok}]> <Response [{response.status_code}]>.\n')

        # ------------------------------------------------------------------------------- #
        # Create response.request Object - needed for Requests
        # ------------------------------------------------------------------------------- #

        response.request = requests.models.Request(
            method=options['Method'],
            url=options['URL'].split('?')[0] if '?' in options['URL'] else options['URL'],
            headers=CaseInsensitiveDict(options['Headers']),
            #cookies=request_cookies,
            json=options.get('Body') if options.get('Body') != None and type(options.get('Body')) == dict else json.loads(options.get('Body')) if options.get('Body') != None and type(options.get('Body')) == str else options.get('Body').decode('utf-8') if options.get('Body') != None and type(options.get('Body')) == bytes else None,
            data=options.get('Form') if options.get('Form') != None and type(options.get('Form')) == dict else None,
            params=params_dict if params_dict != {} else None
        )

        response.request = response.request.prepare()

        # ------------------------------------------------------------------------------- #
        # Check for challenge (You can only do Cloudflare with Hawk at the moment - You can solve Kasada with Helheim though)
        # ------------------------------------------------------------------------------- #

        if self.requestPostHook:
            response = self.requestPostHook(self, response)

        # ------------------------------------------------------------------------------- #
        # Return response (self-explanatory)
        # ------------------------------------------------------------------------------- #

        return response

# ------------------------------------------------------------------------------- #

if getattr(sys, 'frozen', False):
    file_dir = f'{sys._MEIPASS}/tls/titanium_tls'
else:
    file_dir = os.path.dirname(os.path.abspath(__file__))

tls = ctypes.cdll.LoadLibrary(f'{file_dir}/titanium_tls.{platform.system().lower()}' if str(platform.system()) != 'Windows' else f'{file_dir}/titanium_tls.dll')
tls.Request.restype = ctypes.c_char_p
tls.Request.argtypes = [ctypes.c_char_p]

# ------------------------------------------------------------------------------- #

session = Session
get = session().get
put = session().put
post = session().post
delete = session().delete
patch = session().patch
head = session().head
options = session().options