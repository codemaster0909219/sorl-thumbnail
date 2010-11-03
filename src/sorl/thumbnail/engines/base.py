#coding=utf-8
from abc import ABCMeta, abstractmethod
from sorl.thumbnail.helpers import toint
from sorl.thumbnail.parsers import parse_crop


class EngineBase(object):
    """
    ABC from Thumbnail engines, methods are static
    """
    __metaclass__ = ABCMeta

    def create(self, image, geometry, options):
        """
        Processing conductor, returns the thumbnail as a backend image object
        """
        image = self.colorspace(image, geometry, options)
        image = self.scale(image, geometry, options)
        image = self.crop(image, geometry, options)
        return image

    def colorspace(self, image, geometry, options):
        """
        Wrapper for ``_colorspace``
        """
        colorspace = options['colorspace']
        return self._colorspace(image, colorspace)

    def scale(self, image, geometry, options):
        """
        Wrapper for ``_scale``
        """
        crop = options['crop']
        upscale = options['upscale']
        x_image, y_image = map(float, self.get_image_size(image))
        # calculate scaling factor
        factors = (geometry[0] / x_image, geometry[1] / y_image)
        factor = max(factors) if crop else min(factors)
        if factor < 1 or upscale:
            width = toint(x_image * factor)
            height = toint(y_image * factor)
            image = self._scale(image, width, height)
        return image

    def crop(self, image, geometry, options):
        """
        Wrapper for ``_crop``
        """
        crop = options['crop']
        if not crop or crop == 'noop':
            return image
        x_image, y_image = self.get_image_size(image)
        x_offset, y_offset = parse_crop(crop, (x_image, y_image), geometry)
        return self._crop(image, geometry[0], geometry[1], x_offset, y_offset)

    def write(self, image, options, thumbnail):
        """
        Wrapper for ``_write``
        """
        format_ = options['format']
        quality = options['quality']
        self._write(image, format_, quality, thumbnail)

    #
    # Methods which engines need to implement
    # The ``image`` argument refers to a backend image object
    #
    @abstractmethod
    def get_image(self, source):
        """
        Returns the backend image objects from a ImageFile instance
        """
        raise NotImplemented()

    @abstractmethod
    def get_image_size(self, image):
        """
        Returns the image width and height as a tuple
        """
        raise NotImplemented()

    @abstractmethod
    def _colorspace(self, image, colorspace):
        """
        `Valid colorspaces
        <http://www.graphicsmagick.org/GraphicsMagick.html#details-colorspace>`_.
        Backends need to implement the following::

            RGB, GRAY
        """
        raise NotImplemented()

    @abstractmethod
    def _scale(self, image, width, height):
        """
        Does the resizing of the image
        """
        raise NotImplemented()

    @abstractmethod
    def _crop(self, image, width, height, x_offset, y_offset):
        """
        Crops the image
        """
        raise NotImplemented()

    @abstractmethod
    def _write(self, image, format_, quality, thumbnail):
        """
        Writes to the thumbnail which is ImageFile instance
        """
        raise NotImplemented()

