from setuptools import setup, find_packages
import os

version = '0.7.9'

setup(name='collective.zamqp',
      version=version,
      description="AMQP consumer and producer integration for Zope2",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Communications",
        "Topic :: System :: Distributed Computing",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Asko Soukka',
      author_email='asko.soukka@iki.fi',
      url='',
      license='ZPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      entry_points={
            'console_scripts': [
                  'publishmsg = collective.zamqp.cli:main']},
      extras_require=dict(
            test=['zope.testing', 'Zope2', 'five.dbevent'],
            zope210=['five.dbevent', 'uuid', 'python-cjson'],
            zope212=['five.dbevent', 'Zope2'],
            zope213=['Zope2'],
            docs=['z3c.recipe.sphinxdoc',
                  'collective.sphinx.includechangelog',
                  'repoze.sphinx.autointerface',
                  'collective.sphinx.includedoc']),
      install_requires=[
          'setuptools',
          'Zope2',
          'ZODB3',
          'transaction',
          'zope.component',
          'zope.event',
          'zope.processlifetime',
          'zope.browserpage',
          'grokcore.component',
          'pika == 0.9.5',
          'zope.deprecation',
          ])
