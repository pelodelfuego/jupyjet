# jupy-jet


'''
c.TerminalIPythonApp.extensions = [
    'my_ext',
]
c.InteractiveShellApp.extensions = [
    'my_ext',
]
''


'''
import jupyjet

import line_profiler

import memory_profiler

def load_ipython_extension(ip):
    ip.register_magics(jupyjet.JetMagics)
    ip.register_magics(line_profiler.LineProfilerMagics)
    ip.register_magics(memory_profiler.MemoryProfilerMagics)
'''

