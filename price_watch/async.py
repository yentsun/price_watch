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