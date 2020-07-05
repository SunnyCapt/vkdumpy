import logging

from vkdumpy.api import VkApi
from vkdumpy.utils import load_execute_scripts

logger = logging.getLogger(__name__)


def dump_all():
    import json
    logger.info('Start test dump')

    load_execute_scripts()

    api = VkApi(input('Enter vk token: '))
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

    with open('vkdumpy-result.json', 'w') as file:
        file.write(json.dumps(data))

    logger.info('Finish test dump, check vkdumpy-result.json')


if __name__ == '__main__':
    dump_all()
