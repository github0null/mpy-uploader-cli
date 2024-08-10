#!/usr/bin/python3
# coding=utf-8

import sys
import os
import re
import json
import subprocess
import click
import time
import traceback
import serial
from optparse import OptionParser

# ===== const =====

KEY_CTRL_A = "\u0001" # CTRL-A  -- on a blank line, enter raw REPL mode
KEY_CTRL_B = "\u0002" # CTRL-B  -- on a blank line, enter normal REPL mode
KEY_CTRL_C = "\u0003" # CTRL-C  -- interrupt a running program
KEY_CTRL_D = "\u0004" # CTRL-D  -- on a blank line, do a soft reset of the board
KEY_CTRL_E = "\u0005" # CTRL-E  -- on a blank line, enter paste mode

# ===== vars =====

opt_port = None
opt_baud = None
h_serial = None

# ===== utility func =====

def get_script_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)
    else:
        raise Exception('error !, can not get script root !')

def to_abs_path(repath: str):
    if not os.path.isabs(repath):
        return os.path.normpath(get_script_root() + os.path.sep + repath)
    else:
        return repath

def str2args(line: str) -> list:
    def IsNullOrWhiteSpace(str_):
        return str_ == None or str_.strip() == ''
    argsLi  = []
    inQuote = False
    curArg  = ''
    for char_ in line:
        if char_ == '"' and (len(curArg) == 0 or curArg[-1] != '\\'): # is a "..." start or end
            if inQuote:
                inQuote = False
                if not IsNullOrWhiteSpace(curArg):
                    argsLi.append(curArg)
                curArg = ''
            else:
                inQuote = True
            continue; # skip '"'
        if inQuote: # in "..." region
            curArg += char_
        else: # out "..." region
            if char_.strip() == '':
                if not IsNullOrWhiteSpace(curArg):
                    argsLi.append(curArg)
                curArg = ''
            else:
                curArg += char_
    if not IsNullOrWhiteSpace(curArg):
        argsLi.append(curArg)
    return argsLi

# ===== sub func =====

def repl():
    global opt_port, opt_baud, h_serial
    with serial.Serial(port=opt_port, baudrate=opt_baud, 
                       parity=serial.PARITY_NONE, timeout=0.200) as h_serial:
        startup_backend()
        cliparsers = {}
        cliparsers['ls'] = OptionParser()
        cliparsers['ls'].add_option('-l', action="store_true")
        cliparsers['tree'] = OptionParser()
        cliparsers['cat'] = OptionParser()
        while True:
            usr_input = input('> ').lstrip()
            for func in cliparsers.keys():
                if re.match(f"{func}\\b", usr_input):
                    options, args = cliparsers[func].parse_args(str2args(usr_input))
                    _arg_str = ''
                    _locals = {}
                    for k, value in vars(options).items():
                        _arg_str += k if _arg_str == '' else f',{k}'
                        _locals[k] = value
                    for i in range(1, len(args)):
                        k = 'arg' + str(i)
                        _arg_str += k if _arg_str == '' else f',{k}'
                        _locals[k] = args[i]
                    eval(f'_{func}({_arg_str})', globals(), _locals)

def startup_backend():
    pass

# ===== commands =====

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--port', '-p', default='COM1', type=click.STRING, help='serial port name (like: COM1, /dev/ttyUSB0)')
@click.option('--baud', '-b', default=115200, type=click.INT, help='serial port baudrate')
def main(ctx, port: str, baud: int):
    """Micropython File Uploader"""
    global opt_port, opt_baud, h_serial
    opt_baud = port
    opt_baud = baud
    if ctx.invoked_subcommand is None:
        repl()
    else:
        click.echo(f'opening serial port: {opt_port}, baud: {str(opt_baud)} ...')
        h_serial = serial.Serial(port=opt_port, baudrate=opt_baud,
                                 parity=serial.PARITY_NONE, timeout=0.200)
        startup_backend()

@main.command()
@click.option('-l', 'uselonglist', is_flag=True, help='use a long listing format')
@click.argument('path', type=click.STRING)
def ls(uselonglist, path):
    _ls(uselonglist, path)
def _ls(uselonglist, path):
    #click.echo(f'ls {uselonglist} {path}')
    pass

if __name__ == '__main__':
    main()