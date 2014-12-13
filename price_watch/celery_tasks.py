from celery import Celery

app = Celery('price_watch', broker='amqp://guest@localhost//')
app.conf.CELERY_TASK_SERIALIZER = 'json'


@app.task
def cache_refresh(cached_callable, arg):
    cached_callable.refresh(arg)