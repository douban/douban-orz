import os
from setuptools import setup, find_packages

# package meta info
NAME = "ORZ"
VERSION = "0.2"
DESCRIPTION = "fuyuquan's orm"
AUTHOR = "fuyuquan"
AUTHOR_EMAIL = "fuyuquan@douban.com"
LICENSE = "Pirate"
URL = "http://code.dapps.douban.com/ORZ"
KEYWORDS = ""
CLASSIFIERS = []

# package contents
MODULES = []
PACKAGES = find_packages(exclude=['tests.*', 'tests', 'examples.*', 'examples'])

# dependencies
INSTALL_REQUIRES = []

here = os.path.abspath(os.path.dirname(__file__))

def read_long_description(filename):
    path = os.path.join(here, filename)
    if os.path.exists(path):
        return open(path).read()
    return ""

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=read_long_description('README.rst'),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url=URL,
    keywords=KEYWORDS,
    classifiers=CLASSIFIERS,
    py_modules=MODULES,
    packages=PACKAGES,
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
)
