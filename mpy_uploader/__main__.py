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

# ===== main =====

opt_port = None
opt_baud = None

@click.group()
@click.option('--port', '-p', default='COM1', type=click.STRING, help='serial port name (like: COM1, /dev/ttyUSB0)')
@click.option('--baud', '-b', default=115200, type=click.INT, help='serial port baudrate')
def main(port: str, baud: int):
    """Micropython File Uploader"""
    global opt_port, opt_baud
    opt_baud = port
    opt_baud = baud
    print(f'opening serial port: {opt_port}, baud: {str(opt_baud)} ...')

@main.command()
def ls():
    pass

if __name__ == '__main__':
    main()