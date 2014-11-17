# -*- coding: utf-8 -*-

import os
from fabric.api import *
from fabric.colors import *


# def clear_cache(namespace):
#     """Recreate cache"""
#     path_ = os.path.join('cache', namespace)
#     local('rm {}/*'.format(path_))