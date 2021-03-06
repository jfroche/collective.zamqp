from setuptools import setup, find_packages

version = '0.7.17'

setup(name='collective.zamqp',
      version=version,
      description="AMQP consumer and producer integration for Zope2",
      long_description=open("README.rst").read() + "\n" +
                       open("HISTORY.txt").read(),
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
      url='http://github.com/datakurre/collective.zamqp',
      license='ZPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      entry_points={
          'console_scripts': ['publishmsg = collective.zamqp.cli:main']
      },
      extras_require={
          'test': [
              'rabbitfixture',
              'plone.testing',
              'zope.configuration',
              'msgpack-python',
          ],
          'docs': [
              'sphinx',
              'collective.sphinx.includedoc',
              'repoze.sphinx.autointerface',
              'sphinxcontrib-plantuml',
              'sphinxtogithub',
          ]
      },
      install_requires=[
          'setuptools',
          'Zope2',
          'ZODB3',
          'transaction',
          'zope.component',
          'zope.event',
          'zope.processlifetime',
          'grokcore.component',
          'pika == 0.9.5',
          'zope.deprecation',
          'z3c.unconfigure',  # only for sauna.reload-support
          ])
