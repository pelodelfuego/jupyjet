#!/usr/bin/env python
# -*- coding: utf-8 -*-


from distutils.core import setup

long_description = """\
Jupyjet is a IPyhton notebook extention which allow you to dynamically genrate python files from cells.

Code portions registered with %jet or %jet-init magics will be written and updated into a python file.
This approach make possible to easily separate a notebook into several notebooks and bind them.
"""

setup(
    name='jupy-jet',
    url='https://github.com/pelodelfuego/jupy-jet',
    author='Clément CREPY',
    author_email='clement.crepy@gmail.com',
    version='0.1.0',
    py_modules=['jupyjet'],
    license='MIT',
    description='jupyter extention to generate python modules',
    long_description=long_description,
    keywords = ['jupyter', 'notebook', 'module', 'jupyjet'],
    install_required = ['IPython>=0.13', 'codegen==1.0'],
)


