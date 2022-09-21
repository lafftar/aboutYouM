from requests.compat import cookielib, MutableMapping

class CJar(cookielib.CookieJar, MutableMapping):

    def __setitem__(self, key, value):

        self.set(name=key, value=value)

    def __getitem__(self, key):

        return self.find_no_duplicates(key)

    def __delitem__(self, key):

        try:
            self.remove_cookie_by_name(key)
        except:
            pass

    def get(self, name, default=None, domain=None, path=None):

        try:
            return self.find_no_duplicates(name, domain, path)
        except KeyError:
            return default

    def set(self, name, value, **kwargs):

        c_object = self.create_cookie(name, value, **kwargs)

        if c_object.name in self.get_dict():
            for cookie in iter(self):
                if c_object.name == cookie.name:
                    cookie.value = c_object.value
                    cookie.domain = c_object.domain
                    cookie.path = c_object.path
        else:
            self.set_cookie(c_object)

        return c_object

    def create_cookie(self, name, value, **kwargs):

        result = {
            'version': 0,
            'name': name,
            'value': value,
            'port': None,
            'domain': '',
            'path': '/',
            'secure': False,
            'expires': None,
            'discard': True,
            'comment': None,
            'comment_url': None,
            'rest': {'HttpOnly': None},
            'rfc2109': False,
        }

        badargs = set(kwargs) - set(result)

        if badargs:
            err = 'create_cookie() got unexpected keyword arguments: %s'
            raise TypeError(err % list(badargs))

        result.update(kwargs)
        result['port_specified'] = bool(result['port'])
        result['domain_specified'] = bool(result['domain'])
        result['domain_initial_dot'] = result['domain'].startswith('.')
        result['path_specified'] = bool(result['path'])

        return cookielib.Cookie(**result)

    def set_cookie(self, cookie, *args, **kwargs):
        if hasattr(cookie.value, 'startswith') and cookie.value.startswith('"') and cookie.value.endswith('"'):
            cookie.value = cookie.value.replace('\\"', '')

        return super(CJar, self).set_cookie(cookie, *args, **kwargs)

    def remove_cookie_by_name(self, name):

        for cookie in iter(self):
            if cookie.name == name:
                self.clear(cookie.domain, cookie.path, cookie.name)

    def get_dict(self):

        t_cookiedict = {}

        for cookie in iter(self):
            t_cookiedict[cookie.name] = cookie.value

        return t_cookiedict

    def list_domains(self):

        t_cookiedomains = []

        for cookie in iter(self):
            if cookie.domain in t_cookiedomains:
                continue

            t_cookiedomains.append(cookie.domain)

        return t_cookiedomains

    def find_no_duplicates(self, name, domain=None, path=None):

        toReturn = None

        for cookie in iter(self):
            if cookie.name == name:
                if domain is None or cookie.domain == domain:
                    if path is None or cookie.path == path:
                        if toReturn is not None:
                            raise RuntimeError('There are multiple cookies with name, %r' % (name))

                        toReturn = cookie.value

        if toReturn:
            return toReturn

        raise KeyError('name=%r, domain=%r, path=%r' % (name, domain, path))
