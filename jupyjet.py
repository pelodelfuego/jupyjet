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



_jet_beg_key = '__jet_beg'
_jet_end_key = '__jet_end'

_jet_beg = '# --- JET BEG --- #'
_jet_end = '# --- JET END --- #'

_jet_split_re = re.compile('# --- JET (BEG|END) --- #')


# PATH
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


def _build_file_path():
    """
    Construct the path to the generated python file.
    """

    mp = _find_file_path()
    return mp['top_dir'] + '/' + mp['file_name'] + '.py'


def _build_notebook_path():
    """
    Construct the path to the existing notebook file.
    """

    mp = _find_file_path()
    return mp['top_dir'] + '/' + mp['file_name'] + '.ipynb'


# FILE
def _load_file_ast():
    """
    Build the ast of the current python file.
    """

    # the ast should be empty if the file does not exist
    mfp = _build_file_path()
    if not os.path.isfile(mfp):
        return {'beg': '',
                'symbols': [],
                'end': ''}

    # if it does, the ast is loaded
    with open(mfp) as source_file:
        # TODO: add end
        # file_code = source_file.read().split(_jet_beg)
        file_code = _jet_split_re.split(source_file.read())[::2]

        # assert len(file_code) == 3

        # if len(file_code) == 1:
            # return {'beg': file_code[0]}

        return {'beg': file_code[0],
                'symbols': ast.parse(file_code[1]).body,
                'end': file_code[2]}


# symbols
def _extract_symbols(file_ast):
    """
    Extract the symbols from the file ast.
    """

    symbols = [(_jet_beg_key, file_ast['beg'] + _jet_beg)]
    symbols += [(symb.name, codegen.to_source(symb) + '\n') for symb in file_ast['symbols']]
    symbols += [(_jet_end_key, file_ast['end'] + _jet_end)]

    return OrderedDict(symbols)


def _save_symbols(symbols, file_path):
    """
    Save the symbols into the file.
    """

    symbols_content = '\n\n'.join(symbols.values())

    print(symbols_content)

    with open(file_path, 'w') as file_file:
        file_file.write(symbols_content)


# DECLARATION symb
def _find_last_decl(In, symb_name):
    for cell in reversed(In):
        decl_ast = [decl for decl in ast.parse(cell).body if hasattr(decl, 'name')]

        if len(decl_ast) > 0:
            for decl in decl_ast:
                if decl.name == symb_name:
                    return codegen.to_source(decl) + '\n'


def _update_decl(In, symbols, decl):
    new_symbols = OrderedDict(symbols)
    new_symbols[decl.__name__] = _find_last_decl(In, decl.__name__)
    return new_symbols


# BEG symb
def _get_beg_symb(In):
    raw_content = In[-1]
    content = raw_content.split('\n')
    content[-1] = _jet_beg

    return (_jet_beg_key, '\n'.join(content))


def _update_beg_symb(symbols_dict, beg_symb):
    if _jet_beg_key in symbols_dict:
        new_symbols = OrderedDict(symbols_dict)
        new_symbols[_jet_beg_key] = beg_symb[1]
        return new_symbols
    else:
        return OrderedDict([beg_symb] + \
                           [(k, v) for k, v in symbols_dict.iteritems()] + \
                           [end_symb])


# POINT OF ENTRY
@magics_class
class JetMagics(Magics):

    @line_magic
    def jet_beg(self, arg_line):
        In = self.shell.user_ns['In']
        new_symbols = _update_beg_symb(_extract_symbols(_load_file_ast()), _get_beg_symb(In))

        _save_symbols(new_symbols, _build_file_path())

    @line_magic
    def jet(self, arg_line):
        In = self.shell.user_ns['In']
        decl_list = [eval(func_name, self.shell.user_global_ns, self.shell.user_ns) for func_name in arg_line.split()]

        new_symbols = reduce(lambda cur_bloc, new_decl: _update_decl(In, cur_bloc, new_decl),
                            decl_list,
                            _extract_symbols(_load_file_ast()))

        _save_symbols(new_symbols, _build_file_path())


def load_ipython_extension(ip):
    ip.register_magics(JetMagics)


