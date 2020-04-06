import re
import requests

from inspect import stack
from time import sleep, time
from functools import wraps
from vkdumpy.settings.main import *
from vkdumpy.exception import *


class WaitingMixin:
    def _how_much_to_wait(self, hash_code=''):
        field_name = f'_{self.__class__.__name__}_{stack()[0][3]}' + (f'_{hash_code}' if hash_code else '')
        last_call_time = getattr(self, field_name, None)

        if last_call_time is None:
            setattr(self, field_name, time())
            return timedelta()

        interval = time() - last_call_time
        if interval < WAITING_BETWEEN_REQUESTS:
            if RAISE_WAITING_EXCEPTION:
                raise VkDumpyWaitException(stack()[1][3], interval)
            logger.info(f'Go to sleep [cause is {stack()[1][3]}][hash is {hash}]: {interval} seconds')
            sleep(interval)
            setattr(self, field_name, time())


class VkExecutor(WaitingMixin):
    _api_url = 'https://api.vk.com/method/execute'

    def __init__(self, code):
        self.code = code

    def execute(self, token):
        self._how_much_to_wait(hash(token))

        data = {
            'v': VK_API_VERSION,
            'code': self.code,
            'access_token': token
        }
        try:
            resp = requests.post(
                self._api_url,
                data=data
            ).json()
            return resp['response']
        except RequestException as e:
            logger.error(e)
            raise VkDumpyExecuteException(e)

    @classmethod
    def generate_getDialogs(cls, **kwargs: dict) -> 'VkExecutor':
        code = VK_EXECUTE_SCRIPTS['get_dialogs']
        code = code.replace('\'{{API_VERSION}}\'', VK_API_VERSION)
        code = code.replace('\'{{ARGS}}\'', str(kwargs))
        return cls(code)


if __name__ == '__main__':
    import json
    get_dialogs = VkExecutor.generate_getDialogs(
        v=VK_API_VERSION,
        offset=0,
        count=200
    ).execute
    data = get_dialogs(input('Enter your account token'))
    print(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False))
