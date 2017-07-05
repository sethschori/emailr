__author__ = 'Seth Schori'

from setuptools import setup

setup(
    name='emailr',
    packages=['emailr'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)