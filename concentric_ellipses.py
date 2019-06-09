#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Concentric Ellipses v0.1
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
# Draws a bunch of ellipses inside each other
#


# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)

sys.stderr = open(this_directory + 'gimpfu_debug.txt', 'a')


import random
from gimpfu import *


class Ellipses(object):
	def __init__(self, image, center_x, center_y, radius_x, radius_y, in_percent, angle, depth, decrease, offset_x, offset_y):
		self.image = image

		self.width = pdb.gimp_image_width(self.image)
		self.height = pdb.gimp_image_height(self.image)

		if in_percent:
			self.center_x = int(center_x * (self.width * 0.01))
			self.center_y = int(center_y * (self.height * 0.01))
			self.radius_x = int(radius_x * (self.width * 0.01))
			self.radius_y = int(radius_y * (self.height * 0.01))

		else:
			self.center_x = int(center_x)
			self.center_y = int(center_y)
			self.radius_x = int(radius_x)
			self.radius_y = int(radius_y)

		self.radius_x = max(1, self.radius_x)
		self.radius_y = max(1, self.radius_y)

		self.angle = math.radians(angle)
		self.max_depth = max(1, min(5, int(depth)))
		self.decrease = max(0.01, min(1.00, float(decrease) * 0.01))
		self.offset_x = max(0.00, min(1.00, float(offset_x) * 0.01))
		self.offset_y = max(0.00, min(1.00, float(offset_y) * 0.01))

		self.vectors = pdb.gimp_vectors_new(self.image, "Ellipses")
		pdb.gimp_image_insert_vectors(self.image, self.vectors, None, 0)

		# progress counter so we don't get bored during the recursion...
		self.count = 0
		self.max_count = sum((4**x) for x in range(0, self.max_depth+1)) # only accurate for decrease = 50% (ie traditional case)
	pass


	def plot_ellipse(self, cx=None, cy=None, rx=None, ry=None, depth=1):
		pdb.gimp_image_undo_freeze(self.image)

		cx = cx if cx is not None else self.center_x
		cy = cy if cy is not None else self.center_y
		rx = rx if rx is not None else self.radius_x
		ry = ry if ry is not None else self.radius_y
		
		# for some unknown-to-me reason, vector ellipses aren't made right (in 2.10.8 at least)
		stroke_id = pdb.gimp_vectors_bezier_stroke_new_ellipse(self.vectors, cx,cy, rx,ry, 0)

		# so this replaces the incorrect Y value at the start with its counterpart on the opposite side and remakes the path
		stroke_type, num_points, controlpoints, closed = pdb.gimp_vectors_stroke_get_points(self.vectors, stroke_id)
		pdb.gimp_vectors_remove_stroke(self.vectors, stroke_id)
		controlpoints = list(controlpoints)
		controlpoints[1] = controlpoints[17]
		controlpoints = tuple(controlpoints)
		stroke_id = pdb.gimp_vectors_stroke_new_from_points(self.vectors, stroke_type, num_points, controlpoints, closed)
		
		# but this simple fix messes up angled ellipses so we separately rotate the path to correct the correction
		angle = - math.degrees(self.angle) # which of course isn't in radians anti-clockwise but degrees clockwise because god knows we don't want any consistency in an api...
		pdb.gimp_vectors_stroke_rotate(self.vectors, stroke_id, cx,cy, angle)

		self.count+= 1
		pdb.gimp_progress_update(float(self.count)/float(self.max_count))

		# now get on with plotting the next ellipse
		if self.decrease < 1 and depth <= self.max_depth:
			rx = int(rx * self.decrease)
			ry = int(ry * self.decrease)

			ox = int(rx * self.offset_x)
			oy = int(ry * self.offset_y)

			if self.offset_x == 0.0 and self.offset_y == 0.0:
				if rx > 0 and ry > 0:
					self.plot_ellipse(cx,cy, rx,ry, depth+1)

			elif self.offset_x == 0.0:
				if rx > 8 and ry > 8:
					self.plot_ellipse(cx,cy + oy, rx,ry, depth+1)
					self.plot_ellipse(cx,cy - oy, rx,ry, depth+1)

			elif self.offset_y == 0.0:
				if rx > 8 and ry > 8:
					self.plot_ellipse(cx + ox,cy, rx,ry, depth+1)
					self.plot_ellipse(cx - ox,cy, rx,ry, depth+1)
					
			else:
				if rx > 8 and ry > 8:
					self.plot_ellipse(cx + ox,cy, rx,ry, depth+1)
					self.plot_ellipse(cx - ox,cy, rx,ry, depth+1)
					self.plot_ellipse(cx,cy + oy, rx,ry, depth+1)
					self.plot_ellipse(cx,cy - oy, rx,ry, depth+1)

					#self.plot_ellipse(cx + ox,cy + oy, rx,ry, depth+1)
					#self.plot_ellipse(cx + ox,cy - oy, rx,ry, depth+1)
					#self.plot_ellipse(cx - ox,cy + oy, rx,ry, depth+1)
					#self.plot_ellipse(cx - ox,cy - oy, rx,ry, depth+1)

		pdb.gimp_image_undo_thaw(self.image)

	pass

	def draw_ellipse(self):
		pdb.gimp_context_set_paint_method("gimp-pencil")	# make sure we have the right tool selected in this context else gimp errors when you have a non-painting tool selected
		pdb.gimp_context_set_brush("1. Pixel")				# I'm assuming the brush is always present - may be better to just create a temp brush
		pdb.gimp_context_set_brush_size(1)
		pdb.gimp_context_set_brush_hardness(1)

		layer = pdb.gimp_layer_new(self.image, self.image.width, self.image.height, RGBA_IMAGE, "Ellipses", 100.00, LAYER_MODE_NORMAL)
		pdb.gimp_image_insert_layer(self.image, layer, None, 0)

		pdb.gimp_drawable_edit_stroke_item(layer, self.vectors)
	pass

pass


def python_kd_concentric_ellipses(image, layer, center_x, center_y, radius_x, radius_y, in_percent, angle, depth, decrease, offset_x, offset_y):
	pdb.gimp_image_undo_group_start(image)

	ellipses = Ellipses(image, center_x, center_y, radius_x, radius_y, in_percent, angle, depth, decrease, offset_x, offset_y)

	pdb.gimp_progress_init("Plotting ellipses ...", None)
	ellipses.plot_ellipse()
	pdb.gimp_progress_set_text("Drawing ellipse plots ...")
	ellipses.draw_ellipse()
	
	pdb.gimp_image_undo_group_end(image)
pass


register(
	"concentric_ellipses",
	"Draw concentric ellipses",
	"Draws a set of ever decreasing concentric ellipses around a center point.",
	"Keith Drakard",
	"Keith Drakard",
	"2019",
	"<Image>/Filters/Render/Pattern/Concentric Ellipses...",
	"*",
	[
		(PF_INT, "center_x", "X Center", 50),
		(PF_INT, "center_y", "Y Center", 50),
		(PF_INT, "radius_x", "X Radius", 50),
		(PF_INT, "radius_y", "Y Radius", 50),
		(PF_BOOL, "in_percent", "In Percent?", 1),
		(PF_SPINNER, "angle", "Angle (X Axis)", 0, (0,359,1)),
		
		(PF_SPINNER, "depth", "Depth", 3, (1,5,1)),
		(PF_SPINNER, "decrease", "Reduce By %", 50, (1,100,1)),

		(PF_INT, "offset_x", "X Radius Offset %", 100),
		(PF_INT, "offset_y", "Y Radius Offset %", 100),
	],
	[],
	python_kd_concentric_ellipses)

main()