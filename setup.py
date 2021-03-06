1# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

name = 'usermanagement'
version = '0.1'
readme = open('README.txt').read()
history = "" 


install_requires = [
    'shunting',
    'cromlech.jwt',
    'cromlech.sqlalchemy',
    'dolmen.api_engine',
    'zope.interface',
    'zope.schema',
    ]

db2_requires = [
   'ukh.ibmdbsa',
   ]

tests_require = [
    'webtest',
    ]


setup(name=name,
      version=version,
      description=("Usermanagement"),
      long_description=readme + '\n\n' + history,
      keywords='API',
      author='Souheil Chelfouh',
      author_email='sch@treegital.fr',
      url='http://www.treegital.fr/',
      license='Proprietary',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['ez_setup']),
      namespace_packages=[],
      include_package_data=True,
      zip_safe=False,
      tests_require=tests_require,
      install_requires=install_requires,
      extras_require={
        'test': tests_require,
        'db2': db2_requires,
        },
      classifiers=[
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          ],
      )
