#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Image Guides v0.1
# 
# Copyright 2019, Keith Drakard; Released under the 3-Clause BSD License
# See https://opensource.org/licenses/BSD-3-Clause for details
#
#
# Change Log
# ----------
# 0.1: Initial release
#
# ------------------------------------------------------------------------------
#
# Adds a grid of guides to the image
#


from gimpfu import *

class Guides(object):
	def __init__(self, image, space_x, space_y, in_percent):
		self.image = image

		self.width = pdb.gimp_image_width(self.image)
		self.height = pdb.gimp_image_height(self.image)

		if in_percent:
			self.space_x = int(space_x * (self.width * 0.01))
			self.space_y = int(space_y * (self.height * 0.01))
		else:
			self.space_x = max(1, min(self.width, int(space_x)))
			self.space_y = max(1, min(self.height, int(space_y)))

		self.okay = False # quick sanity check
		
		if (self.space_x > 0 and self.space_y > 0):
			# how many guide lines?
			self.guides_x = int(self.width/self.space_x)
			self.guides_y = int(self.height/self.space_y)
			self.okay = True

	pass

	def add_guides(self):
		if not self.okay:
			return

		# vertical guides along the x-axis
		for i in range(0, self.guides_x):
			pdb.gimp_image_add_vguide(self.image, i * self.space_x)

		# horizontal guides along the y-axis
		for i in range(0, self.guides_y):
			pdb.gimp_image_add_hguide(self.image, i * self.space_y)

		# final 2 borders
		pdb.gimp_image_add_vguide(self.image, self.width)
		pdb.gimp_image_add_hguide(self.image, self.height)
	pass

pass


def python_kd_image_guides(image, layer, space_x, space_y, in_percent):
	pdb.gimp_image_undo_group_start(image)
	guides = Guides(image, space_x, space_y, in_percent)
	guides.add_guides()
	pdb.gimp_image_undo_group_end(image)
pass


register(
	"python_fu_kd_image_guides",
	"Image Guide Grid",
	"Creates a grid of guides with either pixel or percentage spacing.",
	"Keith Drakard",
	"Keith Drakard",
	"2019",
	"<Image>/Image/Guides/Add Grid...",
	"*",
	[
		(PF_INT, "space_x", "Horizontal Spacing", 10),
		(PF_INT, "space_y", "Vertical Spacing", 10),
		(PF_BOOL, "in_percent", "In Percent?", 1)
	],
	[],
	python_kd_image_guides)

main()