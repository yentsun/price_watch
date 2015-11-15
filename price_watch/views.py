# -*- coding: utf-8 -*-

import datetime
import json

from babel.core import Locale
from babel.numbers import format_currency
from babel.dates import format_datetime
from mako.exceptions import TopLevelLookupException
from pyramid.view import view_config, view_defaults, notfound_view_config
from pyramid.renderers import render_to_response, render
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid_dogpile_cache import get_region

from price_watch.models import (Page, PriceReport, PackageLookupError,
                                CategoryLookupError, ProductCategory, Product,
                                ProductPackage, Merchant)
from price_watch.utilities import multidict_to_list
from price_watch.exceptions import MultidictError

MULTIPLIER = 1
general_region = get_region('general')


def namespace_predicate(class_):
    """
    Custom predicate to check context for being a namespace
    """
    def check_namespace(context, request):
        try:
            return context == request.root[class_.namespace]
        except KeyError:
            return False
    return check_namespace


def get_datetimes(days):
    """Return list with days back range"""

    result = list()
    for count in reversed(range(0, int(days))):
        date = datetime.date.today() + datetime.timedelta(-1*MULTIPLIER*count)
        date_time = datetime.datetime.combine(date,
                                              datetime.datetime.now().time())
        result.append(date_time)
    return result


class EntityView(object):
    """View class for Milk Price Report entities"""

    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.root = request.root
        self.locale = Locale(request.locale_name)
        self.display_days = int(request.registry.settings['display_days'])
        self.delta_period = (datetime.datetime.now() -
                             datetime.timedelta(days=self.display_days))
        self.fd = format_datetime

    def __str__(self):
        return self.__class__.__name__

    def menu(self):
        """Generate simple menu"""
        items = [
            (u'главная', '/'),
            (u'о проекте', '/pages/about')
        ]
        menu = list()
        for item in items:
            title, path = item
            menu.append((title, path, self.request.path == path))
        return menu

    def currency(self, value, symbol=''):
        """Format currency value with Babel"""
        return format_currency(value, symbol, locale=self.locale)


@view_defaults(custom_predicates=(namespace_predicate(Merchant),))
class MerchantsView(EntityView):
    """Merchant collection views"""

    @view_config(request_method='GET', renderer='json')
    def get(self):
        return list(self.context)


@view_defaults(context=Merchant)
class MerchantView(EntityView):
    """Merchant instance view"""

    @view_config(request_method='GET', renderer='json')
    def get(self):
        return {'key': self.context.key,
                'title': self.context.title,
                'location': self.context.location}

    @view_config(request_method='PATCH', renderer='json')
    def patch(self):
        data = self.request.params
        try:
            self.context.patch(data, self.root)
            return {'key': self.context.key,
                    'title': self.context.title,
                    'location': self.context.location}
        except TypeError as e:
            return HTTPBadRequest(e.message)


@view_defaults(context=Page)
class PageView(EntityView):
    """Page instance views"""

    @view_config(request_method='GET')
    def get(self):
        try:
            return render_to_response(
                'pages/{slug}.mako'.format(**self.context.__dict__),
                {'view': self},
                request=self.request
            )
        except TopLevelLookupException:  # Mako can't find the template
            raise HTTPNotFound


@view_defaults(custom_predicates=(namespace_predicate(Page),))
class PagesView(EntityView):
    """Pages collection views"""

    @view_config(request_method='POST', renderer='json')
    def post(self):
        post_data = self.request.POST
        try:
            new_page, stats = Page.assemble(storage_manager=self.root,
                                            **post_data)
            return {
                'new_page': new_page.slug
            }
        except TypeError as e:
            raise HTTPBadRequest(e.message)


@view_defaults(context=Product)
class ProductView(EntityView):

    @general_region.cache_on_arguments('product')
    def serve_data(self, product):
        """Return prepared product data"""
        current_price = product.get_price()
        if current_price:
            current_price = self.currency(current_price)
            product_delta = int(product.get_price_delta(
                self.delta_period)*100)
            last_report_url = None
        else:
            product_delta = 0
            last_price = product.get_last_reported_price()
            current_price = self.currency(last_price) if last_price else None
            last_report = self.context.get_last_report()
            last_report_url = \
                self.request.resource_url(last_report) if last_report else None
        datetimes = get_datetimes(self.display_days)
        chart_data = list()
        for date in datetimes:
            chart_data.append([date.strftime('%d.%m'),
                               product.get_price(date)])
        chart_data = json.dumps(chart_data)
        package_key = product.category.get_data('normal_package')
        product_category_title = product.category.get_data(
            'keyword').split(', ')[0]
        product_category_url = self.request.resource_url(product.category)
        package_title = ProductPackage(package_key).get_data('synonyms')[0]
        type_ = product.category.category
        category_title = type_.title
        category_title_ru = type_.get_data('title_ru')
        category_primary_color = type_.get_data('primary_color')
        category_background_color = type_.get_data('background_color')
        reports = list()

        for report in sorted(product.get_reports(
                from_date_time=self.delta_period),
                reverse=True, key=lambda rep: rep.date_time):
            url = self.request.resource_url(report)
            date = format_datetime(report.date_time, format='short',
                                   locale=self.request.locale_name)
            merchant = report.merchant.title
            location = report.merchant.location
            price = self.currency(report.normalized_price_value)
            reports.append((url, date, merchant, location, price))

        return {
            'current_price': current_price,
            'product_delta': product_delta,
            'last_report_url': last_report_url,
            'chart_data': chart_data,
            'reports': reports,
            'product_category_title': product_category_title,
            'product_category_url': product_category_url,
            'category_title': category_title,
            'category_title_ru': category_title_ru,
            'category_background_color': category_background_color,
            'category_primary_color': category_primary_color,
            'package_title': package_title
        }

    @view_config(renderer='product.mako', request_method='GET')
    def get(self):
        return self.serve_data(self.context)


