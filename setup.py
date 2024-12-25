#!/usr/bin/env python3

from setuptools import setup, find_packages

import pathlib

HERE = pathlib.Path(__file__).parent


def read(path):
    return (HERE / path).read_text("utf-8").strip()


install_requires = [
    'netunnel>=1.0.13',
    'jwthenticator>=1.6.3',
    'YURL>=1.0.0'
]

setup(
    name="netunnel-jwthenticator",
    version='1.0.3',
    description='JWThenticator plugin for NETunnel',
    long_description="\n\n".join((read("README.md"), read("CHANGES.md"))),
    long_description_content_type='text/markdown',
    author='Claroty Open Source',
    author_email='opensource@claroty.com',
    maintainer='Claroty Open Source',
    maintainer_email='opensource@claroty.com',
    url='https://github.com/claroty/netunnel-jwthenticator',
    license="Apache 2",
    packages=find_packages(exclude=('*test*',)),
    install_requires=install_requires,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
