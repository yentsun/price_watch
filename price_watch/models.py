import os
import datetime
import yaml
import json
import numpy
import urllib
from uuid import uuid4
from ZODB import DB
from persistent import Persistent
from operator import attrgetter
from BTrees import OOBTree


HOUR_AGO = datetime.datetime.now() - datetime.timedelta(hours=1)
DAY_AGO = datetime.datetime.now() - datetime.timedelta(days=1)
WEEK_AGO = datetime.datetime.now() - datetime.timedelta(weeks=1)
TWO_WEEKS_AGO = datetime.datetime.now() - datetime.timedelta(weeks=2)
MONTH_AGO = datetime.datetime.now() - datetime.timedelta(days=30)

# time, during which report's price matters
REPORT_LIFETIME = datetime.timedelta(weeks=1)


def get_delta(base_price, current_price, relative=True):
    """Return delta relative or absolute"""
    try:
        abs_delta = current_price - base_price
        if relative:
            return abs_delta / base_price
        else:
            return abs_delta
    except TypeError:
        return 0


def load_data_map(node):
    """Return parsed `data_map.yaml`"""

    dir_ = os.path.dirname(__file__)
    filename = os.path.join(dir_, 'data_map.yaml')
    with open(filename) as map_file:
        return yaml.safe_load(map_file)[node]


def mixed_keys(list_):
    """Return combined list of str items and dict first keys (for parsed yaml
       structures)"""
    result = list()
    for item in list_:
        if type(item) is str:
            result.append(item)
        else:
            result.append(item.keys()[0])
    return result


def traverse(target, category_node, return_parent=False):
    """
    Recursively look for appropriate category from the tree in
    `data_map.yaml`
    """
    try:
        subcategories = category_node['sub']
        if target in subcategories:
            if return_parent:
                return category_node
            else:
                return subcategories[target]
        for key in subcategories:
            match = traverse(target, subcategories[key],
                             return_parent=return_parent)
            if match:
                return match
    except (KeyError, TypeError):
        pass


def keyword_lookup(string_, data_map):
    """
    Recursively look for appropriate category from the tree in
    `data_map.yaml`, checking by presence of a category keyword in the string
    """
    requirements_met = list()
    if 'keyword' not in data_map:
        requirements_met.append(False)
    else:
        keyphrase_requirements_met = list()
        key_phrases = data_map['keyword'].split(', ')
        for phrase in key_phrases:
            phrase_requirements_met = list()
            phrase_parts = phrase.split(' ')
            for phrase_part in phrase_parts:
                phrase_requirements_met.append(phrase_part in string_)
            keyphrase_requirements_met.append(all(phrase_requirements_met))
        requirements_met.append(any(keyphrase_requirements_met))
    if 'stopword' in data_map:
        stopword_parts = data_map['stopword'].split(' ')
        for stopword_part in stopword_parts:
            requirements_met.append(stopword_part not in string_)
    if all(requirements_met):
        return data_map
    if 'sub' in data_map:
        subcategories = data_map['sub']
        for key in subcategories:
            category_data = subcategories[key]
            if category_data:
                match = keyword_lookup(string_, category_data)
                if match:
                    return match


class PackageLookupError(Exception):
    """Exception for package not found in `data_map.yaml`"""
    def __init__(self, product):
        message = u'Package lookup failed ' \
                  u'for product "{0}"'.format(product.title)

        Exception.__init__(self, message)
        self.product = product


class CategoryLookupError(Exception):
    """Exception for category not found in `data_map.yaml`"""
    def __init__(self, product):
        message = u'Category lookup failed for ' \
                  u'product "{}"'.format(product.title)
        Exception.__init__(self, message)
        self.product = product


