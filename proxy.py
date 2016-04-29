import logging
import socket
from thread import start_new_thread

from cache import Cache
from utils import *

# @todo: setting HTTP 1.1 to HTTP 1.0

logging.basicConfig(filename='pyoxy.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger('pyoxy')


class PyoxyServer:
    def __init__(self):
        self.default_port = 31374
        self.max_connections = 10
        self.buffer_size = 8192
        self.cache = Cache(1000000)

    def start(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self.default_port))
            s.listen(self.max_connections)
        except Exception, e:
            print "couldn't start Pyoxy server"
            print e
            return

        while True:
            connection, address = s.accept()
            data = connection.recv(self.buffer_size)
            start_new_thread(self.handle_request, (connection, data, address))

    def handle_request(self, connection, data, address):
        info = parse_header(data)
        if info['method'] != 'GET':
            send_not_implemented(connection)
            return

        host = info['Host']
        url = info['full_url']
        logger.info("Request for %s from %s" % (url, address))

        if self.cache.has_key(url):
            if 'In-Modified-Since' in info.keys():
                logger.debug("[If-Modified-Since] should check with server!")
                result = call_server(host, data, self.buffer_size)
                logger.debug("[If-Modified-Since] server response:  ")
                logger.debug(result)
                response = self.cache.read(url)  # @todo: should be changeds
            else:
                logger.info("Cache hit for " + url)
                response = self.cache.read(url)
        else:
            logger.info("Cache miss for " + url)
            response = call_server(host, data, self.buffer_size)
            self.cache.store(url, response)

        connection.send(response)
        connection.close()
