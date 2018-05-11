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

import geometry as geo
import utils


class ImageMarker:

    def __init__(self, img, img_ext="png", output_folder="."):

        self._image = img

        self._pos_out_dir = "{}/positives".format(output_folder)
        self._neg_out_dir = "{}/negatives".format(output_folder)

        self._patches = []

        self._figure, self._axis = plt.subplots(1)

        self._keyset = {"quit": "q", "undo": "u", "skip": "s", "help": "h", "process": "p"}
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
            self._create_csv()
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


    def _create_csv(self):

        bounds = [(obj.get_bbox().bounds) for obj in self._patches]

        x1s, y1s, x2s, y2s = _create_lists(bounds)

        raw_data = {"x_1": x1s, "y_1": y1s, "x_2": x2s, "y_2": y2s}
        df = pd.DataFrame(raw_data, columns=["x_1", "y_1", "x_2", "y_2", ])

        ou_file = "{}/{}.csv".format(o_name, i+1, time_block)
        df.to_csv(ou_file, index=False)

    
    def _create_lists(self, bounds):
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


    def _create_positive_samples(self, bboxes):

        utils.check_dir(self._pos_out_dir)

        rot_mats = []
        rot_mats.append(cv2.getRotationMatrix2D( \
                (self._sample_sz // 2, self._sample_sz // 2), 90, 1.0))
        rot_mats.append(cv2.getRotationMatrix2D( \
                (self._sample_sz // 2, self._sample_sz // 2), 180, 1.0))
        rot_mats.append(cv2.getRotationMatrix2D( \
                (self._sample_sz // 2, self._sample_sz // 2), 270, 1.0))

        for box in bboxes:
            p1 = box.tl
            p2 = box.br

            imgs = []
            croped = self._image[int(p1.y):int(p2.y), int(p1.x):int(p2.x), :]
            imgs.append(cv2.resize(croped, (self._sample_sz, self._sample_sz), \
                    interpolation=cv2.INTER_AREA))
            imgs.append(cv2.flip(imgs[0], 1))

            for img in imgs:
                tmp_name = utils.get_random_file_name(extension=self._img_ext)
                cv2.imwrite("{}/{}".format(self._pos_out_dir, tmp_name), img)

                for r_mat in rot_mats:
                    tmp_name = utils.get_random_file_name(extension=self._img_ext)
                    rotated = cv2.warpAffine(img, r_mat, (self._sample_sz, self._sample_sz))
                    cv2.imwrite("{}/{}".format(self._pos_out_dir, tmp_name), rotated)

                    resized = cv2.pyrUp(cv2.pyrDown(rotated))
                    tmp_name = utils.get_random_file_name(extension=self._img_ext)
                    cv2.imwrite("{}/{}".format(self._pos_out_dir, tmp_name), resized)


    def _create_negative_samples(self, bboxes):

        utils.check_dir(self._neg_out_dir)

        img_res = cv2.pyrDown(cv2.pyrDown(self._image))
        boxes_res = [b.resize(1/4) for b in bboxes]

        for prob_b in self._create_boxes(img_res.shape[:2], boxes_res):
            tl = prob_b.tl
            br = prob_b.br

            croped = img_res[int(tl.y):int(br.y), int(tl.x):int(br.x), :]
            tmp_name = utils.get_random_file_name(extension=self._img_ext)
            cv2.imwrite("{}/{}".format(self._neg_out_dir, tmp_name), croped)


    def _create_boxes(self, img_dims, pos_boxes):
        boxes = []

        for y in range(0, img_dims[0]-self._sample_sz, self._sample_sz):
            for x in range(0, img_dims[1]-self._sample_sz, self._sample_sz):
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

    ap.add_argument("-i", "--input", required=True, \
            help="Path to the directory of images")

    ap.add_argument("-ie", "--input_extension", required=False, \
            help="The extension type of the input images")

    ap.add_argument("-oe", "--output_extension", required=False, \
            help="The extension type of the output images")

    ap.add_argument("-o", "--output", required=False, \
            help="The folder where the positive and negative samples will be stored")

    args = vars(ap.parse_args())

    i_name = args["input"]
    o_name = "samples"
    i_ext = "png"
    o_ext = "png"

    if args["input_extension"]:
        i_ext = args["input_extension"]

    if args["output_extension"]:
        o_ext = args["output_extension"]

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
        creator = ImageMarker(image, img_ext=o_ext, output_folder=o_name)

        if creator.should_quit:
            print("Terminating...")
            break
