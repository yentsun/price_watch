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


def multidict_to_list(multidict):
    """Convert Multidict object to a list of dicts"""
    dict_list = list()
    keys = multidict.dict_of_lists().keys()
    value_count = len(multidict.getall(keys[0]))
    for index in range(0, value_count):
        new_dict = dict()
        for key in keys:
            new_dict[key] = multidict.getall(key)[index]
        dict_list.append(new_dict)
    return dict_list