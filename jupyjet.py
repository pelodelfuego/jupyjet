#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json, requests
import os, re

import ast

from collections import OrderedDict
from functools import reduce

import psutil, codegen

import IPython
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.display import display, Javascript
from IPython.lib import kernel as ip_ker



_jet_beg = '\n# --- JET BEG --- #\n\n'
_jet_end = '\n# --- JET END --- #\n\n'

_jet_split_re = re.compile(r'\n# --- JET (BEG|END) --- #\n\n')


# NOTEBOOK PATH
def _find_file_path():
    """
    Find the local path to the current notebook.
    """

    # fetch into the socket file to find the kernel id
    connection_file = os.path.basename(ip_ker.get_connection_file())
    kernel_id = connection_file.split('-', 1)[1].split('.')[0]

    # from the kernel id, retrieve the PID of the kernel
    app_dict = IPython.Application.instance().session.__dict__
    pid = app_dict['_trait_values']['pid']

    # from the pid, retrive the running port on the local machine
    address = [a for a in psutil.Process(pid).parent().connections() if a.status == psutil.CONN_LISTEN].pop().laddr
    address = ':'.join([address[0], str(address[1])])

    # build the url of the client
    url = 'http://' + address + '/api/sessions'
    url = url.replace('http://::1', 'http://localhost')

    # fetch the current session of the client
    sessions = requests.get(url).json()
    ntb_name_list = [sess['notebook']['path'] for sess in sessions if sess['kernel']['id'] == kernel_id]

    assert len(ntb_name_list) == 1
    ntb_name = '.'.join(ntb_name_list[0].split('.')[:-1]).split('/')[-1]

    return {'top_dir': os.getcwd(),'file_name': ntb_name}


def _build_py_fp():
    """
    Construct the path to the generated python file.
    """

    mp = _find_file_path()
    return mp['top_dir'] + '/' + mp['file_name'] + '.py'


def _build_ntb_fp():
    """
    Construct the path to the existing notebook file.
    """

    mp = _find_file_path()
    return mp['top_dir'] + '/' + mp['file_name'] + '.ipynb'


# JET CODE and JET FILE
def _load_jet_code():
    """
    Load the python file into jet_code format.

        jet_code is a dict:
            beg => content of begining (str)
            body => declaration to save (OrderedDict)
                symbol name => declaration
                symbol name => declaration
            beg => content of end (str)


    """

    # the ast should be empty if the file does not exist
    py_fp = _build_py_fp()
    if not os.path.isfile(py_fp):
        return {'beg': '',
                'body': OrderedDict(),
                'end': ''}

    # if it does, the ast is loaded
    with open(py_fp) as py_f:
        file_code = _jet_split_re.split(py_f.read())[::2]

        assert len(file_code) == 3, 'the jet file is not in the good format'

        body_ast = ast.parse(file_code[1]).body

        body_symb = OrderedDict()
        for node in body_ast:
            if hasattr(node, 'name'):
                body_symb[node.name] = node

        return {'beg': file_code[0],
                'body': body_symb,
                'end': file_code[2]}


def _save_jet_file(jet_code):
    """
    Save the jet_code into a the jet file.
    """

    # generate the code for the symbols
    body_str = '\n'.join([codegen.to_source(symb)+'\n\n' for symb in jet_code['body'].values()])

    # concat eveything
    jet_code_str = jet_code['beg'] + \
                  _jet_beg + \
                  body_str + \
                  _jet_end + \
                  jet_code['end']

    # write into the file
    py_fp = _build_py_fp()
    with open(py_fp, 'w') as py_file:
        py_file.write(jet_code_str)

# CELL and SYMBOLS
def _find_last_decl(In, symb_name):
    """
    Iter through execution flow backward to find the last existing delaration.
    """

    for cell in reversed(In):
        # select only function and classes
        decl_ast = [decl for decl in ast.parse(cell).body if hasattr(decl, 'name')]

        # retrieve the last
        for decl in reversed(decl_ast):
            if decl.name == symb_name:
                return decl

    return None


def _fetch_current_cell(In):
    body = In[-1]
    if len(body.split('\n')) == 1:
        return ''
    else:
        # remove the last line
        return body[:body.rfind('\n')]



# POINT OF ENTRY
@magics_class
class JetMagics(Magics):

    @line_magic
    def jet_beg(self, arg_line):
        In = self.shell.user_ns['In']
        jet_code = _load_jet_code()

        jet_code['beg'] = _fetch_current_cell(In)

        _save_jet_file(jet_code)


    @line_magic
    def jet_end(self, arg_line):

        In = self.shell.user_ns['In']
        jet_code = _load_jet_code()

        jet_code['end'] = _fetch_current_cell(In)

        _save_jet_file(jet_code)


    @line_magic
    def jet(self, arg_line):
        In = self.shell.user_ns['In']
        update_list = [name for name in arg_line.split()]

        jet_code = _load_jet_code()

        for name in update_list:
            decl = _find_last_decl(In, name)
            assert decl, 'the symbol "{}" is not defined'.format(name)

            jet_code['body'][name] = decl

        _save_jet_file(jet_code)

def load_ipython_extension(ip):
    ip.register_magics(JetMagics)


