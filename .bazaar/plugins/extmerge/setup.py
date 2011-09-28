#!/usr/bin/env python2.4
try:
    from setuptools import setup
except ImportError:    
    from distutils.core import setup

setup(name='bzr-extmerge',
      description='External merge plugin for Bazaar',
      keywords='plugin bzr merge',
      version='0.0.1',
      url='http://erik.bagfors.nu/bzr-plugins/extmerge/',
      download_url='http://erik.bagfors.nu/bzr-plugins/extmerge/',
      license='GPLv2',
      author='Erik Bagfors',
      author_email='erik@bagfors.nu',
      long_description="""
      This plugin calls a user defined tool, if that exists. Otherwise, it tries kdiff3, xxdiff, meld and opendiff in that order. 
      """,
      package_dir={'bzrlib.plugins.extmerge':'.'},
      packages=['bzrlib.plugins.extmerge']
      )
