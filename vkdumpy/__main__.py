import logging
import sys

from vkdumpy.api import VKDumpy
from vkdumpy.utils import load_execute_scripts

logger = logging.getLogger(__name__)


def dump_all():
    import json
    logger.info('Start test dump_all')

    load_execute_scripts()

    api = VKDumpy(input('Enter vk token: '))
    conversations = api.get_conversations()
    messages = {}

    for peer_id in conversations:
        messages.update({
            peer_id: api.get_history(peer_id=peer_id)
        })

    data = {
        'conversations': conversations,
        'messages': messages
    }

    with open('dump-all.vkdumpy-result.json', 'w') as file:
        file.write(json.dumps(data))

    logger.info('Finish test dump, check dump-all.vkdumpy-result.json')


def get_deleted_messages():
    import json
    logger.info('Start test get_deleted')

    load_execute_scripts()

    api = VKDumpy(input('Enter vk token: '))
    deleted_messages = api.get_deleted_messages()

    data = {
        'deleted_messages': deleted_messages,
    }

    with open('deleted-messages.vkdumpy-result.json', 'w') as file:
        file.write(json.dumps(data))

    logger.info('Finish test dump, check deleted-messages.vkdumpy-result.json')


def help_():
    print(
        'lib: vkdumpy\n'
        'author: SunnyCapt\n'
        '\ncommand pattern: `python -m vkdumpy [dump-all|get-deleted-messages|help]`\n'
        'args:\n'
        '\t* dump-all - get all conversations and messages and write to file\n'
        '\t* get-deleted-messages - get all deleted messages today and write to file\n'
        '\t* help - show this text\n'
    )


if __name__ == '__main__':
    switch = {
        'dump-all': dump_all,
        'get-deleted-messages': get_deleted_messages
    }
    switch.setdefault('help', help_)

    switch[sys.argv[1] if len(sys.argv) > 1 else 'help']()
