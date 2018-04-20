#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import tempfile
import argparse
import cv2
import matplotlib.pyplot as plt

from matplotlib.widgets import RectangleSelector, Cursor
from SimpleSetCreator import geometry as geo


def get_random_file_name(extension="png"):
    random_name = tempfile.NamedTemporaryFile(prefix="", \
            suffix=".{}".format(extension), dir=".").name
    random_name = os.path.split(random_name)[-1]
    return random_name


def check_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


class DatasetCreator:

    def __init__(self, img_name, sample_size=64, img_ext="png", output_folder="."):

        self._image = cv2.imread(img_name)

        img_name = img_name.split("/")[-1].split(".")[0]
        self._pos_out_dir = "{}/{}/positives".format(output_folder, img_name)
        self._neg_out_dir = "{}/{}/negatives".format(output_folder, img_name)

        self._img_ext = img_ext

        self._sample_sz = sample_size

        self._patches = []

        self._figure, self._axis = plt.subplots(1)

        self._keyset = {"quit": "q", "undo": "u"}
        self._modifiers = {"shift", "control"}

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

        elif event.key in self._modifiers:
            pass

        else:
            print('Press "q" to finish the program.')


    def _run_gui(self):
        self._axis.imshow(cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB))
        plt.show()


    def _create_dataset(self):

        bounds = [(obj.get_bbox().bounds) for obj in self._patches]
        bboxes = [geo.BBox((x, y), (x+width, y+height)) \
                for (x, y, width, height) in bounds]

        self._create_positive_samples(bboxes)
        self._create_negative_samples(bboxes)


    def _create_positive_samples(self, bboxes):

        file_path = "{}/{}"
        check_dir(self._pos_out_dir)
        final_sz = (self._sample_sz, self._sample_sz)

        for box in bboxes:
            p1 = box.tl
            p2 = box.br
            croped = self._image[int(p1.y):int(p2.y), int(p1.x):int(p2.x), :]
            resized = cv2.resize(croped, final_sz, interpolation=cv2.INTER_AREA)

            tmp_name = get_random_file_name(extension=self._img_ext)
            cv2.imwrite(file_path.format(self._pos_out_dir, tmp_name), resized)


    def _create_negative_samples(self, bboxes):

        file_path = "{}/{}"
        check_dir(self._neg_out_dir)

        pyramid = []
        pos_boxes = []

        img_copy = self._image.copy()
        pyramid.append(img_copy)
        pos_boxes.append(list(bboxes))

        for i in range(1, 4):
            img_copy = cv2.pyrDown(img_copy)
            pyramid.append(img_copy)
            pos_boxes.append([b.resize(1/(2**i)) for b in bboxes])

        for (scaled, p_boxes) in zip(pyramid, pos_boxes):

            for prob_b in self._create_boxes(scaled.shape[:2], p_boxes):
                tl = prob_b.tl
                br = prob_b.br

                croped = scaled[int(tl.y):int(br.y), int(tl.x):int(br.x), :]
                tmp_name = get_random_file_name(extension=self._img_ext)
                cv2.imwrite(file_path.format(self._neg_out_dir, tmp_name), croped)


    def _create_boxes(self, img_dims, pos_boxes):
        boxes = []

        for y in range(0, img_dims[0], self._sample_sz):
            for x in range(0, img_dims[1], self._sample_sz):
                b = geo.BBox((x, y), (x+self._sample_sz, y+self._sample_sz))

                valid = True
                for p_b in pos_boxes:
                    if p_b.intersect(b):
                        valid = False

                if valid is True:
                    boxes.append(b)

        return boxes


if __name__ == "__main__":
    ap = argparse.ArgumentParser()

    ap.add_argument("-i", "--image", required=True, \
            help="Path to the image")

    ap.add_argument("-ie", "--image_extension", required=False, \
            help="The extension type of the output images")

    ap.add_argument("-o", "--output", required=False, \
            help="The folder where the positive and negative samples will be stored")

    ap.add_argument("-ss", "--sample_size", required=False, type=int, \
            help="The size of the resulting samples")

    args = vars(ap.parse_args())

    i_name = args["image"]
    o_name = "samples"
    i_ext = "png"
    s_sz = 64

    if args["image_extension"]:
        i_ext = args["image_extension"]

    if args["output"]:
        o_name = args["output"]

    if args["sample_size"]:
        s_sz = args["sample_size"]

    creator = DatasetCreator(i_name, sample_size=s_sz, img_ext=i_ext, output_folder=o_name)
