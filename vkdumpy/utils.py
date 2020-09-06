import logging
import time
from functools import wraps

from jinja2 import Template
from vk.exceptions import VkAPIError

from vkdumpy.settings.main import VK_EXECUTE_SCRIPTS, VK_SCRIPTS_DIR, MAX_WAITING_BETWEEN_REQUESTS

logger = logging.getLogger(__name__)


def log_start_finish(flag_field_name=None):
    def inner_1(func):
        @wraps(func)
        def inner_2(*args, **kwargs):
            log_msg = f'calling {func.__qualname__}'
            if flag_field_name is not None and len(args) > 0 and getattr(args[0], flag_field_name, None) is not None:
                log_msg += f' [{hash(getattr(args[0], flag_field_name))}]'

            logger.info(f'Started {log_msg}')
            result = func(*args, **kwargs)
            logger.info(f'Finished {log_msg}')

            return result

        return inner_2

    return inner_1


@log_start_finish()
def load_execute_scripts():
    for method_part in VK_SCRIPTS_DIR.iterdir():
        if not method_part.is_dir():
            continue
        for method in method_part.iterdir():
            with method.open() as file:
                VK_EXECUTE_SCRIPTS[method.parent.name].update({
                    method.name.replace(".js", "")
                        .replace(".jinja2", ""): Template(file.read().replace('\n', ' '))
                })


def waiting(method_part, flag_name):
    def inner_1(func):
        @wraps(func)
        def inner_2(self, *args, **kwwargs):
            self.wait_if_need(method_part, getattr(self, flag_name))

            try:
                return func(self, *args, **kwwargs)
            except VkAPIError as e:
                if e.code == 6:
                    logger.warning(
                        f'WAITING_BETWEEN_REQUESTS is small, retrying: go to sleep {MAX_WAITING_BETWEEN_REQUESTS} secs'
                    )
                    time.sleep(MAX_WAITING_BETWEEN_REQUESTS)
                else:
                    raise e
            return func(self, *args, **kwwargs)

        return inner_2

    return inner_1
