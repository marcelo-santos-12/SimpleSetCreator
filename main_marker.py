#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import argparse
import glob
import cv2

import matplotlib.pyplot as plt
import pandas as pd

from matplotlib.widgets import RectangleSelector, Cursor

import utils

def create_lists(bounds):
    x1s = []
    y1s = []
    x2s = []
    y2s = []

    for (x, y, width, height) in bounds:
        x1s.append(x)
        y1s.append(y)
        x2s.append(x+width)
        y2s.append(y+height)

    return x1s, y1s, x2s, y2s


class ImageMarker(object):

    def __init__(self, img):

        self._image = img

        self._patches = []
        self._boxes = []

        self._figure, self._axis = plt.subplots(1)

        self._keyset = {"quit": "q", "undo": "u", "skip": "s", "help": "h", \
                "process": "p"}
        self._modifiers = {"shift", "control"}

        self._should_quit = False

        self._figure.canvas.mpl_connect("key_press_event", self._keypress)

        self._rs = RectangleSelector(self._axis, self._line_select, drawtype="box", \
                useblit=True, button=[1], minspanx=5, minspany=5, spancoords="pixels", \
                interactive=False)
        self._cursor = Cursor(self._axis, useblit=True, color="red", linewidth=1)

        self._run_gui()


    @property
    def should_quit(self):
        return self._should_quit


    @property
    def boxes(self):
        return self._boxes


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
        if event.key == self._keyset["process"]:
            self._process_boxes()
            plt.close()

        elif event.key == self._keyset["quit"]:
            self._should_quit = True
            plt.close()

        elif event.key == self._keyset["undo"]:
            self._undo()

        elif event.key == self._keyset["skip"]:
            plt.close()

        elif event.key == self._keyset["help"]:
            print("Commands:")
            print("\th -- show help message.")
            print("\tp -- process image.")
            print("\ts -- skip the image processing without terminating the program.")
            print("\tu -- undo last selection.")
            print("\tq -- terminate the program.")

        elif event.key in self._modifiers:
            pass

        else:
            print('Press "h" for help.')


    def _run_gui(self):
        self._axis.imshow(cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB))
        plt.show()


    def _process_boxes(self):

        if not self._patches:
            return

        self._boxes = [(obj.get_bbox().bounds) for obj in self._patches]


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("-i", "--input", required=True, \
            help="Path to the directory of images")

    ap.add_argument("-ie", "--input_extension", required=False, \
            help="The extension type of the input images")

    ap.add_argument("-o", "--output", required=False, \
            help="The folder where the csvs folder will be stored.")

    args = vars(ap.parse_args())

    i_name = args["input"]
    o_name = "samples"
    i_ext = "png"

    if args["input_extension"]:
        i_ext = args["input_extension"]

    if args["output"]:
        o_name = args["output"]

    template = "{}/*.{}".format(i_name, i_ext)
    print(template)

    files = sorted(glob.glob(template), key=os.path.getmtime)
    n_files = len(files)

    plt.rcParams["keymap.save"] = ""

    for i, f in enumerate(files):
        print("Processing file: {} ({}/{})".format(f, i+1, n_files))
        image = cv2.imread(f)
        splited_filename = f.split("/")
        img_dir, img_nam = splited_filename[-2], splited_filename[-1].split(".")[0]
        creator = ImageMarker(image)

        if creator.should_quit:
            print("Terminating...")
            break

        x1s, y1s, x2s, y2s = create_lists(creator.boxes)

        raw_data = {"x_1": x1s, "y_1": y1s, "x_2": x2s, "y_2": y2s}
        df = pd.DataFrame(raw_data, columns=["x_1", "y_1", "x_2", "y_2", ])

        utils.check_dir(o_name)

        ou_file = "{}/{}_{}.csv".format(o_name, img_dir, img_nam)
        df.to_csv(ou_file, index=False)


if __name__ == "__main__":
    main()
