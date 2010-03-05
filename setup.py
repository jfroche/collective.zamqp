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
      extras_require=dict(
            docs=['z3c.recipe.sphinxdoc',
                  'collective.sphinx.includechangelog',
                  'repoze.sphinx.autointerface',
                  'collective.sphinx.includedoc']),
      install_requires=[
          'setuptools',
          'carrot',
          'grokcore.component',
          'z3c.autoinclude'])
