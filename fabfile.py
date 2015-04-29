# -*- coding: utf-8 -*-

import sys
import datetime
import transaction
import logging
from ZODB.FileStorage import FileStorage
from fabric.api import *
from fabric.colors import *

from price_watch.models import (ProductCategory, StorageManager,
                                ProductPackage, PriceReport, Category,
                                PackageLookupError, Product, Merchant,
                                CategoryLookupError)

APP_NAME = 'food-price.net'
env.hosts = ['ubuntu@alpha.korinets.name']
env.key_filename = ['/home/yentsun/Dropbox/Documents/AWS/yentsunkey.pem']

MULTIPLIER = 1
logging.basicConfig(filename='debug.log', level=logging.DEBUG)


def get_storage(path_='storage/storage.fs'):
    return StorageManager(path_)


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
def fix_normalized_price():
    """
    Walk through all reports and fix normalized price_value
    and product package
    """

    keeper = get_storage()
    reports = PriceReport.fetch_all(keeper)
    for report in reports:
        try:
            correct_package_key = report.product.get_package_key()
            if report.product.package.key != correct_package_key:
                correct_package = ProductPackage.acquire(correct_package_key,
                                                         keeper)
                product = Product.fetch(report.product.key, keeper)
                print(yellow(u'Fixing package for {}: {}-->{}'.format(
                    report.product, product.package, correct_package)))
                product.package = correct_package
                report.product = product

            old_norm_price = report.normalized_price_value
            new_norm_price = report._get_normalized_price(report.price_value)
            if old_norm_price != new_norm_price:
                print(yellow(u'Fixing normal price {}-->{}'.format(
                      old_norm_price, new_norm_price)))
                report.normalized_price_value = new_norm_price
        except PackageLookupError, e:
            print(e.message)
    transaction.commit()
    keeper.close()


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
def display_category(category_key):
    """Display category data in table"""
    from prettytable import PrettyTable

    table = PrettyTable(['product', 'N', 'O',
                         'pack.'])
    table.align = 'l'
    keeper = get_storage()
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
def recreate():
    """Recreate storage from reports"""
    keeper = get_storage()
    new_keeper = get_storage('storage/new.fs')

    reports = PriceReport.fetch_all(keeper)
    print(cyan('Recreating storage from {} reports...'.format(len(reports))))
    for report in reports:
        try:
            PriceReport.assemble(storage_manager=new_keeper,
                                 uuid=report.uuid,
                                 price_value=report.price_value,
                                 product_title=report.product.title,
                                 merchant_title=report.merchant.title,
                                 reporter_name=report.reporter.name,
                                 url=report.url,
                                 date_time=report.date_time)
        except CategoryLookupError:
            print(yellow(u'Dropping `{}`: '
                         u'no category...'.format(report.product)))
    transaction.commit()
    keeper.close()
    new_keeper.close()