class StorageManager(object):
    """Persistence tool for entity instances."""

    def __init__(self, zodb_storage=None, connection=None):
        if zodb_storage is not None:
            self._db = DB(zodb_storage)
            self._zodb_storage = zodb_storage
        if connection is not None:
            self.connection = connection
        else:
            self.connection = self._db.open()
        self._root = self.connection.root()

    def __getitem__(self, namespace):
        """Container behavior"""
        return self._root[namespace]

    def register(self, *instances):
        """Register new instances to appropriate namespaces"""
        for instance in instances:
            namespace = instance.namespace
            if namespace not in self._root:
                self._root[namespace] = OOBTree.BTree()
            if instance.key not in self._root[namespace]:
                self._root[namespace][instance.key] = instance

    def delete(self, *instances):
        """Delete instances from appropriate namespaces"""
        for instance in instances:
            instance.delete_from(self)

    def delete_key(self, namespace, key):
        """Delete given key in the namespace"""
        try:
            del self._root[namespace][key]
            return True
        except KeyError:
            return False

    def get(self, namespace, key):
        """Get instance from appropriate namespace by the key"""
        try:
            return self._root[namespace][key]
        except KeyError:
            return None

    def get_all(self, namespace, objects_only=True):
        """Get all instances from namespace"""
        result = None
        if namespace in self._root:
            result = self._root[namespace]
        if objects_only:
            return result.values()
        else:
            return result

    def close(self):
        """Close ZODB connection and storage"""
        self.connection.close()
        self._zodb_storage.close()

    def load_fixtures(self, path):
        """Load fixtures from JSON file in path. Mostly for testing"""
        result = dict(reports=[], pages=[])
        with open(path) as f:
            fixture_list = json.load(f)
            for fixture in fixture_list:
                try:
                    report, stats = PriceReport.assemble(storage_manager=self,
                                                         **fixture)
                    result['reports'].append(report)
                except TypeError:
                    page = Page.assemble(storage_manager=self, **fixture)
                    result['pages'].append(page)
        return result


class Entity(Persistent):
    """Master class to inherit from. Used to implement ORM"""
    _representation = u'{title}'
    _key_pattern = u'{title}'
    namespace = None

    def __str__(self):
        return str(self.__repr__().encode('utf-8'))

    def __unicode__(self):
        return self.__repr__()

    def __repr__(self):
        """Unique representational string"""
        return self._representation.format(**self.__dict__)

    @property
    def __name__(self):
        """For compatibility with pyramid traversal"""
        return self.key

    def _get_inner_container(self):
        """
        Return the inner container if the instance has it
        """
        if hasattr(self, '_container_attr'):
            container_name = getattr(self, '_container_attr')
            container = getattr(self, container_name)
            return container
        else:
            raise NotImplementedError

    def __getitem__(self, key):
        """Container behaviour"""
        inner_container = self._get_inner_container()
        return inner_container[key]

    def __contains__(self, key):
        """Container behaviour"""
        inner_container = self._get_inner_container()
        return key in inner_container

    def __resource_url__(self, request, info):
        """For compatibility with pyramid traversal"""
        parts = {
            'app_url': info['app_url'],
            'collection': self.namespace,
            'key': urllib.quote(self.key.encode('utf-8'), safe='')
        }
        return u'{app_url}/{collection}/{key}/'.format(**parts)

    @property
    def key(self):
        """Return unique key based on `_key_pattern`"""
        raw_key = self._key_pattern.format(**self.__dict__)
        return raw_key.replace('/', '-')

    @classmethod
    def fetch(cls, key, storage_manager):
        """Fetch instance from storage"""
        return storage_manager.get(cls.namespace, key)

    @classmethod
    def fetch_all(cls, storage_manager, objects_only=True):
        """Fetch all instances from storage"""
        return storage_manager.get_all(cls.namespace, objects_only)

    @classmethod
    def acquire(cls, key_attr, storage_manager, return_tuple=False):
        """
        Fetch or register new instance and return it in tuple
        with status
        """
        created_new = False
        key = cls(key_attr).key
        stored_instance = cls.fetch(key, storage_manager)

        if not stored_instance:
            new_instance = cls(key_attr)
            storage_manager.register(new_instance)
            stored_instance = new_instance
            created_new = True
        if return_tuple:
            return stored_instance, created_new
        else:
            return stored_instance

    @classmethod
    def assemble(cls, **kwargs):
        """
        Minimal data instance factory. Encouraged to be the only way of
        initializing entities.
        """
        raise NotImplementedError

    def delete_from(self, storage_manager):
        """Properly delete class instance from the storage_manager"""
        raise NotImplementedError


