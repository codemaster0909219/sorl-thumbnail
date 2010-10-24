from django.core.cache import cache
from django.db import models
from django.db.models import signals
from sorl.thumbnail.conf import settings
from sorl.thumbnail.helpers import get_cache_key, Options


class ThumbnailCacheManager(models.Manager):
    def get(self, source_name, source_storage, options):
        cache_key = get_cache_key(
            source_name,
            source_storage,
            options,
            )
        obj = cache.get(cache_key)
        if not obj:
            sup = super(ThumbnailCacheManager, self)
            obj = sup.get_query_set().get(
                source_name=source_name,
                source_storage=source_storage,
                options=options,
                )
            cache.set(cache_key, obj, settings.THUMBNAIL_CACHE_TIMEOUT)
        return obj


class Thumbnail(models.Model):
    source_name = models.CharField(max_length=1000, db_index=True)
    source_storage = models.CharField(max_length=200, db_index=True)
    source_width = models.PositiveIntegerField()
    source_height = models.PositiveIntegerField()
    options = models.CharField(max_length=1000, db_index=True)

    name = models.CharField(max_length=1000)
    url = models.CharField(max_length=1000, unique=True)
    path = models.CharField(max_length=1000)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    size = models.PositiveIntegerField()

    objects = models.Manager()
    cache = ThumbnailCacheManager()

    x = property(lambda self: self.width)
    y = property(lambda self: self.height)

    def css_margin(self):
        opts_list = self.options.split(' ')
        if self.source_height > self.source_width:
            geometry_string = opts_list[1]
        else:
            geometry_string = opts_list[0]
        geometry = Geometry(geometry_string)
        return geometry.css_margin()

    @property
    def cache_key(self):
        return get_cache_key(
            self.source_name,
            self.source_storage,
            self.options,
            )

    class Meta:
        unique_together = (('source_name', 'source_storage', 'options'),)


def invalidate_cache(sender, instance, **kwargs):
    cache.delete(instance.cache_key)

def update_cache(sender, instance, **kwargs):
    cache.set(instance.cache_key, instance, settings.THUMBNAIL_CACHE_TIMEOUT)

signals.pre_save.connect(invalidate_cache, sender=Thumbnail)
signals.post_save.connect(update_cache, sender=Thumbnail)
signals.pre_delete.connect(invalidate_cache, sender=Thumbnail)

