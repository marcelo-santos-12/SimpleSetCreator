#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

from matplotlib.widgets import RectangleSelector, Cursor
from SimpleSetCreator import geometry as geo

class DatasetCreator:

    def __init__(self, img_name, img_ext="png"):

        self._image = np.array(Image.open(img_name), dtype=np.uint8)
        self.img_name = img_name.split("/")[-1].split(".")[0]

        self._img_ext = img_ext

        self._patches = []

        self._figure, self._axis = plt.subplots(1)

        self._keyset = {"quit": "q", "undo": "u"}

        self._figure.canvas.mpl_connect("key_press_event", self._keypress)

        self._rs = RectangleSelector(self._axis, self._line_select, drawtype="box", \
                useblit=True, button=[1], minspanx=5, minspany=5, spancoords="pixels", \
                interactive=False)
        self._cursor = Cursor(self._axis, useblit=True, color="red", linewidth=1)

        self._run_gui()


    def _undo(self):
        if self._try_to_remove_last_rectangle() is None:
            print("patches list empty!")


    def _try_to_remove_last_rectangle(self):
        if self._patches:
            x0, y0, width, height = self._patches[-1].get_bbox().bounds
            tp_coords = (x0 + width // 2, y0 + height // 2)

            self._patches[-1].remove()

            self._patches.pop()
            self._figure.canvas.draw()

            return tp_coords

        return None


    def _add_rectangle(self, x1, y1, x2, y2):

        obj = plt.Rectangle((x1, y1), x2-x1, y2-y1, \
                edgecolor="blue", linewidth=1.5, fill=False)

        self._axis.add_patch(obj)
        self._patches.append(obj)
        self._figure.canvas.draw()


    def _line_select(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

        self._add_rectangle(x1, y1, x2, y2)


    def _keypress(self, event):
        if event.key == self._keyset["quit"]:
            self._create_dataset()
            plt.close()

        elif event.key == self._keyset["undo"]:
            self._undo()

        else:
            print('Press "q" to finish the program.')


    def _run_gui(self):
        self._axis.imshow(self._image)
        plt.show()


    def _create_dataset(self):

        bounds = [(obj.get_bbox().bounds) for obj in self._patches]
        bboxes = [geo.BBox((x, y), (x+width, y+height)) for (x, y, width, height) in bounds]

        for box in bboxes:
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

    creator = DatasetCreator(i_name, img_ext=i_ext)