class PriceReport(Entity):
    """Price report model, the working horse"""
    _representation = u'{price_value}-{product}-{merchant}-{reporter}'
    _key_pattern = '{uuid}'
    namespace = 'reports'

    def __init__(self, price_value, product, reporter, merchant,
                 url=None, date_time=None):
        self.uuid = uuid4()
        self.date_time = date_time or datetime.datetime.now()
        self.merchant = merchant
        self.product = product
        self.price_value = price_value
        self.normalized_price_value = self._get_normalized_price(price_value)
        self.reporter = reporter
        self.url = url

    def _get_normalized_price(self, price_value):
        """Return `normal` package price value for a product"""

        package = self.product.get_package()
        ratio = package.get_ratio(self.product.category)

        return price_value / ratio

    def delete_from(self, storage_manager):
        """Delete the report from product and storage"""
        try:
            del self.product.reports[self.key]
            del self.reporter.reports[self.key]
        except (KeyError, AttributeError):
            pass
        storage_manager.delete_key(self.namespace, self.key)

    @classmethod
    def acquire(cls, key, storage_manager, return_tuple=False):
        """Disallow acquiring of reports. Only pure fetching!"""

        raise NotImplementedError

    @classmethod
    def assemble(cls, storage_manager, price_value, product_title,
                 merchant_title, reporter_name, url, date_time=None):
        """
        The only encouraged factory method for price reports and all the
        referenced instances:
          - product
          - category
          - package
          - merchant
          - reporter
        `date_time` is expected to be str in `%Y-%m-%d %H:%M:%S` format or
        datetime object.
        New report is registered in storage.
        """

        if type(date_time) in (str, unicode):
            try:
                date_time = datetime.datetime.strptime(date_time,
                                                       '%Y-%m-%d %H:%M:%S')
            except ValueError:
                #  microseconds in string?
                date_time = datetime.datetime.strptime(date_time.split('.')[0],
                                                       '%Y-%m-%d %H:%M:%S')

        prod_is_new = cat_is_new = pack_is_new = False
        product_key = Product(product_title).key
        merchant_key = Merchant(merchant_title).key
        product = Product.fetch(product_key, storage_manager)
        merchant = Merchant.acquire(merchant_key, storage_manager)
        reporter = Reporter.acquire(reporter_name, storage_manager)

        if not product:
            prod_is_new = True
            product = Product(product_title)

            # category
            category_key = product.get_category_key()
            category, cat_is_new = ProductCategory.acquire(category_key,
                                                           storage_manager,
                                                           True)
            category.add_product(product)

            # package
            package_key = product.get_package_key()
            package, pack_is_new = ProductPackage.acquire(package_key,
                                                          storage_manager,
                                                          True)
            package.add_category(category)
            product.package = package
            category.add_package(package)
            product.package_ratio = package.get_ratio(category)

            storage_manager.register(product)

        # merchant
        product.add_merchant(merchant)
        merchant.add_product(product)

        # report
        report = cls(price_value=float(price_value), product=product,
                     reporter=reporter, merchant=merchant, url=url,
                     date_time=date_time)
        reporter.add_report(report)
        product.add_report(report)

        storage_manager.register(report)

        stats = prod_is_new, cat_is_new, pack_is_new

        return report, stats


class Merchant(Entity):
    """Merchant model"""
    _representation = u'{title}-{location}'
    namespace = 'merchants'

    def __init__(self, title, location=None):
        self.title = title
        self.location = location
        self.products = OOBTree.BTree()

    def update(self, data, storage_manager):
        """Update merchant from dict. Return `True` if new key created"""
        old_key = self.key
        self.title = data['title']
        if old_key != self.key:
            storage_manager.register(self)
            try:
                storage_manager.delete_key(self.namespace, old_key)
                for product in self.products.values():
                    del product.merchants[old_key]
                    product.add_merchant(self)
            except KeyError:
                pass

    def add_product(self, product):
        """Add product to products dict"""
        if product.key not in self.products:
            self.products[product.key] = product


class ProductPackage(Entity):
    """Product package model"""
    namespace = 'packages'

    def __init__(self, title):
        self.title = title
        self.categories = OOBTree.BTree()

    def add_category(self, category):
        """Add category to package"""
        if category.key not in self.categories:
            self.categories[category.key] = category

    def get_data(self, attribute, default=None):
        """Get category data from `data_map.yaml`"""
        data_map = load_data_map(self.__class__.__name__)
        try:
            data = data_map[self.title][attribute]
            return data
        except KeyError:
            return default

    def is_normal(self, category):
        """Check if the package is `normal` for a product's category"""
        cat_canonical = category.get_data('normal_package')
        return cat_canonical == self.title

    def convert(self, to_unit, category):
        """Convert instance amount to amount in given units"""
        pack_amount, from_unit = self.title.split(' ')
        density = float(category.get_data('density'))
        pack_amount = float(pack_amount)
        if from_unit == 'kg' and to_unit == 'l':
            m3 = pack_amount / density  # pack_amount is weight
            liters = m3 * 1000
            return liters
        if from_unit == 'l' and to_unit == 'kg':
            kilogramms = density * pack_amount  # pack_amount is volume
            return kilogramms

    def get_ratio(self, category):
        """Get ratio to the normal package"""
        norm_package = category.get_data('normal_package')
        norm_amount, norm_unit = norm_package.split(' ')
        pack_amount, pack_unit = self.title.split(' ')
        if norm_unit != pack_unit:
            pack_amount = self.convert(norm_unit, category)
        result = float(pack_amount) / float(norm_amount)
        return result


