#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='pydotmailer',
    version='0.1',
    description='A reusable python module for driving the dotMailer API',
    author='Mike Austin at Triggered Messaging',
    author_email='mike.austin2012@triggeredmessaging.com',
    url='http://github.com/TriggeredMessaging/pydotmailer/',
    packages=find_packages(exclude=['examples', 'examples.*', "*.tests", "*.tests.*", "tests.*", "tests"]),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    package_dir={'pydotmailer': 'pydotmailer'},
    zip_safe=False,
    tests_require=[]
)
