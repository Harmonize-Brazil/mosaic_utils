"""
Set operations for validate input and output files or directories.
:Contains:
 is_valid_file,
 is_valid_directory

:Notes:
This module enable verify if input and output files and directories passed to ArgParse arguments are valid. The
code was adapted from https://codereview.stackexchange.com posted for Matthew Rankin.
"""

import os
import string


def is_valid_file(parser, arg):
    if not os.path.isfile(arg):
        parser.error('The file {} does not exist!'.format(arg))
    else:
        # File exists so return the filename
        return arg


def is_valid_directory(parser, arg):
    if not os.path.isdir(arg):
        parser.error('The directory {} does not exist!'.format(arg))
    else:
        # Directory exists so return the directory name
        return arg


def is_valid_namefile(parser,arg):
    if '.tif' not in os.path.basename(arg) and '.TIF' not in os.path.basename(arg):
         parser.error('The file {} does not have a valid extension for a COG file!'.format(arg))
    elif os.path.isdir(os.path.dirname(arg)) != True:
        parser.error('Please, include a valid path to save COG file {}!'.format(arg))                       
    else:
        # File have COG valid extension so return the filename
        return arg