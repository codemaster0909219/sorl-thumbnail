from abc import ABCMeta, abstractmethod, abstractproperty
from sorl.thumbnail.conf import settings
from sorl.thumbnail.storage import ImageFile
from sorl.thumbnail.storage import serialize_image_file, deserialize_image_file
from sorl.thumbnail.helpers import get_module_class, tokey
from sorl.thumbnail.helpers import serialize, deserialize
from sorl.thumbnail.parsers import parse_geometry



def add_prefix(key, identity='image'):
    """
    Adds prefixes to the key
    """
    return '||'.join([settings.THUMBNAIL_KEY_PREFIX, identity, key])


class ThumbnailBackendBase(object):
    __metaclass__ = ABCMeta

    default_options = {
        'format': settings.THUMBNAIL_FORMAT,
        'quality': settings.THUMBNAIL_QUALITY,
        'colorspace': settings.THUMBNAIL_COLORSPACE,
        'upscale': settings.THUMBNAIL_UPSCALE,
        'crop': False,
    }

    extensions = {
        'JPEG': 'jpg',
        'PNG': 'png',
    }

    def __init__(self, engine=None, storage=None):
        if engine is None:
            engine = get_module_class(settings.THUMBNAIL_ENGINE)()
        if storage is None:
            storage = get_module_class(settings.THUMBNAIL_STORAGE)()
        self.engine = engine
        self.storage = storage

    def get_thumbnail(self, file_, geometry_string, **options):
        source = ImageFile(file_)
        for key, value in self.default_options.iteritems():
            options.setdefault(key, value)

        name = self._get_thumbnail_filename(source, geometry_string, options)
        thumbnail = ImageFile(name, self.storage)
        if not self.store_get(thumbnail):
            if not thumbnail.exists():
                self._create_thumbnail(source, geometry_string, options,
                                       thumbnail)
            # If the thumbnail exists we don't do anything, the other option is
            # to delete and write but this could lead to race conditions so I
            # will just leave that out for now.
            self.store_set(thumbnail, source)
        return thumbnail

    def _create_thumbnail(self, source, geometry_string, options, thumbnail):
        image = self.engine.get_image(source)
        image_size = self.engine.get_image_size(image)
        geometry = parse_geometry(geometry_string, image_size)
        thumbnail_image = self.engine.create(image, geometry, options)
        self.engine.write(thumbnail_image, options, thumbnail)
        # its much cheaper to set the size here since we probably have the
        # image in memory
        thumbnail.size = self.engine.get_image_size(thumbnail_image)

    def _get_thumbnail_filename(self, source, geometry_string, options):
        """
        Computes the destination filename.
        """
        key = tokey(source.key, geometry_string, serialize(options))
        # make some subdirs
        path = '%s/%s/%s' % (key[:2], key[2:4], key)
        return '%s%s.%s' % (settings.THUMBNAIL_PREFIX, path,
                            self.extensions[options['format']])

    def store_get(self, image_file):
        """
        Gets the ``image_file`` from store. Returns ``None`` if not found in
        store.
        """
        return self._store_get(image_file.key)

    def store_set(self, image_file, source=None):
        """
        Updates store for the `image_file`. Makes sure the `image_file` has a
        size set.
        """
        if source is not None:
            # Update the list of thumbnails for source. Storage is not saved,
            # we assume current storage when unpacking.
            thumbnails = self._store_get(source.key, identity='thumbnails') or []
            thumbnails = set(thumbnails)
            thumbnails.add(image_file.name)
            self._store_set(source.key, list(thumbnails), identity='thumbnails')
        # now set store for the image_file and make sure it's got a size
        if image_file.size is None:
            if hasattr(image_file.storage, 'image_size'):
                image_file.size = image_file.storage.image_size(self.name)
            else:
                # This is the worst case scenario
                image = self.engine.get_image(image_file)
                image_file.size = self.engine.get_image_size(image)
        self._store_set(image_file.key, image_file)
        return image_file

    def store_delete(self, image_file, delete_thumbnails=True):
        """
        Deletes the store referense to the image_file and deletes store
        references to thumbnails as well as thumbnail files if
        `delete_thumbnails` is set to `True`.
        """
        if delete_thumbnails:
            self.store_delete_thumbnails(image_file)
        self._store_delete(image_file.key)

    def store_delete_thumbnails(self, image_file, storage=None):
        """
        Deletes store references to thumbnails as well as thumbnail
        image_files.
        """
        if storage is not None:
            storage = self.storage
        thumbnails = self._store_get(image_file.key, identity='thumbnails')
        if thumbnails:
            # Delete all thumbnail keys from store and delete the
            # ImageFiles. Storage is assumed to be the same
            for name in thumbnails:
                thumbnail = ImageFile(name, storage)
                self._store_delete(thumbnail.key)
                thumbnail.delete()
        # Delete the thumbnails key from store
        self._store_delete(image_file.key, identity='thumbnails')

    def _store_get(self, key, identity='image'):
        """
        Deserializing, prefix wrapper for ThumbnailBackendBase._store_get_raw
        """
        value = self._store_get_raw(add_prefix(key, identity))
        if value is None:
            return None
        if identity == 'image':
            return deserialize_image_file(value)
        return deserialize(value)

    def _store_set(self, key, value, identity='image'):
        """
        Serializing, prefix wrapper for ThumbnailBackendBase._store_set_raw
        """
        if identity == 'image':
            s = serialize_image_file(value)
        else:
            s = serialize(value)
        self._store_set_raw(add_prefix(key, identity), s)

    def _store_delete(self, key, identity='image'):
        """
        Prefix wrapper for ThumbnailBackendBase._store_delete_raw
        """
        self._store_delete_raw(add_prefix(key, identity))

    #
    # Methods which backends need to implement
    #
    @abstractmethod
    def _store_get_raw(self, key):
        """
        Gets the value from keystore, returns `None` if not found.
        """
        raise NotImplemented()

    @abstractmethod
    def _store_set_raw(self, key, value):
        """
        Sets value associated to key. Key is expected to be shorter than 200
        chars. Value is a `basestring` with an unknown length, length depends
        on how many *different* thumbnails you have created from a source.
        """
        raise NotImplemented()

    @abstractmethod
    def _store_delete_raw(self, key):
        """
        Deletes the key, value. Silent failure for missing key.
        """
        raise NotImplemented()

    @abstractmethod
    def _store_delete_orphans(self):
        """
        Removes all store referneces image_files that do not exist and their
        referenced thumbnail keys *and* image_fields. This can be used in
        *emergency* situations.
        """
        raise NotImplemented()