@view_defaults(custom_predicates=(namespace_predicate(PriceReport),))
class PriceReportsView(EntityView):
    """PriceReports collection views"""

    @view_config(request_method='POST', renderer='json')
    def post(self):
        # TODO Implement validation
        try:
            dict_list = multidict_to_list(self.request.params)
        except MultidictError as e:
            raise HTTPBadRequest(e.message)
        counts = {'product': 0,
                  'category': 0,
                  'package': 0}
        new_report_keys = list()
        error_msgs = list()
        for dict_ in dict_list:
            try:
                report, new_items = PriceReport.assemble(
                    storage_manager=self.root, **dict_)
                new_report_keys.append(report.key)
                prod_is_new, cat_is_new, pack_is_new = new_items
                counts['product'] += int(prod_is_new)
                counts['category'] += int(cat_is_new)
                counts['package'] += int(pack_is_new)
            except (PackageLookupError, CategoryLookupError, ValueError,
                    TypeError) as e:
                error_msgs.append(e.message)
        counts['total'] = len(dict_list)
        counts['report'] = len(new_report_keys)
        counts['error'] = len(error_msgs)
        if len(new_report_keys):
            general_region.invalidate(hard=False)
            reporters = ', '.join(
                set(self.request.params.getall('reporter_name')))
            # send email
            from pyramid_mailer import get_mailer
            from pyramid_mailer.message import Message
            mailer = get_mailer(self.request)
            message = Message(
                subject=u'Price Watch: отчеты от {}'.format(reporters),
                sender='no-reply@food-price.net',
                recipients=["mkorinets@gmail.com"],
                html=render('email/post_report_stats.mako',
                            {'counts': counts,
                             'reporters': reporters,
                             'error_msgs': error_msgs}))
            mailer.send(message)

            return {
                'new_report_keys': new_report_keys,
                'counts': counts,
                'errors': error_msgs
            }
        else:
            raise HTTPBadRequest('No new reports\n' +
                                 '\n'.join(error_msgs))


@view_defaults(context=PriceReport)
class PriceReportView(EntityView):
    """PriceReport instance views"""

    @view_config(request_method='GET', renderer='report.mako')
    def get(self):
        return {}

    @view_config(request_method='DELETE', renderer='json')
    def delete(self):

        self.context.delete_from(self.root)
        general_region.invalidate(hard=False)
        return {'deleted_report_key': self.context.key}


@view_defaults(custom_predicates=(namespace_predicate(ProductCategory),))
class ProductCategoriesView(EntityView):
    """ProductCategory collection view"""

    @view_config(request_method='GET', renderer='json', xhr=True)
    def get(self):
        if 'ingredients' in self.request.params:
            ingredients_text = self.request.params.getone('ingredients')
            return {}


