from vk import API
from abc import ABC, abstractmethod
from vkdumpy.settings.main import *


class VkPartMixin(ABC):
    api: API

    @abstractmethod
    def __check(self):
        pass


class Account(VkPartMixin):
    __LAST_CALL_TIME = int(time.time())

    def __new__(cls, *arg, **args):
        if cls is Account:
            return None
        return object.__new__(cls)

    def get_name(self, vk_id="", need_full_info=False):
        self.__check()
        vk_id = str(vk_id)
        if vk_id.startswith("-"):
            resp = self.api.groups.getById(group_id=str(vk_id)[1:], v=5.1)
            if need_full_info:
                return resp
            else:
                return resp['name']
        else:
            if vk_id:
                resp = self.api.users.get(user_ids=vk_id, v=5.100)[0]
            else:
                resp = self.api.users.get(v=5.100)[0]
            if need_full_info:
                return resp
            else:
                return "%s %s" % (resp['first_name'], resp['last_name'])

    def __check(self):
        past_time = int(time.time()) - self.__LAST_CALL_TIME
        if past_time < PAUSE_TIME: time.sleep(PAUSE_TIME - past_time)


class Messages(VkPartMixin):
    __LAST_CALL_TIME = int(time.time())

    def __new__(cls, *arg, **args):
        if cls is Messages:
            return None
        return object.__new__(cls)

    def get_dialogs(self, page=0, count=200):
        self.__check()
        return self.api.messages.getDialogs(offset=count * page, count=count, v=5.0)

    def get_peers(self, page=0, count=15):
        dialogs = self.get_dialogs(page, count)["items"]
        peers = []
        date_hash = 0
        for peer in dialogs:
            if "chat_id" in peer.keys():
                peers.append(2000000000 + peer['chat_id'])
            else:
                peers.append(peer['user_id'])
            date_hash += peer["date"]
        return {"items": peers, "hash": date_hash}

    def get_messages(self, vk_id, page, count=15):
        self.__check()
        return self.api.messages.getHistory(offset=count * page, count=count, peer_id=vk_id, v=5.38)['items']

    def get_message_by_id(self, mid):
        self.__check()
        return self.api.messages.getById(message_ids=str(mid), v=5.103)

    def long_pool(self):
        self.__check()
        return self.api.messages.getLongPollServer(need_pts=1, lp_version=3, v=5.65)
        return {
            'url': 'https://%s?act=a_check&key=%s&wait=25&mode=10&version=3' %
                   (server['server'], server['key']),
            'tss': '&ts=%d' % server['ts']
        }

    def __check(self):
        past_time = int(time.time()) - self.__LAST_CALL_TIME
        if past_time < PAUSE_TIME: time.sleep(PAUSE_TIME - past_time)


class Media(VkPartMixin):
    __LAST_CALL_TIME = int(time.time())

    def __new__(cls, *arg, **args):
        if cls is Media:
            return None
        return object.__new__(cls)

    def get_max_size_photo(self, attachment):
        # self.__check()
        old_size = -1
        max_size = -1
        if 'photo' in attachment.keys():
            photo = attachment['photo']
        else:
            photo = attachment
        for key in photo.keys():
            if 'photo' in key:
                new_size = int(key.split('_')[1])
                if new_size > old_size:
                    max_size = key
                    old_size = new_size
        if max_size:
            return photo[max_size]
        else:
            raise AttributeError("It isnt photo attachment")

    def get_posts(self, owner_id, page, count=15):
        self.__check()
        return self.api.wall.get(owner_id=owner_id, count=count, offset=count * page, v=5.92)

    def __check(self):
        past_time = int(time.time()) - self.__LAST_CALL_TIME
        if past_time < PAUSE_TIME: time.sleep(PAUSE_TIME - past_time)

    # dont work
    # def getVideo(self, raw_video):
    #     raw_video = raw_video['video']
    #     url = 'https://api.vk.com/method/video.get?videos=%d_%d_%s&access_token=%s&v=5.60' % (
    #         raw_video['owner_id'], raw_video['id'], raw_video['access_key'], self.token)
    #     session = requests.Session()
    #     session.headers.update({'User-Agent': 'VKAndroidApp/4.12-1118'})
    #     video = session.get(url).json()["response"]['items'][0]
    #     return {'player': video['player'], 'photo': self.getMaxSizePhoto(raw_video)}


class VK(Account, Messages, Media):
    class info:
        def __init__(self, id=0, name="", creation_time=0, login="", password=""):
            self.id = id
            self.name = name
            self.creation_time = creation_time
            self.login = login
            self.password = password

    def __init__(self, token="", login="", password=""):
        if token:
            self.token = token
            self.api = self._get_api(token)
        elif login and password:
            self.token = self._get_token(login, password)
            self.api = self._get_api(self.token)
        else:
            raise AttributeError("set token or login&password")
        self.info = VK.info(id=self.get_name(need_full_info=True)['id'],
                            name=self.get_name(),
                            creation_time=int(time.time()),
                            login=login,
                            password=password)

        # self.__dict__.update({'id': id, 'token': token, 'api': api})
        # self.messages = Messages(self.__dict__)
        # self.wall = Wall(self.__dict__)
        # self.media = Media(self.__dict__)

    def _get_token(self, login, password):
        if login.startswith("8"): login = '+7' + login[1:]
        try:
            session = vk.AuthSession('2685278', login, password, scope='2097151')
            return session.access_token
        except VkAPIError as e:
            raise VkAPIError("cannt login: " + e.message)

    def _get_api(self, token):
        try:
            return vk.API(vk.AuthSession(access_token=token))
        except VkAPIError as e:
            raise VkAPIError("cannt login: " + e.message)

    def __str__(self):
        return "%s\nid:   %s\nname: %s\n%s" % ("=" * 20, str(self.info["id"]), self.info["name"], "=" * 20)


if __name__ == '__main__':
    vk = VK(login=config.vk.login, password=config.vk.password)
    print(vk)
