#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Sierpinski Triangles v0.1
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
# Draws Sierpinski triangles
#


# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)

sys.stderr = open(this_directory + 'gimpfu_debug.txt', 'a')
import logging


from gimpfu import *
from classes.point import *



class SierpinskiTriangle(object):
	def __init__(self, image, max_depth=6, size=200):
		self.image = image
		self.width = pdb.gimp_image_width(self.image)
		self.height = pdb.gimp_image_height(self.image)

		self.line_scale = 0.5

		self.n_sides = 3
		self.side_rotation = 120
		self.sides = [[], [], []]
		
		self.max_depth = max(0, min(6, int(max_depth)))					# 6 is as far as you need for normal resolution, unless you really want this in 8k etc

		base_x = int((self.width - size) / 2)
		base_y = int(self.height * 0.50)								# doesn't matter as we have to reposition it vertically anyway

		self.start = Point(base_x, base_y)
		self.end = Point(base_x + size, base_y)

		self.points = []
	pass


	def plot_lines(self, depth=0, start=None, end=None):
		start = start if start is not None else self.start
		end = end if end is not None else self.end

		if depth < self.max_depth:
			length = start.distance_from(end) * self.line_scale
			angle = math.degrees(end.angle_of(start))

			pA = start													# bot left
			pB = pA.make_point(length, math.radians(angle))				# bot mid
			pC = pA.make_point(2* length, math.radians(angle))			# bot right
			pD = pA.make_point(length, math.radians(angle- 60))			# mid left
			pE = pA.make_point(2* length, math.radians(angle- 60))		# top
			pF = pE.make_point(length, math.radians(angle+ 60))			# mid right

			self.plot_lines(depth+1, pA, pB)							# BL
			self.plot_lines(depth+1, pB, pD)							# BL
			self.plot_lines(depth+1, pD, pF)							# TOP
			self.plot_lines(depth+1, pF, pB)							# BR
			self.plot_lines(depth+1, pB, pC)							# BR
			self.plot_lines(depth+1, pC, pE)							# BR + TOP
			self.plot_lines(depth+1, pE, pA)							# TOP + BL
			

		else:
			self.points.extend([Point(start.x, start.y), Point(end.x, end.y)])

	pass


	# given a side (i, 0=top) work out point rotation/reflection - note that the next side uses the modified coords (... python variable references)
	def next_side(self, i, item):
		if i % 2 == 1: # odd
			item.rotate(math.radians(self.side_rotation), self.start)
			item.reflect_x(self.start)
		elif i > 0: # even
			item.reflect_x(self.start.halfway_to(self.end))
		return [item.x, item.y]
	pass


	def rotate_lines(self):
		todo = len(self.points) * self.n_sides
		current = 0

		for item in self.points:
			for i in range(self.n_sides):
				self.sides[i].extend(self.next_side(i, item))

				current += 1
				progress = float(current) / float(todo)
				pdb.gimp_progress_update(progress)


		y_min = min([y for coords in self.sides for y in coords[1::2]])
		y_max = max([y for coords in self.sides for y in coords[1::2]])
		y_mod = (self.height / 2) - ((y_max-y_min) / 2) - y_min			# required height adjustment to vertically center the points

		for coords in self.sides:
			coords[1::2] = [y + y_mod for y in coords[1::2]]			# correct the height
		
	pass


pass


def python_kd_fractals_sierpinski(image, layer, max_depth=5, size=200):
	pdb.gimp_image_undo_group_start(image)
	pdb.gimp_context_push()

	sierpinski = SierpinskiTriangle(image, max_depth, size)

	pdb.gimp_progress_init("Plotting lines ...", None)
	sierpinski.plot_lines()

	# makes triangles out of the triangles
	pdb.gimp_progress_set_text("Rotating lines ...")
	sierpinski.rotate_lines()


	pdb.gimp_progress_set_text("Drawing lines ...")
	tools = {
		'gimp-airbrush': pdb.gimp_airbrush_default,
		'gimp-paintbrush': pdb.gimp_paintbrush_default,
		'gimp-pencil': pdb.gimp_pencil,
		'gimp-convolve': pdb.gimp_convolve_default,
		'gimp-dodge-burn': pdb.gimp_dodgeburn_default,
		'gimp-eraser': pdb.gimp_eraser_default,
		'gimp-smudge': pdb.gimp_smudge_default,
	}
	need_new_layer = ['gimp-airbrush', 'gimp-paintbrush', 'gimp-pencil']
	
	current_tool = pdb.gimp_context_get_paint_method()
	if current_tool not in tools:
		#pdb.gimp_message(current_tool)
		current_tool = "gimp-pencil"
		pdb.gimp_context_set_paint_method(current_tool)
	
	if current_tool in need_new_layer:
		layer = pdb.gimp_layer_new(image, image.width, image.height, RGBA_IMAGE, "Sierpinski Triangles", 100.00, LAYER_MODE_NORMAL)
		pdb.gimp_image_insert_layer(image, layer, None, 0)


	pdb.gimp_progress_update(0.0)
	for i, coords in enumerate(sierpinski.sides):
		if len(coords):
			#logging.warn("drawing coords "+str(len(coords)))
			tools[current_tool](layer, len(coords), coords)
			progress = float(i) / 3.0
			pdb.gimp_progress_update(progress)


	pdb.gimp_context_pop()	
	pdb.gimp_image_undo_group_end(image)
pass


register(
	"fractals_sierpinski_triangles",
	"Draws Sierpinski triangles with selected tool",
	"Draws Sierpinski triangles with selected tool",
	"Keith Drakard",
	"Keith Drakard",
	"2019",
	"<Image>/Filters/Render/Fractals/Sierpinski Triangles...",
	"*",
	[
		(PF_SPINNER, "max_depth", "Iterations", 3, (0, 6, 1)),
		(PF_INT, "size", "Side Length (px)", 200),
	],
	[],
	python_kd_fractals_sierpinski)

main()