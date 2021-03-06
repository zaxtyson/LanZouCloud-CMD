from os.path import expanduser, sep
from pickle import load, dump

__all__ = ['config']


class Config:

    def __init__(self):
        self._data = 'user.dat'
        self._config = None

        with open(self._data, 'rb') as c:
            self._config = load(c)

    def _save(self):
        with open(self._data, 'wb') as c:
            dump(self._config, c)

    @property
    def cookie(self):
        return self._config.get('cookie')

    @cookie.setter
    def cookie(self, value):
        self._config['cookie'] = value
        self._save()

    @property
    def save_path(self):
        path = self._config.get('path')
        if not path:
            return expanduser("~") + sep + "Downloads"
        return path

    @save_path.setter
    def save_path(self, value):
        self._config['path'] = value
        self._save()

    @property
    def upload_delay(self):
        return self._config.get('upload_delay')

    @upload_delay.setter
    def upload_delay(self, value):
        self._config['upload_delay'] = value
        self._save()

    @property
    def default_file_pwd(self):
        return self._config.get('default_file_pwd')

    @default_file_pwd.setter
    def default_file_pwd(self, value):
        self._config['default_file_pwd'] = value
        self._save()

    @property
    def default_dir_pwd(self):
        return self._config.get('default_dir_pwd')

    @default_dir_pwd.setter
    def default_dir_pwd(self, value):
        self._config['default_dir_pwd'] = value
        self._save()

    @property
    def max_size(self):
        return self._config.get('max_size')

    @max_size.setter
    def max_size(self, value):
        self._config['max_size'] = value
        self._save()

    @property
    def reader_mode(self):
        return self._config.get('reader_mode')

    @reader_mode.setter
    def reader_mode(self, value: bool):
        self._config['reader_mode'] = value
        self._save()


# 全局配置对象
config = Config()
