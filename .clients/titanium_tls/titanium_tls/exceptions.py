class RequestInitException(Exception):
    """
    Request initializing exception
    """

class RequestSendException(Exception):
    """
    Request sending exception
    """

class RequestReadException(Exception):
    """
    Body reading exception
    """

class UnknownException(Exception):
    """
    Basic exception
    """

class ReadTimeout(Exception):
    """
    Request read timeout
    """

class ProxyError(Exception):
    """
    Proxy exception
    """

class DecodeError(Exception):
    """
    Message decode exception
    """

class ConnectionError(Exception):
    """
    Connection error to host
    """

class MacError(Exception):
    """
    local error: tls: bad record MAC
    """

class ClientHelloLength(Exception):
    """
    unexpected ClientHello length
    """

class TimeoutError(Exception):
    """
    Request exceeded client timeout
    """