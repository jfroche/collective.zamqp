from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='affinitic.zamqp',
      version=version,
      description="AMQP Consumer and publisher in Zope",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='',
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
          'Zope2',
          'grokcore.component',
          'z3c.autoinclude'])
