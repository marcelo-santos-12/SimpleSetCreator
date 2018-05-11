# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import os
import tempfile

def get_random_file_name(extension="png"):
    random_name = tempfile.NamedTemporaryFile(prefix="", \
            suffix=".{}".format(extension), dir=".").name
    random_name = os.path.split(random_name)[-1]
    return random_name


def check_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
