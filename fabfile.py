# -*- coding: utf-8 -*-

import json
import datetime
import transaction
import logging
from collections import OrderedDict
from ZODB.FileStorage import FileStorage
from fabric.api import *
from fabric.colors import *

from price_watch.models import (ProductCategory, StorageManager,
                                PriceReport, PackageLookupError, Reporter,
                                Product, Merchant, CategoryLookupError)

APP_NAME = 'food-price.net'
env.hosts = ['ubuntu@alpha.korinets.name']
env.key_filename = ['/home/yentsun/Dropbox/_Documents/AWS/yentsunkey.pem']

MULTIPLIER = 1
logging.basicConfig(filename='debug.log', level=logging.DEBUG)


def get_storage():
    return StorageManager(FileStorage('storage/storage.fs'))


def get_datetimes(days):
    """Return list with days back range"""

    result = list()
    for count in range(0, int(days)):
        date = datetime.date.today() + datetime.timedelta(-1*MULTIPLIER*count)
        date_time = datetime.datetime.combine(date,
                                              datetime.datetime.now().time())
        result.append(date_time)
    return result


@task
def output_data(days=14):
    """Generate JSON with data"""
    storage = StorageManager(FileStorage('storage.fs'))
    categories = ProductCategory.fetch_all(storage)
    dates = [datetime.date.today() + datetime.timedelta(-1*count)
             for count in range(0, int(days))]
    result = dict()
    for category in categories:
        result[category.key()] = OrderedDict()
        for date in dates:
            data_dict = dict()
            prices = category.get_prices(date)
            if len(prices) > 0:
                data_dict['median'] = category.get_price(date, prices=prices)
                data_dict['min'] = min(prices)
                data_dict['max'] = max(prices)
                result[category.title][str(date)] = data_dict
    with open('data.json', 'w') as f:
        json.dump(result, f, indent=2)
    storage.close()


@task
def set_normalized_price():
    """Walk through all reports and set normalized price_value"""

    storage = StorageManager(FileStorage('storage.fs'))
    reports = PriceReport.fetch_all(storage)
    for report in reports:
        try:
            del report.product.package
            report.product.package = report.product.get_package()
            report.normalized_price_value = \
                report._get_normalized_price(report.price_value)
            print('Report {0} updated'.format(report.uuid))
        except PackageLookupError, e:
            print(e.message)
    transaction.commit()
    storage.close()


@task
def set_package_ratio():
    """Walk through products and set `package` and `package_ratio`"""

    keeper = StorageManager(FileStorage('storage.fs'))
    products = Product.fetch_all(keeper)
    for product in products:
        try:
            product.package = product.get_package()
            product.package_ratio = product.package.get_ratio(product.category)
            print(green(u'Product "{}" updated'.format(product)))
        except AttributeError, e:
            print(red(u'{} removed'.format(product)))
            keeper.delete(product)
        except PackageLookupError, e:
            logging.debug(e.message.encode('utf-8'))
            print(yellow(e.message))
    transaction.commit()


@task
def add(merchant_str, title, price_value, url, date_time=None):
    """Add price report"""
    keeper = StorageManager(FileStorage('storage/storage.fs'))
    merchant = Merchant.acquire(merchant_str.decode('utf-8'), keeper)
    reporter = Reporter.acquire('Price Watch', keeper)
    if date_time:
        date_time = datetime.datetime.strptime(date_time, '%d.%m.%Y')
    try:
        report, stats_ = PriceReport.assemble(
            price_value=float(price_value),
            product_title=title.decode('utf-8'),
            url=url,
            merchant=merchant,
            reporter=reporter,
            date_time=date_time,
            storage_manager=keeper
        )
        transaction.commit()
        print(green(u'Report {} added'.format(report)))
    except (PackageLookupError, CategoryLookupError), e:
        transaction.abort()
        print(red(e.message))
    keeper.close()


