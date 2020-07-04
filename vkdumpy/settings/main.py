import logging
import os
from os.path import abspath, dirname, join, basename

RAISE_WAITING_EXCEPTION = False  # if false then sleep
WAITING_BETWEEN_REQUESTS = 0.4

ROOT_DIR = dirname(dirname(abspath(__file__)))
VK_SCRIPTS_DIR = join(ROOT_DIR, 'execute-scripts')
VK_EXECUTE_SCRIPTS = {}

for file_name in os.listdir(VK_SCRIPTS_DIR):
    with open(join(VK_SCRIPTS_DIR, file_name), 'r') as file:
        VK_EXECUTE_SCRIPTS.update({
            basename(file_name).replace('.js', ''): file.read().replace('\n', ' ')
        })

VK_API_VERSION = '5.120'

logging.basicConfig(level=logging.INFO)

try:
    from .local import *
except ImportError:
    pass
