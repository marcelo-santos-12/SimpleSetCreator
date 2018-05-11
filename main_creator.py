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

from matplotlib.widgets import RectangleSelector, Cursor

import geometry as geo
import utils


class DatasetCreator:

    def __init__(self, img, sample_size=64, img_ext="png", output_folder="."):

        self._image = img

        self._pos_out_dir = "{}/positives".format(output_folder)
        self._neg_out_dir = "{}/negatives".format(output_folder)

        self._img_ext = img_ext

        self._sample_sz = sample_size

        self._patches = []

        self._figure, self._axis = plt.subplots(1)

        self._keyset = {"quit": "q", "undo": "u", "skip": "s", "help": "h", \
                "process_all": "a", "process_positives": "p", "process_negatives": "n"}
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
        if event.key == self._keyset["process_all"]:
            self._create_dataset(True, True)
            plt.close()

        elif event.key == self._keyset["process_positives"]:
            self._create_dataset(True, False)
            plt.close()

        elif event.key == self._keyset["process_negatives"]:
            self._create_dataset(False, True)
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
            print("\ta -- process positive and negative samples.")
            print("\tp -- process positive samples.")
            print("\tn -- process negative samples.")
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


    def _create_dataset(self, gen_pos, gen_neg):

        bounds = [(obj.get_bbox().bounds) for obj in self._patches]
        bboxes = [geo.BBox((x, y), (x+width, y+height)) \
                for (x, y, width, height) in bounds]

        if gen_pos:
            self._create_positive_samples(bboxes)
        if gen_neg:
            self._create_negative_samples(bboxes)


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

    ap.add_argument("-ss", "--sample_size", required=False, type=int, \
            help="The size of the resulting samples")

    args = vars(ap.parse_args())

    i_name = args["input"]
    o_name = "samples"
    i_ext = "png"
    o_ext = "png"
    s_sz = 64

    if args["input_extension"]:
        i_ext = args["input_extension"]

    if args["output_extension"]:
        o_ext = args["output_extension"]

    if args["output"]:
        o_name = args["output"]

    if args["sample_size"]:
        s_sz = args["sample_size"]

    template = "{}/*.{}".format(i_name, i_ext)
    print(template)

    files = sorted(glob.glob(template), key=os.path.getmtime)
    n_files = len(files)

    plt.rcParams["keymap.save"] = ""

    for i, f in enumerate(files):
        print("Processing file: {} ({}/{})".format(f, i+1, n_files))
        image = cv2.imread(f)
        creator = DatasetCreator(image, sample_size=s_sz, img_ext=o_ext, \
            output_folder=o_name)

        if creator.should_quit:
            print("Terminating...")
            break
