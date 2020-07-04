import logging
from inspect import stack
from json.decoder import JSONDecodeError
from time import sleep, time
from typing import Union

import requests
from requests import RequestException

from vkdumpy.exceptions import VkDumpyWaitException, VkDumpyExecuteException
from vkdumpy.settings.main import WAITING_BETWEEN_REQUESTS, RAISE_WAITING_EXCEPTION, VK_API_VERSION, VK_EXECUTE_SCRIPTS
from vkdumpy.utils import log_start_finish

logger = logging.getLogger(__name__)


class WaitController:
    _call_time_store = {}  # todo: thread-safe

    @classmethod
    def wait_if_need(cls, method_part: str, hash_code: Union[int, str]):
        field_name = f'_{method_part}_{hash_code}_last_call_time'
        last_call_time = WaitController._call_time_store.get(field_name, None)

        if last_call_time is None:
            WaitController._call_time_store.update({field_name: time()})
            return

        interval = time() - last_call_time

        if interval >= WAITING_BETWEEN_REQUESTS:
            return

        if RAISE_WAITING_EXCEPTION:
            raise VkDumpyWaitException(method_part, hash_code, interval)

        logger.info(f'Go to sleep [{method_part}][{hash_code}]: {interval} seconds')
        sleep(interval)
        logger.info(f'Finish sleeping [{method_part}][{hash_code}]: {interval} seconds')

        WaitController._call_time_store.update({field_name: time()})


class VkExecutor(WaitController):
    _api_url = 'https://api.vk.com/method/execute'

    def __init__(self, code: str):
        self.code = code

    def execute(self, token: str):
        hash_code = hash(token)
        self.wait_if_need('execute', hash_code)

        request_data = {
            'v': VK_API_VERSION,
            'code': self.code,
            'access_token': token
        }

        resp = None

        try:
            resp = requests.post(
                self._api_url,
                data=request_data
            )
            resp_json = resp.json()
            return resp_json['response']
        except (RequestException, KeyError, JSONDecodeError) as e:
            error_msg = f'{e.__class__.__name__}: {e} [{hash_code}]'
            if resp is not None:
                error_msg += f' | response content: {resp.content}'
            logger.error(error_msg)
            raise VkDumpyExecuteException(error_msg)

    @classmethod
    def generate_getConversations_executor(cls, **kwargs) -> 'VkExecutor':
        kwargs.update({'v': '5.120', 'count': 200})
        code = VK_EXECUTE_SCRIPTS['get_dialogs'] \
            .replace('{{API_VERSION}}', VK_API_VERSION) \
            .replace('\'{{KwARGS}}\'', str(kwargs))
        return cls(code)


class VkApi:
    # todo: run parallel
    def __init__(self, token):
        self._token = token

    @log_start_finish('_token')
    def get_conversations(self):
        response = VkExecutor.generate_getConversations_executor().execute(self._token)
        result = response['items']

        logger.info(
            f'Getting conversations: {len(result)}/{response["count"]} '
            f'[{stack()[0][3]}][{hash(self._token)}]'
        )

        while len(result) < response['count']:
            response = VkExecutor \
                .generate_getConversations_executor(offset=len(result)) \
                .execute(self._token)
            result += response['items']

            logger.info(
                f'Getting conversations: {len(result)}/{response["count"]} '
                f'[{stack()[0][3]}][{hash(self._token)}]'
            )

        return result


if __name__ == '__main__':
    import json

    api = VkApi(input('Enter vk token: '))
    data = api.get_conversations()
    print(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False))
