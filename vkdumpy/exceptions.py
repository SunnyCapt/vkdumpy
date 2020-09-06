from requests.exceptions import RequestException


class VkDumpyException(Exception):
    pass


class VkDumpyWaitException(VkDumpyException):
    def __init__(self, method_part, hash_code, time_to_wait):
        self.method_part = method_part
        self.hash_code = hash_code
        self.time_to_wait = time_to_wait

    def __str__(self):
        return f'You need to wait {self.time_to_wait} seconds for {self.method_part} [{self.hash_code}]'


class VkDumpyRequestException(RequestException, VkDumpyException):
    pass


class VkDumpyExecuteException(VkDumpyRequestException):
    pass


class VkDumpyRestApiException(VkDumpyRequestException):
    pass


class VkDumpyConfigException(VkDumpyException):
    pass
