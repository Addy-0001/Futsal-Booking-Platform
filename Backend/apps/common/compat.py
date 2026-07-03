"""
Runtime compatibility shims.

Python 3.14 made ``super`` objects copyable, which breaks Django's
``BaseContext.__copy__`` (it relied on ``copy(super())`` returning a copy of the
underlying instance). On 3.14 that now returns the ``super`` proxy itself, so
setting ``.dicts`` raises:

    AttributeError: 'super' object has no attribute 'dicts'
    and no __dict__ for setting new attributes

This crashes any admin changelist render. Django fixed it upstream in 5.2
(ticket #35844 / PR #18824). This project is pinned to Django < 5.2, so we
backport the exact fix at startup. It is a no-op on Python < 3.14 and on any
Django that has already fixed ``__copy__``.

Remove this module once you move to Django >= 5.2.
"""

import sys
from copy import copy


def patch_basecontext_copy():
    if sys.version_info < (3, 14):
        return

    from django.template.context import BaseContext

    def __copy__(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__ = copy(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = __copy__


def apply():
    patch_basecontext_copy()
