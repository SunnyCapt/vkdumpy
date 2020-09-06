import json
import logging
from inspect import stack
from json.decoder import JSONDecodeError
from time import sleep, time
from typing import Union, List

import requests
from requests import RequestException
from retry import retry
from vk import API as ApiWrapper
from vk import AuthSession as ApiWrapperAuthSession
from vk.exceptions import VkAPIError

from vkdumpy.exceptions import VkDumpyWaitException, VkDumpyExecuteException, VkDumpyRestApiException
from vkdumpy.settings.main import WAITING_BETWEEN_REQUESTS, RAISE_WAITING_EXCEPTION, VK_API_VERSION, \
    VK_EXECUTE_SCRIPTS, DEBUG
from vkdumpy.utils import log_start_finish, waiting

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

    @retry(tries=4, delay=2)
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
    def generate_getConversations_executor(cls, extended: bool, **kwargs) -> 'VkExecutor':
        kwargs.update({'v': '5.120', 'count': 200})
        code = VK_EXECUTE_SCRIPTS['messages']['getConversations'] \
            .render(
            api_version=VK_API_VERSION,
            kwargs=json.dumps(kwargs, ensure_ascii=False),
            extended=str(extended).lower()
        )

        if DEBUG:
            logger.info(f'Generated code: {code}')

        return cls(code)

    @classmethod
    def generate_getHistory_executor(
            cls,
            peer_id: Union[str, int],
            start_message_id: int,
            offset: int,
            **kwargs
    ) -> 'VkExecutor':
        kwargs.update({'peer_id': peer_id})
        code = VK_EXECUTE_SCRIPTS['messages']['getHistory'] \
            .render(
            start_message_id=start_message_id,
            offset=offset,
            kwargs=json.dumps(kwargs, ensure_ascii=False)
        )

        if DEBUG:
            logger.info(f'Generated code: {code}')

        return cls(code)


class VkRestApi(WaitController):
    def __init__(self, token):
        self.api: ApiWrapper = ApiWrapper(ApiWrapperAuthSession(access_token=token))
        self.hash = hash(token)

    @waiting('messages', 'hash')
    def get_init_long_pool_data(self, **kwargs):
        return self.api.messages.getLongPollServer(need_pts=1, lp_version=3, v=VK_API_VERSION, **kwargs)

    @waiting('messages', 'hash')
    def get_long_poll_history(self, pts=None, **kwargs):
        if pts is None:
            init_info = self.api.messages.getLongPollServer(need_pts=1, lp_version=3, v=VK_API_VERSION, **kwargs)
            pts = init_info['pts']
            logger.info(f'Got pts: {pts}')

        return self.api.messages.getLongPollHistory(pts=pts, v=VK_API_VERSION)


class VKDumpy:
    # todo: run parallel
    def __init__(self, token):
        self._token = token

    @log_start_finish(flag_field_name='_token')
    def get_conversations(self, extended=False) -> List[int]:
        response = VkExecutor.generate_getConversations_executor(extended).execute(self._token)
        result = response['items']

        logger.info(
            f'Getting {"extended " if extended else ""}conversations: {len(result)}/{response["count"]} '
            f'[{stack()[0][3]}][{hash(self._token)}]'
        )

        while len(result) < response['count']:
            response = VkExecutor \
                .generate_getConversations_executor(extended=extended, offset=len(result)) \
                .execute(self._token)
            result += response['items']

            logger.info(
                f'Getting {"extended " if extended else ""}conversations: {len(result)}/{response["count"]} '
                f'[{stack()[0][3]}][{hash(self._token)}]'
            )

        return result

    @log_start_finish(flag_field_name='_token')
    def get_history(self, peer_id: Union[int, str], start_message_id=-1) -> List[dict]:
        response = VkExecutor.generate_getHistory_executor(
            peer_id=peer_id,
            offset=0,
            start_message_id=start_message_id
        ).execute(self._token)
        result = response['items']

        logger.info(
            f'Getting dialog history with {peer_id}: {len(result)}/{response["count"]} '
            f'[{stack()[0][3]}][{hash(self._token)}]'
        )

        while len(result) < response['count'] and result[-1]['id'] > start_message_id:
            response = VkExecutor.generate_getHistory_executor(
                peer_id=peer_id,
                offset=len(result),
                start_message_id=start_message_id
            ).execute(self._token)
            result += response['items']

            logger.info(
                f'Getting dialog history with {peer_id}: {len(result)}/{response["count"]} '
                f'[{stack()[0][3]}][{hash(self._token)}]'
            )

        if start_message_id == -1:
            return result

        for i in range(len(result) - 1, -1, -1):
            if result[i]['id'] >= start_message_id:
                break
            result.pop(i)

        return result

    @log_start_finish(flag_field_name='_token')
    def get_deleted_messages(self) -> List[dict]:
        """
        Returns today deleted messages sorted by date
        """

        vk_resp_api = VkRestApi(self._token)

        min_pts = vk_resp_api.get_init_long_pool_data()['pts']
        results = []
        deleted_msgs = []

        while True:
            logger.info(
                f'Try to find minimal pts for getting deleted messages: now minimal pts is {min_pts} [{stack()[0][3]}][{hash(self._token)}]'
            )
            try:
                lp_history = vk_resp_api.get_long_poll_history(pts=min_pts)
            except Exception as e:
                if isinstance(e, VkAPIError) and e.code == 907:
                    break
                err_msg = f'Can not get_deleted_messages: {e}'
                logger.error(err_msg)
                raise VkDumpyRestApiException(err_msg)

            min_pts -= 1000

            if lp_history.get('messages', {}).get('items', []):
                results.append(lp_history)

        for result in results:
            deleted_msgs += [m for m in result['messages']['items'] if m.get('deleted')]

        logger.info(
            f'Found {len(deleted_msgs)} messages [{stack()[0][3]}][{hash(self._token)}]'
        )

        return sorted(deleted_msgs, key=lambda m: m['date'])
