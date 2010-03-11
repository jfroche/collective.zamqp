from setuptools import setup, find_packages
import os

version = '0.2dev'

setup(name='affinitic.zamqp',
      version=version,
      description="AMQP Consumer and publisher in Zope",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Jean-Francois Roche',
      author_email='jfroche@affinitic.be',
      url='http://hg.affinitic.be/affinitic.zamqp',
      license='GPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['affinitic'],
      include_package_data=True,
      zip_safe=False,
      entry_points={
            'console_scripts': [
                  'publishmsg = affinitic.zamqp.publisher:main']},
      extras_require=dict(
            test=['zope.testing', 'Zope2'],
            docs=['z3c.recipe.sphinxdoc',
                  'collective.sphinx.includechangelog',
                  'repoze.sphinx.autointerface',
                  'collective.sphinx.includedoc']),
      install_requires=[
          'setuptools',
          'carrot',
          'transaction',
          'five.dbevent',
          'zope.component',
          'uuid', # python < 2.5
          #'Zope2', # python = 2.6
          'grokcore.component',
          'z3c.autoinclude'])
