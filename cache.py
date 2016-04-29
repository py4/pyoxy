import datetime
import logging
import threading

logging.basicConfig(filename='pyoxy.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger('pyoxy')
lock = threading.Lock()


def synchronized(lock):
    """ Synchronization decorator """

    def wrap(f):
        def newFunction(*args, **kw):
            #with lock:
            return f(*args, **kw)

        return newFunction

    return wrap


# @todo: supporting max age for cache

class Cache:
    def __init__(self, cache_size):
        self.max_cache_size = cache_size
        self.capacity = cache_size
        self.size = 0
        self.storage = {}

    def has_capacity(self, x):
        return x <= self.capacity

    def has_key(self, key):
        if key in self.storage.keys():
            if self.expired(key):
                self.remove(key)
                return False
            return True
        return False

    @synchronized(lock)
    def remove(self, key):
        self.release(len(self.storage[key]['data']))
        self.storage.pop(key)

    @synchronized(lock)
    def store(self, url, response):
        n = len(response)
        if not self.possible(n):
            logger.debug("Impossible to store response with size %d in cache" % (n))
            return
        if not self.has_capacity(n):
            logger.debug("not enough for %d bytes with capacity %d" % (n, self.capacity))
            self.free_space(n)
            logger.debug("After free space. currency capacity: %d" % self.capacity)

        self.storage[url] = {
            'data': response,
            'updated_at': datetime.datetime.now(),
            'max_age': -1,
            'access_at': datetime.datetime.now()
        }
        self.capacity -= n
        self.size += n
        logger.debug("Stored %d bytes for %s - currency capacity: %d" % (n, url, self.capacity))

    @synchronized(lock)
    def update(self, url, response):
        self.remove(url)
        self.update(url, response)

    @synchronized(lock)
    def read(self, url):
        self.storage[url]['access_at'] = datetime.datetime.now()
        return self.storage[url]['data']

    @synchronized(lock)
    def consume(self, n):
        self.capacity -= n
        self.size += n

    @synchronized(lock)
    def release(self, n):
        self.capacity += n
        self.size -= n

    def possible(self, n):
        return n <= self.max_cache_size

    def expired(self, key):
        v = self.storage[key]
        if v['max_age'] == -1:
            return False
        expires_at = self.storage[key]['updated_at'] + datetime.timedelta(seconds=v['max_age'])
        return expires_at < datetime.datetime.now()

    def free_space(self, required_size):
        if self.has_capacity(required_size):
            return

        for k in self.storage.keys():
            if self.expired(k):
                logger.debug("[expire] Removed %s and released %d bytes" % (k, len(self.storage[k]['data'])))
                self.remove(k)

        if self.has_capacity(required_size):
            return

        while not self.has_capacity(required_size) or self.size != 0:
            self.free_LRU()

    def free_LRU(self):
        least = None
        least_access_time = datetime.datetime.now()
        for k in self.storage.keys():
            if self.storage[k]['access_at'] < least_access_time:
                least = k
                least_access_time = self.storage[k]['access_at']
        if least:
            logger.debug(
                "[LRU policy] Removed %s and released %d bytes" % (least, len(self.storage[least]['data'])))
            self.remove(least)