class ProductCategory(Entity):
    """Product category model"""
    _container_attr = 'products'
    namespace = 'categories'

    def __init__(self, title):
        self.title = title
        self.products = OOBTree.BTree()

    def get_data(self, attribute):
        """Get category data from `data_map.yaml`"""
        data_map = load_data_map(self.__class__.__name__)
        category = traverse(self.title, data_map)
        try:
            data = category[attribute]
            return data
        except KeyError:
            return None

    def get_parent(self):
        """Get parent category using `find_parent`"""
        # TODO decide if this should be taken from storage by default
        data_map = load_data_map(self.__class__.__name__)
        parent_category_dict = traverse(self.title, data_map,
                                        return_parent=True)
        try:
            return ProductCategory(parent_category_dict['title'])
        except TypeError:
            return None

    def add_product(self, *products):
        """Add product(s) to the category and set category to the products"""

        for product in products:
            product.category = self
            if product.key not in self.products:
                self.products[product.key] = product

    def remove_product(self, product):
        """
        Remove product from the category and set its `category`
        attribute to None
        """
        product.category = None
        if product.key in self.products:
                del self.products[product.key]

    def add_package(self, package):
        """Add package to the category"""

        if not hasattr(self, 'packages'):
            self.packages = OOBTree.BTree()
        if package.key not in self.packages:
            self.packages[package.key] = package

    def get_reports(self, date_time=None):
        """Get price reports for the category by datetime"""

        result = list()
        for key, product in self.products.items():
            result.extend(product.get_reports(date_time))
        return result

    def get_qualified_products(self):
        """Return products list filtered by qualification conditions"""

        min_package_ratio = self.get_data('min_package_ratio')
        products = self.products.values()
        filtered_products = list()
        for product in products:
            package_fit = True
            if min_package_ratio:
                package_fit = product.package_ratio >= float(min_package_ratio)
            # Actual qualification
            if package_fit and product.get_price():
                filtered_products.append(product)
        return filtered_products

    def get_prices(self, date_time=None):
        """
        Fetch last known to `date_time` prices filtering by `min_package_ratio`
        """
        result = list()
        products = self.get_qualified_products()
        for product in products:
            price = product.get_last_reported_price(date_time)
            if price:
                result.append(price)
        return result

    def get_price(self, date_time=None, prices=None, cheap=False):
        """Get median or minimum price for the date"""

        prices = prices or self.get_prices(date_time)
        if len(prices):
            if cheap:
                try:
                    return min(prices)
                except ValueError:
                    return None
            else:
                prices = numpy.array(prices)
                return round(numpy.median(prices), 2)
        return None

    def get_price_delta(self, date_time, relative=True):

        base_price = self.get_price(date_time)
        current_price = self.get_price()
        return get_delta(base_price, current_price, relative)