@task
def cleanup(entity_class_name=None):
    """Perform cleanup and fixing routines on stored instances"""

    if entity_class_name:
        entity_list = [entity_class_name]
    else:
        entity_list = ['ProductCategory', 'Product', 'Merchant', 'PriceReport']

    def cycle(entity_class_name_, keeper):
        """Perform all needed routines on an `entity_class`"""

        print(cyan('{} check...'.format(entity_class_name_)))
        entity_class = globals()[entity_class_name_]
        instances = entity_class.fetch_all(keeper, objects_only=False)

        for key in instances.keys():
            instance = instances[key]
            if entity_class is ProductCategory:

                if not hasattr(instance, 'category') or not instance.category:
                    category_key = instance.get_category_key()
                    category = Category.acquire(category_key, keeper)
                    instance.category = category
                    category.add(instance)
                    print(green(u'Added {} to {}'.format(instance, category)))

                for product in instance.products:
                    if product.category is not instance:
                        instance.remove_product(product)
                        print(yellow(u'Removed '
                                     u'`{}` from `{}`...'.format(product,
                                                                 instance)))
                    if len(product.reports) == 0:
                        instance.remove_product(product)
                        print(yellow(u'Removed stale '
                                     u'`{}` from `{}`...'.format(product,
                                                                 instance)))
                    if product.key not in keeper[product.namespace]:
                        try:
                            instance.remove_product(product)
                            print(yellow(u'Removed `{}` from `{}` '
                                         u'as its not '
                                         u'registered...'.format(product,
                                                                 instance)))
                        except ValueError:
                            pass

            if entity_class is Product:

                if type(instance.reports) is not list:
                    print(yellow(u'Fixing product report '
                                 u'list for `{}`...'.format(instance)))
                    instance.reports = list(instance.reports.values())

                if type(instance.merchants) is not list:
                    print(yellow(u'Fixing product merchant '
                                 u'list for `{}`...'.format(instance)))
                    instance.merchants = list(instance.merchants.values())

                if len(instance.reports) == 0:
                    print(yellow(u'Removing stale `{}`...'.format(instance)))
                    instance.delete_from(keeper)

                # check category
                try:
                    cat_key = instance.get_category_key()
                    category = ProductCategory.fetch(cat_key, keeper)
                    if instance.category is not category:
                        print(yellow(u'Adding `{}` to '
                                     u'`{}`...'.format(instance, category)))
                        category.add_product(instance)
                        instance.category = category
                except CategoryLookupError:
                    print(yellow(u'Removing `{}` as no '
                                 u'category found...'.format(instance)))
                    instance.delete_from(keeper)

                # check key
                if key != instance.key:
                    print(yellow(u'Fixing key for `{}`...'.format(key)))
                    keeper.register(instance)
                    keeper.delete_key(instance.namespace, key)

            if entity_class is Merchant:
                if type(instance.products) is not list:
                    instance.products = list(instance.products.values())
                for product in instance.products:
                    if len(product.reports) == 0:
                        print(yellow(u'Deleting `{}` '
                                     u'from `{}`...'.format(product,
                                                            instance)))
                        instance.remove_product(product)
                    for report in product.reports:
                        if type(report) is str:
                            print(yellow('Removing product with str report ...'))
                            product.delete_from(keeper)

            if entity_class is PriceReport:
                try:
                    correct_package_key = instance.product.get_package_key()
                except PackageLookupError, e:
                    print(e.message)
                else:
                    if instance.product.category is None:
                        print(yellow(u'Removing report '
                                     u'for {}'.format(instance.product)))
                        instance.delete_from(keeper)
                        break
                    if instance.product.package.key != correct_package_key:
                        correct_package = ProductPackage.acquire(
                            correct_package_key, keeper)
                        product = Product.fetch(report.product.key, keeper)
                        print(yellow(u'Fixing package for {}: {}-->{}'.format(
                            report.product, product.package, correct_package)))
                        product.package = correct_package
                        report.product = product

                    old_norm_price = instance.normalized_price_value
                    correct_norm_price = instance._get_normalized_price(
                        instance.price_value)
                    if old_norm_price != correct_norm_price:
                        print(yellow(
                            u'Fixing normal price '
                            u'for {} report ({}-->{})'.format(
                                instance.product, old_norm_price,
                                correct_norm_price)))
                        instance.normalized_price_value = correct_norm_price

            transaction.commit()
    keeper = get_storage()
    for entity_class_name in entity_list:
        cycle(entity_class_name, keeper)
    keeper.close()



@task
def download():
    """Download the storage file"""
    print(cyan('Downloading storage...'))
    local('scp ubuntu@alpha:www/storage/food-price.net/storage.fs '
          '~/Downloads/storage.fs')
    local('cp ~/Downloads/storage.fs ~/Dropbox/Vault/food-price.net')
    local('cp ~/Downloads/storage.fs storage/storage.fs')


@task
def backup():
    """Backup the remote storage"""
    print(yellow('Stopping processes...'))
    with cd('www'):
        run('~/env/bin/supervisorctl stop food-price.net:*')
    print(cyan('Packing storage...'))
    with cd('www/food-price.net'):
        run('~/env/bin/pack_storage production.ini')
    print(cyan('Starting processes...'))
    with cd('www'):
        run('~/env/bin/supervisorctl start food-price.net:*')
    download()


@task
def prepare():
    res = local('git status', capture=True)
    if 'nothing to commit, working directory clean' in res:
        local('git describe --tags > VERSION.txt')
        local('~/env2/bin/python setup.py sdist --formats=gztar',
              capture=False)
    else:
        print(yellow('Git: directory not clean.'))
        sys.exit()


@task
def deploy():
    print(cyan('Preparing package...'))
    prepare()
    print(cyan('Uploading package...'))
    dist = local('~/env2/bin/python setup.py --fullname',
                 capture=True).strip()
    local('scp dist/{dist}.tar.gz '
          'ubuntu@alpha:www/{dist}.tar.gz'.format(dist=dist))
    print(cyan('Unpacking...'))
    with cd('www'):
        run('tar xzf {}.tar.gz '.format(dist))
        # remove distr
        run('rm -f {}.tar.gz'.format(dist))
    print(cyan('Installing dependencies...'))
    with cd('www/{}'.format(dist)):
        run('~/env/bin/python setup.py install')
    print(cyan('Running tests...'))
    with cd('www/{}/price_watch/tests'.format(dist)):
        run('~/env/bin/nosetests lookup_tests.py')
        run('~/env/bin/nosetests unit_tests.py')
        run('~/env/bin/nosetests functional_tests.py')
    print(cyan('Swapping directories...'))
    run('rm -rf ~/www/{}'.format(APP_NAME))
    run('mv ~/www/{dist} ~/www/{appname}'.format(appname=APP_NAME, dist=dist))
    print(cyan('Restarting processes...'))
    with cd('www'):
        run('~/env/bin/supervisorctl restart food-price.net:*')