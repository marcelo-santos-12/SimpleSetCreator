#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from SimpleSetCreator import geometry as geo

if __name__ == '__main__':
    box1 = geo.BBox((-1, -2), (4, 4))
    box2 = geo.BBox((1, 4), (5, 5))

    print('Bounding box 01: ', box1)
    print('Bounding box 02: ', box2)
    print('Interseção: ', box2.intersect(box1))

    box3 = box1 & box2
    print('E lógico: ', box3)

    box4 = box1 | box2
    print('OU lógico: ', box4)
