#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup

long_description = """\
Jupyjet is a IPyhton notebook extention which allows you to dynamically genrates python file / module from a notebook.

Code portions registered with %jet or %jet-init magics will be written and updated into a python file.
This approach make possible to easily separate a notebook into several notebooks and bind them.
"""

setup(
    name='jupyjet',
    url='https://github.com/pelodelfuego/jupyjet',
    author='Clément CREPY',
    author_email='clement.crepy@gmail.com',
    version='0.2.3',
    py_modules=['jupyjet'],
    license='MIT',
    description='jupyter extention to generate python modules',
    long_description=long_description,
    keywords = ['jupyter', 'notebook', 'module', 'jupyjet'],
    install_requires = ['IPython>=0.13',
                        'codegen>=1.0',
                        'psutil>=5.1.3',
                        'urllib3>=1.9.1'],
)


