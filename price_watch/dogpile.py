import threading


def creation_runner(cache, somekey, creator, mutex):
    """Used by dogpile.core:Lock when appropriate"""
    def runner():
        try:
            value = creator()
            cache.set(somekey, value)
        finally:
            mutex.release()
 
    thread = threading.Thread(target=runner)
    thread.start()


def unicode_key_generator(namespace, fn, **kwargs):
    """Custom key generator that handles unicode arguments"""
    fname = fn.__name__

    def generate_key(*args):
        pattern = '{}_{}_{}'
        clean_args = list()
        for arg in args:
            try:
                arg = arg.encode('utf-8')
            except AttributeError:
                pass
            clean_args.append(arg)
        key = pattern.format(namespace, fname,
                             '_'.join(str(a) for a in clean_args))
        return key

    return generate_key