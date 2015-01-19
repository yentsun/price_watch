import threading

from price_watch.exceptions import MultidictError


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
    """
    Convert Multidict object to a list of dicts. Dict tuples must have equal
    number of key/value pairs.
    """
    dict_list = list()
    keys = multidict.dict_of_lists().keys()
    value_count = 0
    for key in keys:
        this_value_count = len(multidict.getall(key))
        if value_count is 0:
            value_count = this_value_count
        else:
            if this_value_count != value_count:
                raise MultidictError()
    for index in range(0, value_count):
        new_dict = dict()
        for key in keys:
            new_dict[key] = multidict.getall(key)[index]
        dict_list.append(new_dict)
    return dict_list