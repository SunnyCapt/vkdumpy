import logging
from functools import wraps

from vkdumpy.settings.main import VK_EXECUTE_SCRIPTS, VK_SCRIPTS_DIR

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
                    method.name.replace(".js", ""): file.read().replace('\n', ' ')
                })
