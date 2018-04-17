#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

from SimpleSetCreator import geometry as geo

class DatasetCreator:

    def __init__(self, img_name, initial_rect_sz=80, img_ext="png"):

        self._image = np.array(Image.open(img_name), dtype=np.uint8)
        self.img_name = img_name.split("/")[-1].split(".")[0]

        self._rect_sz = initial_rect_sz
        self._p_shift = initial_rect_sz // 2

        self._img_ext = img_ext

        self._patches = []

        self._figure, self._axis = plt.subplots(1)
        self._canvas = self._figure.canvas

        self._keyset = {"quit": "q", "undo": "u", "inc_rect_sz": "i", "dec_rect_sz": "d"}

        self._canvas.mpl_connect("button_press_event", self._onclick)
        self._canvas.mpl_connect("key_press_event", self._keypress)

        self._run_gui()


    def _undo(self):
        if self._try_to_remove_last_rectangle() is None:
            print("patches list empty!")


    def _try_to_remove_last_rectangle(self):
        if self._patches:
            tp_coords = self._patches[-1].get_xy()

            self._patches[-1].remove()

            self._patches.pop()
            self._canvas.draw()

            return tp_coords

        return None


    def _add_rectangle(self, coords):

        obj = plt.Rectangle(coords, self._rect_sz, self._rect_sz, \
                edgecolor="blue", linewidth=1.5, fill=False)

        self._axis.add_patch(obj)
        self._patches.append(obj)
        self._canvas.draw()


    def _onclick(self, event):

        if event.dblclick:
            if event.button == 1:
                self._add_rectangle((event.xdata - self._p_shift, event.ydata - self._p_shift))

        else:
            pass  # Do nothing


    def _keypress(self, event):
        if event.key == self._keyset["quit"]:
            self._create_dataset()
            plt.close()

        elif event.key == self._keyset["undo"]:
            self._undo()

        elif event.key == self._keyset["inc_rect_sz"]:
            self._rect_sz += 2
            self._p_shift = self._rect_sz // 2

            tp_coords = self._try_to_remove_last_rectangle()
            if tp_coords is not None:
                self._add_rectangle(tp_coords)

        elif event.key == self._keyset["dec_rect_sz"]:
            self._rect_sz -= 2
            self._p_shift = self._rect_sz // 2

            tp_coords = self._try_to_remove_last_rectangle()
            if tp_coords is not None:
                self._add_rectangle(tp_coords)

        else:
            print('Press "q" to finish the program.')


    def _run_gui(self):
        self._axis.imshow(self._image)
        plt.show()


    def _create_dataset(self):

        tp_coords = [(p.get_xy()) for p in self._patches]
        bboxes = [geo.BBox((x, y), \
                (x+self._rect_sz, y+self._rect_sz)) for (x, y) in tp_coords]

        for box in bboxes:
            print(box)
            p1 = box.tl
            p2 = box.br
            croped = self._image[int(p1.y):int(p2.y), int(p1.x):int(p2.x), :]

            plt.figure()
            plt.imshow(croped)
            plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()

    ap.add_argument("-i", "--image", required=True, \
            help="Path to the image")

    ap.add_argument("-ie", "--image_extension", required=False, \
            help="The extension type of the output images")

    args = vars(ap.parse_args())

    i_name = args["image"]
    i_ext = "png"

    if args["image_extension"]:
        i_ext = args["image_extension"]

    creator = DatasetCreator(i_name, initial_rect_sz=60, img_ext=i_ext)