@view_defaults(context=ProductCategory)
class ProductCategoryView(EntityView):

    @general_region.cache_on_arguments('category')
    def serve_data(self, product_category, location):
        """Return prepared category data"""
        category = product_category.category
        category_title = category.title
        category_title_ru = category.get_data('title_ru')
        category_primary_color = category.get_data('primary_color')
        category_background_color = category.get_data('background_color')
        prod_cat_title = product_category.get_data('ru_accu_case')
        median = product_category.get_price(location=location)
        category_delta = int(product_category.get_price_delta(
            self.delta_period, location=location)*100)
        if not prod_cat_title:
            prod_cat_title = product_category.get_data(
                'keyword').split(', ')[0]
        package_key = product_category.get_data('normal_package')
        package_title = ProductPackage(package_key).get_data('synonyms')[0]

        chart_data = list()
        datetimes = get_datetimes(self.display_days)
        for date in datetimes:
            chart_data.append([date.strftime('%d.%m'),
                               product_category.get_price(date, location=location)])
        products = list()
        locations = product_category.get_locations()
        current_path = self.request.resource_url(product_category)
        sorted_products = sorted(
            product_category.get_qualified_products(location=location),
            key=lambda pr: pr[1])
        for num, product_tuple in enumerate(sorted_products):
            try:
                product, price = product_tuple
                middle_num = int(len(sorted_products) / 2)
                is_median = (num == middle_num)
                if len(sorted_products) % 2 == 0:
                    is_median = (num == middle_num or num == middle_num-1)

                # construct data row as tuple
                products.append((
                    num+1,
                    product,
                    self.request.resource_url(product),
                    self.currency(price),
                    int(product.get_price_delta(self.delta_period)*100),
                    is_median
                ))
            except TypeError:
                pass
        return {
            'price_data': json.dumps(chart_data),
            'products': products,
            'cat_title': prod_cat_title,
            'current_location': location,
            'locations': locations,
            'category_title': category_title,
            'category_title_ru': category_title_ru,
            'category_background_color': category_background_color,
            'category_primary_color': category_primary_color,
            'current_path': current_path,
            'package_title': package_title,
            'median_price': self.currency(median) if median else None,
            'category_delta': category_delta if median else None
        }

    @view_config(request_method='GET',
                 renderer='product_category.mako')
    def get(self):
        category = self.request.context
        location = None
        if 'location' in self.request.params:
            location = self.request.params.getone('location')
        return self.serve_data(category, location)

    @general_region.cache_on_arguments('category')
    def serve_api_data(self, product_category, location):
        """Serve cached category data for API call"""
        median = product_category.get_price(location=location)
        category_delta = int(product_category.get_price_delta(
            self.delta_period, location=location)*100)
        title = product_category.get_data('keyword').split(', ')[0]
        package_key = product_category.get_data('normal_package')
        return {
            'title': title,
            'price': median,
            'package': package_key,
            'delta_percent': category_delta if median else None
        }

    @view_config(request_method='GET', renderer='json', xhr=True)
    def api_get(self):
        category = self.request.context
        location = None
        if 'location' in self.request.params:
            location = self.request.params.getone('location')
        return self.serve_api_data(category, location)


class RootView(EntityView):
    """General root views"""
    @general_region.cache_on_arguments('index')
    def served_data(self, location):
        """Serve general index data optionally filter by region"""
        categories = list(self.root['types'].values())
        categories.sort(key=lambda x: float(x.get_data('priority')),
                        reverse=True)

        # category list
        types = list()
        all_locations = set()
        for type_ in categories:
            category_tuples = list()
            type_title_ru = type_.get_data('title_ru')
            type_primary_color = type_.get_data('primary_color')
            type_background_color = type_.get_data('background_color')
            type_.categories.sort(
                key=lambda x: float(x.get_data('priority', default=0)),
                reverse=True)
            for category in type_.categories:
                price = category.get_price(location=location)
                if price:
                    price = self.currency(price)
                    query = {'location': location} if location else None
                    url = self.request.resource_path(category, query=query)
                    title = category.get_data('keyword').split(', ')[0]
                    delta = int(category.get_price_delta(self.delta_period,
                                                         location=location)*100)
                    package_key = category.get_data('normal_package')
                    package_title = ProductPackage(
                        package_key).get_data('synonyms')[0]
                    cat_locations = category.get_locations()
                    all_locations.update(cat_locations)
                    category_tuples.append((url, title, price, delta,
                                            package_title))
            types.append((type_.title, type_title_ru, type_primary_color,
                          type_background_color, category_tuples))
        time = format_datetime(datetime.datetime.now(), format='long',
                               locale=self.request.locale_name)
        return {'types': types,
                'time': time,
                'current_location': location,
                'locations': list(all_locations),
                'root': True}

    @view_config(request_method='GET', renderer='index.mako')
    def get(self):
        location = None
        if 'location' in self.request.params:
            location = self.request.params.getone('location')
        return self.served_data(location)

    @general_region.cache_on_arguments('sitemap')
    def serve_sitemap_data(self):
        url_tuples = list()

        # root
        loc = self.request.resource_url(self.root)
        priority = 1.0
        url_tuples.append((loc, priority))

        # pages
        pages = self.root['pages'].values()
        for page in pages:
            loc = self.request.resource_url(page)
            priority = 1.0
            url_tuples.append((loc, priority))

        # categories
        categories = self.root['categories'].values()
        all_locations = set()
        for category in categories:
            loc = self.request.resource_url(category)
            priority = 1.0
            url_tuples.append((loc, priority))
            locations = category.get_locations()
            all_locations.update(locations)
            for location in locations:
                query = {'location': location}
                loc = self.request.resource_url(category, query=query)
                priority = 0.8
                url_tuples.append((loc, priority))

        # root locations
        for location in list(all_locations):
            query = {'location': location}
            loc = self.request.resource_url(self.root, query=query)
            priority = 0.9
            url_tuples.append((loc, priority))

        # products
        products = self.root['products'].values()
        for product in products:
            loc = self.request.resource_url(product)
            priority = 0.5
            url_tuples.append((loc, priority))

        return {'url_tuples': url_tuples}

    @view_config(request_method='GET', renderer='sitemap.mako',
                 name='sitemap.xml')
    def sitemap(self):
        """Serve sitemap.xml"""
        self.request.response.content_type = 'text/xml'
        return self.serve_sitemap_data()

    @notfound_view_config(renderer='404.mako')
    def not_found(self):
        """A general 404 page"""
        self.request.response.status = 404
        return {}
