import threading

from itertools import tee, islice, chain, izip


def previous_and_next(some_iterable):
    """
    Previous and next values inside a loop
    credit: http://stackoverflow.com/a/1012089/216042
    """
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return izip(prevs, items, nexts)


def async_creation_runner(cache, somekey, creator, mutex):
    """
    Used by dogpile.core:Lock when appropriate
    Taken from http://dogpilecache.readthedocs.org/en/latest/api.html
    #module-dogpile.cache.region
    """
    print('starting thread...')

    def runner():
        try:
            value = creator()
            cache.set(somekey, value)
        finally:
            mutex.release()

    thread = threading.Thread(target=runner)
    thread.start()