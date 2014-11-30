# from pyramid.events import ContextFound
# from pyramid.events import subscriber
# from price_watch.models import PriceReport
#
#
# @subscriber(ContextFound)
# def context_setter(event):
#     """Set the correct context for different instance collections"""
#     root = event.request.root
#     if event.request.context is root[PriceReport.namespace]:
#         event.request.context = PriceReport.__new__(PriceReport)