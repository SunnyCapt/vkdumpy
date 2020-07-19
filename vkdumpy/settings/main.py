import logging
import os
import sysconfig
from collections import defaultdict
from pathlib import Path
from typing import Dict
import pkg_resources
from jinja2 import Template

from vkdumpy.exceptions import VkDumpyConfigException

RAISE_WAITING_EXCEPTION: bool = os.environ.get('VKDUMPY_RAISE_WAITING_EXCEPTION', 'false') \
                                    .casefold().strip() == 'true'  # if false then sleep

_waiting = os.environ.get(
    'VKDUMPY_WAITING_BETWEEN_REQUESTS',
    '0.4'
).casefold().strip()
assert _waiting.isdecimal() or _waiting.replace('.', '').isdecimal() \
       and _waiting.count('.') < 2 and _waiting.index('.') != len(_waiting) - 1, \
    VkDumpyConfigException('VKDUMPY_WAITING_BETWEEN_REQUESTS must be float')

WAITING_BETWEEN_REQUESTS: float = float(_waiting)
del _waiting

# if vkdumpy use as python lib
if 'vkdumpy' in {pkg.key for pkg in pkg_resources.working_set}:
    BASE_DIR = sysconfig.get_paths()['purelib']
else:
    BASE_DIR = Path(os.path.abspath(__file__)).parent.parent.parent

BASE_DIR: Path = BASE_DIR.joinpath('vkdumpy')

VK_SCRIPTS_DIR: Path = BASE_DIR.joinpath('execute-scripts')
VK_EXECUTE_SCRIPTS: Dict[str, Dict[str, Template]] = defaultdict(dict)

VK_API_VERSION: str = '5.120'

DEBUG = True

logging.basicConfig(level=logging.INFO)
