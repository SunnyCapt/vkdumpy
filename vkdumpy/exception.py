from requests.exceptions import RequestException


class VkDumpyWaitException(Exception):
    def __init__(self, calling_method_name, time_to_wait):
        self.calling_method_name = calling_method_name
        self.time_to_wait = time_to_wait

    def __str__(self):
        return f'You need to wait {self.time_to_wait} seconds for {self.calling_method_name}'


class VkDumpyRequestException(RequestException):
    pass


class VkDumpyExecuteException(VkDumpyRequestException):
    pass
