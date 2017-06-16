#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json, urllib3
import os
import ast

import psutil, codegen


import IPython
from IPython.core.magic import (Magics, magics_class, line_magic)
from IPython.core.display import (display, Javascript)
from IPython.lib import kernel as ip_ker
from collections import OrderedDict



_jet_init_key = '__jet_init_block'
_end_of_jet_init = '\n# --- JET INIT END --- #\n\n'


# PATH
def _find_module_path():
    connection_file = os.path.basename(ip_ker.get_connection_file())
    kernel_id = connection_file.split('-', 1)[1].split('.')[0]

    app_dict = IPython.Application.instance().session.__dict__
    pid = app_dict['_trait_values']['pid']

    adress = [a for a in psutil.Process(pid).parent().connections() if a.status == psutil.CONN_LISTEN].pop().laddr
    adress = ':'.join([adress[0], str(adress[1])])

    sessions = json.loads(urllib3.PoolManager().request('GET', 'http://' + adress + '/api/sessions').data)
    ntb_name_list = [sess['notebook']['path'] for sess in sessions if sess['kernel']['id'] == kernel_id]

    assert len(ntb_name_list) == 1
    ntb_name = '.'.join(ntb_name_list[0].split('.')[:-1]).split('/')[-1]

    return {'top_dir': os.getcwd(),'module_name': ntb_name}


def _build_module_path():
    mp = _find_module_path()
    return mp['top_dir'] + '/' + mp['module_name'] + '.py'


def _build_notebook_path():
    mp = _find_module_path()
    return mp['top_dir'] + '/' + mp['module_name'] + '.ipynb'


# FILE
def _load_module_ast():
    mfp = _build_module_path()
    if not os.path.isfile(mfp):
        return {'init': '', 'blocks': []}

    with open(mfp) as source_file:
        module_code = source_file.read().split(_end_of_jet_init)
        if len(module_code) == 1:
            return {'init': module_code[0]}

        return {'init': module_code[0], 'blocks': ast.parse(module_code[1]).body}


# BLOCKS
def _extract_blocks(module_ast):
    blocks = [(_jet_init_key, module_ast['init'] + _end_of_jet_init)]

    if 'blocks' in module_ast:
        blocks += [(block.name, codegen.to_source(block) + '\n') for block in module_ast['blocks']]

    return OrderedDict(blocks)


def _save_blocks(blocks, file_path):
    blocks_str = '\n\n'.join(blocks.values())

    with open(file_path, 'w') as module_file:
        module_file.write(blocks_str)


# DECLARATION BLOCK
def _find_last_decl(In, decl_name):
    for cell in reversed(In):
        decl_ast = [decl for decl in ast.parse(cell).body if hasattr(decl, 'name')]

        if len(decl_ast) > 0:
            for decl in decl_ast:
                if decl.name == decl_name:
                    return codegen.to_source(decl) + '\n'


def _update_decl(In, blocks, decl):
    new_blocks = OrderedDict(blocks)
    new_blocks[decl.__name__] = _find_last_decl(In, decl.__name__)
    return new_blocks


# INIT BLOCK
def _get_init_block(In):
    raw_content = In[-1]
    content = raw_content.split('\n')
    content[-1] = _end_of_jet_init

    return (_jet_init_key, '\n'.join(content))


def _update_init_block(blocks_dict, init_block):
    if _jet_init_key in blocks_dict:
        new_blocks = OrderedDict(blocks_dict)
        new_blocks[_jet_init_key] = init_block[1]
        return new_blocks
    else:
        return OrderedDict([init_block] + [(k, v) for k, v in blocks_dict.iteritems()])


# POINT OF ENTRY
@magics_class
class JetMagics(Magics):

    @line_magic
    def jet_init(self, arg_line):
        In = self.shell.user_ns['In']
        new_blocks = _update_init_block(_extract_blocks(_load_module_ast()), _get_init_block(In))

        _save_blocks(new_blocks, _build_module_path())

    @line_magic
    def jet(self, arg_line):
        In = self.shell.user_ns['In']
        decl_list = [eval(func_name, self.shell.user_global_ns, self.shell.user_ns) for func_name in arg_line.split()]

        new_blocks = reduce(lambda cur_bloc, new_decl: _update_decl(In, cur_bloc, new_decl),
                            decl_list,
                            _extract_blocks(_load_module_ast()))

        _save_blocks(new_blocks, _build_module_path())


def load_ipython_extension(ip):
    ip.register_magics(JetMagics)