@task
def display_category(category_key):
    """Display category data in table"""
    from prettytable import PrettyTable

    table = PrettyTable(['product', 'N', 'O',
                         'pack.'])
    table.align = 'l'
    keeper = StorageManager(FileStorage('storage.fs'))
    category = ProductCategory.fetch(category_key, keeper)
    min_package_ratio = category.get_data('min_package_ratio')
    products = category.products.values()
    if min_package_ratio:
        try:
            products = [product for product in products
                        if product.get_package().get_ratio(category) >=
                        float(min_package_ratio)]
        except PackageLookupError, e:
            print(e.message)
    sorted_products = sorted(products,
                             key=lambda pr: pr.get_last_reported_price())
    for num, product in enumerate(sorted_products):
        table.add_row([u'{}. {}'.format(num+1, product.title),
                       round(product.get_last_reported_price(), 2),
                       product.get_last_reported_price(normalized=False),
                       product.package])
    print(table)


@task
def stats(category_key, days=2):
    """Show daily statistics for a category"""
    from prettytable import PrettyTable
    table = PrettyTable(['date/time', 'report #', 'product #', 'median', 'min',
                         'max'])
    table.align = 'l'
    dates = get_datetimes(days)
    keeper = StorageManager(FileStorage('storage.fs'))
    category = ProductCategory.fetch(category_key, keeper)
    print(table)
    for date in dates:
        table.add_row([str(date),
                       len(category.get_reports(date)),
                       len(category.products),
                       category.get_price(date),
                       category.get_price(cheap=True),
                       max(category.get_prices(date))])


@task
def cleanup():
    """Perform cleanup and fixing routines on stored instances"""
    keeper = StorageManager(FileStorage('storage.fs'))
    products = Product.fetch_all(keeper, objects_only=False)

    print('Products check...')
    for key, product in products.iteritems():
        # key check
        if key != product.key():
            print(yellow(u'Fixing {}...'.format(key)))
            keeper.register(product)
            keeper.delete_key(product.__class__.__name__, key)
            del product.category.products[key]
            product.category.add_product(product)
            for merchant in product.merchants.values():
                del merchant.products[key]
                merchant.add_product(product)

        # reports check
        if len(product.reports) == 0:
            print(yellow(u'Deleting "{}"...'.format(product)))
            product.delete_from(keeper)

        # correct category check
        try:
            product.get_category_key()
        except CategoryLookupError:
            if product.category:
                category = product.category
                print(yellow(u'Deleting "{}" from "{}"'.format(product,
                                                               category)))
                category.remove_product(product)
                product.delete_from(keeper)

    print('Merchants check...')
    for merchant in Merchant.fetch_all(keeper):
        for key, product in merchant.products.items():
            if len(product.reports) == 0:
                print(yellow(u'Deleting "{}"...'.format(product)))
                del merchant.products[key]

    print('Categories check...')
    for category in ProductCategory.fetch_all(keeper):
        for key, product in category.products.items():
            if len(product.reports) == 0:
                print(yellow(u'Deleting "{}"...'.format(product)))
                del category.products[key]
    transaction.commit()


@task
def pack():
    """Pack the storage"""
    keeper = get_storage()
    keeper._db.pack()


@task
def prepare():
    res = local('git status', capture=True)
    print(yellow(res))
    local('git describe --tags > VERSION.txt')
    # local('~/env2/bin/python setup.py sdist --formats=gztar', capture=False)


@task
def deploy():
    prepare()
    dist = local('~/env2/bin/python setup.py --fullname', capture=True).strip()
    # upload distribution
    local('scp dist/{dist}.tar.gz '
          'ubuntu@alpha:www/{dist}.tar.gz'.format(dist=dist))
    # unpack
    with cd('www'):
        run('tar xzf {}.tar.gz '.format(dist))
        # remove distr
        run('rm -f {}.tar.gz'.format(dist))
    # install
    with cd('www/{}'.format(dist)):
        run('~/env/bin/python setup.py install')
    # run tests
    with cd('www/{}/price_watch/tests'.format(dist)):
        run('~/env/bin/nosetests unit_tests.py')
        run('~/env/bin/nosetests functional_tests.py')
    run('rm -rf ~/www/{}'.format(APP_NAME))
    run('mv ~/www/{dist} ~/www/{appname}'.format(appname=APP_NAME, dist=dist))
    with cd('www'):
        run('~/env/bin/supervisorctl restart food-price.net:*')