class Product(Entity):
    """Product model"""

    _container_attr = 'reports'
    namespace = 'products'

    def __init__(self, title, category=None, manufacturer=None, package=None,
                 package_ratio=None):
        self.title = title
        self.manufacturer = manufacturer
        self.category = category
        self.package = package
        self.package_ratio = package_ratio
        self.reports = OOBTree.BTree()
        self.merchants = OOBTree.BTree()

    def add_report(self, report):
        """Add report"""

        if report.key not in self.reports:
            self.reports[report.key] = report

    def add_merchant(self, merchant):
        """Add merchant"""

        if merchant.key not in self.merchants:
            self.merchants[merchant.key] = merchant

    def get_prices(self, date_time=None, normalized=True):
        """Get prices from reports for a given date"""

        result = list()
        reports = self.get_reports(date_time=date_time)
        if len(reports) > 0:
            for report in reports:
                if normalized:
                    price_value = report.normalized_price_value
                else:
                    price_value = report.price_value
                result.append(price_value)
        return result

    def get_price(self, date_time=None, normalized=True):
        """Get price for the product"""
        date_time = date_time or datetime.datetime.now()
        known_prices = list()
        for merchant in self.merchants.values():
            report = self.get_last_report(date_time=date_time,
                                          merchant=merchant)
            if report and report.date_time > date_time - REPORT_LIFETIME:
                if normalized:
                    price = report.normalized_price_value
                else:

                    price = report.price_value
                known_prices.append(price)
        if len(known_prices):
            return numpy.median(known_prices)
        else:
            return None

    def get_price_delta(self, date_time, relative=True):

        base_price = self.get_last_reported_price(date_time)
        current_price = self.get_last_reported_price()
        return get_delta(base_price, current_price, relative)

    def get_reports(self, to_date_time=None, from_date_time=None):
        """Get reports to the given date/time"""

        result = list()
        for report in self.reports.values():
            qualifies = True
            if to_date_time and report.date_time > to_date_time:
                qualifies = False
            if from_date_time and report.date_time < from_date_time:
                qualifies = False
            if qualifies:
                result.append(report)
        return result

    def get_package_key(self):
        """Resolve product's package key from known ones"""

        package_data = load_data_map(ProductPackage.__name__)
        for pack_key in sorted(package_data,
                               key=lambda key: len(key), reverse=True):
            for synonym in package_data[pack_key]['synonyms']:
                if u' {}'.format(synonym) in self.title:
                    return pack_key
        raise PackageLookupError(self)

    def get_package(self):
        """Compatibility method if there's no package defined"""
        if hasattr(self, 'package') and self.package:
            return self.package
        else:
            key = self.get_package_key()
            return ProductPackage(key)

    def get_category_key(self):
        """
        Get category key from the product's title by looking up keywords
        in `data_map.yaml`
        """
        data_map = load_data_map(ProductCategory.__name__)
        category_data = keyword_lookup(self.title.lower(), data_map)
        if category_data:
            return category_data['title']
        raise CategoryLookupError(self)

    def get_last_report(self, date_time=None, merchant=None):
        """Get last (to `date_time`) report of the product"""

        date_time = date_time or datetime.datetime.now()

        def qualify(report):
            qualified = True
            if report.date_time > date_time:
                qualified = False
            if merchant and report.merchant is not merchant:
                qualified = False
            return qualified

        # TODO decide which one to do first sorting or filtering
        reports = self.reports.values()
        if len(reports) > 0:
            sorted_reports = sorted(reports,
                                    key=attrgetter('date_time'))
            filtered_reports = filter(qualify, sorted_reports)
            try:
                return filtered_reports[-1]
            except IndexError:
                return None
        else:
            return None

    def get_last_reported_price(self, date_time=None, normalized=True):
        """Get product price last known to the date"""

        last_report = self.get_last_report(date_time)
        if last_report:
            if normalized:
                return last_report.normalized_price_value
            return last_report.price_value
        return None

    def delete_from(self, storage_manager):
        """Delete the product from all referenced objects"""
        key = self.key
        try:
            del self.category.products[key]
            for merchant in self.merchants.values():
                del merchant.products[key]
        except AttributeError:
            pass
        for report in self.reports.values():
            report.delete_from(storage_manager)
        storage_manager.delete_key(self.namespace, key)


class Reporter(Entity):
    """Reporter model"""
    _representation = u'{name}'
    _key_pattern = u'{name}'
    _container_attr = 'reports'
    namespace = 'reporters'

    def __init__(self, name):
        self.name = name
        self.reports = OOBTree.BTree()

    def add_report(self, report):
        """Add report"""
        if report.key not in self.reports:
            self.reports[report.key] = report


class Page(Entity):
    """Page model (static text)"""
    _representation = u'{slug}'
    _key_pattern = u'{slug}'
    namespace = 'pages'

    def __init__(self, slug):
        self.slug = slug

    @classmethod
    def assemble(cls, storage_manager, slug):
        new_page = cls(slug)
        storage_manager.register(new_page)
        return new_page

    def delete_from(self, storage_manager):
        """Delete the page instance from storage"""
        storage_manager.delete_key(self.namespace, self.key)