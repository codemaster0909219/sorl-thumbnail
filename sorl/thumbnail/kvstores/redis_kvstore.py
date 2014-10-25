import redis
from sorl.thumbnail.kvstores.base import KVStoreBase
from sorl.thumbnail.conf import settings


class KVStore(KVStoreBase):
    def __init__(self, *args, **kwargs):
        super(KVStore, self).__init__(*args, **kwargs)

        if hasattr(settings, 'THUMBNAIL_REDIS_URL'):
            self.connection = redis.from_url(settings.THUMBNAIL_REDIS_URL)
        else:
            self.connection = redis.Redis(
                host=settings.THUMBNAIL_REDIS_HOST,
                port=settings.THUMBNAIL_REDIS_PORT,
                db=settings.THUMBNAIL_REDIS_DB,
                password=settings.THUMBNAIL_REDIS_PASSWORD,
                unix_socket_path=settings.THUMBNAIL_REDIS_UNIX_SOCKET_PATH,
            )

    def _get_raw(self, key):
        return self.connection.get(key)

    def _set_raw(self, key, value):
        return self.connection.set(key, value)

    def _delete_raw(self, *keys):
        return self.connection.delete(*keys)

    def _find_keys_raw(self, prefix):
        pattern = prefix + '*'
        return list(map(lambda key: key.decode('utf-8'),
                        self.connection.keys(pattern=pattern)))
