# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

class Point2D(object):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def coords(self):
        return (self._x, self._y)

    def resize(self, factor):
        return Point2D(self._x*factor, self._y*factor)

    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

class BBox(object):
    def __init__(self, p1, p2):
        assert len(p1) == 2 and len(p2) == 2

        x_s = (p1[0], p2[0])
        y_s = (p1[1], p2[1])

        self._tl = Point2D(min(x_s), min(y_s))
        self._br = Point2D(max(x_s), max(y_s))

    @property
    def tl(self):
        return self._tl

    @property
    def br(self):
        return self._br

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def width(self):
        return self._br.x - self._tl.x

    @property
    def height(self):
        return self._br.y - self._tl.y

    @property
    def area(self):
        return self.width * self.height

    @property
    def center(self):
        return Point2D(self.tl.x+(self.width/2), self.tl.y+(self.height/2))

    def intersect(self, other):
        return (self & other) is not None

    def contains(self, point):
        return self.tl.x <= point.x and self.tl.y <= point.y and \
                self.br.x >= point.x and self.br.y >= point.y

    def resize(self, factor):
        return BBox(self._tl.resize(factor).coords, self._br.resize(factor).coords)

    def __str__(self):
        template = "BBox origin: {}; end: {}; width: {}; height: {}; center: {}"
        return template.format(self._tl, self._br, self.width, self.height, self.center)

    def __and__(self, other):
        tl = (max(self.tl.x, other.tl.x), max(self.tl.y, other.tl.y))
        br = (min(self.br.x, other.br.x), min(self.br.y, other.br.y))
        if tl[0] < br[0] and tl[1] < br[1]:
            return BBox(tl, br)

        return None

    def __or__(self, other):
        tl = (min(self.tl.x, other.tl.x), min(self.tl.y, other.tl.y))
        br = (max(self.br.x, other.br.x), max(self.br.y, other.br.y))
        return BBox(tl, br)

    def __eq__(self, other):
        return self.tl == other.tl and self.br == other.br
