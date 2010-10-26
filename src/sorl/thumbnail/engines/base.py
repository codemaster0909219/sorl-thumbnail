#coding=utf-8
import re
from abc import ABCMeta, abstractmethod
from sorl.thumbnail.conf import settings
from sorl.thumbnail.helpers import get_module_class, mkhash, dict_serialize
from sorl.thumbnail.helpers import ThumbnailError
from sorl.thumbnail.storage import SuperImage


bgpos_pat = re.compile(r'^(?P<value>\d+)(?P<unit>%|px)$')


class ThumbnailEngineBase(object):
    """
    ABC from Thumbnail engines, methods are static
    """
    __metaclass__ = ABCMeta

    extensions = {
        'JPEG': 'jpg',
        'PNG': 'png',
    }

    @abstractmethod
    def resize(self, image, geometry, options):
        """
        Does the resizing of the image
        """
        raise NotImplemented()

    @abstractmethod
    def colorspace(self, image, geometry, options):
        """
        `Valid colorspaces
        <http://www.graphicsmagick.org/GraphicsMagick.html#details-colorspace>`_.
        Backends need to implement the following::

            RGB, GRAY
        """
        raise NotImplemented()

    @abstractmethod
    def create(self, source, geometry, options, thumbnail):
        """
        Should create the thumbnail and return it as a
        ``sorl.thumbnail.storage.SuperImage`` instance
        """
        raise NotImplemented()

    @abstractmethod
    def write(self, image, options, thumbnail):
        """
        Writes the thumbnail to storage
        """
        raise NotImplemented()

    def get(self, source, geometry, options):
        """
        Should return a ``sorl.thumbnail.storage.SuperImage``
        instance
        """
        name = self.get_filename(source, geometry, options)
        storage_cls = get_module_class(settings.THUMBNAIL_STORAGE)
        thumbnail = SuperImage(name, storage_cls())
        if thumbnail.exists():
            # We could have an overwrite option passed in to
            # ThumbnailEngine.get and delete it if existed but I am
            # that could lead to race conditions. There fore we just
            # return it.
            return thumbnail
        return self.create(source, geometry, options, thumbnail)

    def get_filename(self, source, geometry, options):
        """
        Computes the destination filename.
        """
        key = mkhash(source.name, source.storage_path, geometry,
                     dict_serialize(options))
        # make some subdirs
        path = '%s/%s/%s' % (key[:2], key[2:4], key)
        return '%s%s.%s' % (settings.THUMBNAIL_PREFIX, path,
                            self.extensions[options['format']])


