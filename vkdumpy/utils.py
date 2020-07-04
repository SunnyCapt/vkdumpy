import logging
from functools import wraps

logger = logging.getLogger(__name__)


def log_start_finish(flag_field_name):
    def inner_1(func):
        @wraps(func)
        def inner_2(*args, **kwargs):
            log_msg = f'calling {func.__qualname__}'
            if len(args) > 0 and getattr(args[0], flag_field_name, None) is not None:
                log_msg += f' [{hash(getattr(args[0], flag_field_name))}]'

            logger.info(f'Started {log_msg}')
            result = func(*args, **kwargs)
            logger.info(f'Finished {log_msg}')

            return result

        return inner_2

    return inner_1
