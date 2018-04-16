#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

from SimpleSetCreator import geometry as geo

if __name__ == '__main__':
    box1 = geo.BBox((-1, -2), (4, 4))
    box2 = geo.BBox((1, 3), (5, 5))

    print('Bounding box 01: ', box1)
    print('Bounding box 02: ', box2)
    print('Interseção: ', box2.intersect(box1))

    box3 = box1 & box2
    print('E lógico: ', box3)

    box4 = box1 | box2
    print('OU lógico: ', box4)

    p = geo.Point2D(2, 3.5)

    print("Ponto: ", p)
    print("Box3 contém o ponto: ", box3.contains(p))
    print("Box4 contém o ponto: ", box4.contains(p))

    p2 = geo.Point2D(-3, 3.5)

    print("Ponto: ", p2)
    print("Box3 contém o ponto: ", box3.contains(p2))
    print("Box4 contém o ponto: ", box4.contains(p2))

    p3 = geo.Point2D(1, 1)

    print("Ponto: ", p3)
    print("Box3 contém o ponto: ", box3.contains(p3))
    print("Box4 contém o ponto: ", box4.contains(p3))
