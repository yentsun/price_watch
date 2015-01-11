import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()
with open(os.path.join(here, 'VERSION.txt')) as f:
    VERSION = f.read().strip()

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'pyramid_zodbconn',
    'ZODB3',
    'waitress',
    'babel',
    'fabric',
    'dogpile',
    'numpy',
    'dogpile.cache',
    'webtest',
    'pyramid_dogpile_cache',
    'nose',
    'pyyaml',
    'colander',
    'pyramid_mailer'
]

setup(name='price_watch',
      version=VERSION,
      description='price_watch',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='',
      author_email='',
      url='',
      keywords='web pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="price_watch",
      entry_points="""\
      [paste.app_factory]
      main = price_watch:main
      """,
      )
