from setuptools import setup, find_packages
import os

version = '0.7dev'

setup(name='affinitic.zamqp',
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
      author='Jean-Francois Roche',
      author_email='jfroche@affinitic.be',
      url='http://bitbucket.org/jfroche/affinitic.zamqp',
      license='ZPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['affinitic'],
      include_package_data=True,
      zip_safe=False,
      entry_points={
            'console_scripts': [
                  'publishmsg = affinitic.zamqp.cli:main']},
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
