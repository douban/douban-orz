import os
from setuptools import setup, find_packages

# package meta info
NAME = "ORZ"
VERSION = "0.2.4.4"
DESCRIPTION = "missing data manager in shire, even in middle earth"
AUTHOR = "fuyuquan"
AUTHOR_EMAIL = "fuyuquan@douban.com"
URL = "http://code.dapps.douban.com/ORZ"
KEYWORDS = ""
CLASSIFIERS = []

# package contents
MODULES = []
PACKAGES = find_packages(exclude=['tests.*', 'tests', 'examples.*', 'examples'])

# dependencies
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
    url=URL,
    keywords=KEYWORDS,
    classifiers=CLASSIFIERS,
    py_modules=MODULES,
    packages=PACKAGES,
    zip_safe=False,
    test_suite='tests',
    # install_requires=[
    #     'DoubanCoreLib',
    # ],
    # dependency_links = [
    #     'git+http://code.dapps.douban.com/douban-corelib.git@b266b854eeb2365280bcc6aa6e4eaef6cd935486#egg=DoubanCoreLib-1.0',
    # ],
)
