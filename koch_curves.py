#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Koch Curves v0.1
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
# Draws a Koch curve with an angle between -90 to 90 degrees, up to 6 iterations
# deep, and then rotates this line to create a 1-10 sided shape centered in the
# middle of the image.
#


# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)

sys.stderr = open(this_directory + 'gimpfu_debug.txt', 'a')

from classes.mygtk import *
from classes.point import *



class KochCurve(object):
	def __init__(self, image, args):
		self.image = image
		self.width = pdb.gimp_image_width(self.image)
		self.height = pdb.gimp_image_height(self.image)

		self.koch_angle = float(args['angle'])
		rads1 = math.radians((180 - self.koch_angle) / 2)				# law of sines to solve the imaginary right angled triangle (at the half way point) first then again for the length we want
		rads2 = math.radians(self.koch_angle / 2)
		rads3 = math.radians(180 - self.koch_angle)
		hypot = 0.5 / (math.sin(rads1))
		self.line_scale = (hypot * math.sin(rads2)) / math.sin(rads3)

		self.n_sides = max(1, min(10, int(args['sides'])))
		self.side_rotation = 360 / self.n_sides							# (note: 7 sides doesn't divide nicely)
		self.sides = [[] for i in range(self.n_sides)]					# turn a single koch line (self.points) into as many sides as wanted
		
		self.max_depth = max(0, min(6, int(args['max_depth'])))			# 6 is as far as you need for normal resolution, unless you really want this in 8k etc

		base_x = int((self.width - args['size']) / 2)
		base_y = int(self.height * 0.50)								# doesn't matter as we have to reposition it vertically anyway

		self.start = Point(base_x, base_y)
		self.end = Point(base_x + args['size'], base_y)

		self.points = [Point(base_x, base_y)]							# ... python variable references
	

	def plot_lines(self, depth=0, start=None, end=None):
		start = start if start is not None else self.start
		end = end if end is not None else self.end

		if depth < self.max_depth:
			length = start.distance_from(end) * self.line_scale
			angle = math.degrees(end.angle_of(start))

			pA = start
			pB = pA.make_point(length, math.radians(angle))
			pC = pB.make_point(length, math.radians(angle-self.koch_angle))
			pD = pC.make_point(length, math.radians(angle+self.koch_angle))
			pE = end

			self.plot_lines(depth+1, pA, pB)
			self.plot_lines(depth+1, pB, pC)
			self.plot_lines(depth+1, pC, pD)
			self.plot_lines(depth+1, pD, pE)

		else:
			self.points.append(Point(end.x, end.y))						# only need to append end as we already have the previous point

	# given a side (i, 0=top) work out point rotation/reflection - note that the next side uses the modified coords (... python variable references)
	def next_side(self, i, item):
		if i % 2 == 1: # odd
			item.rotate(math.radians(self.side_rotation), self.start)
			item.reflect_x(self.start)
		elif i > 0: # even
			item.reflect_x(self.start.halfway_to(self.end))
		return [item.x, item.y]

	def rotate_lines(self):
		for item in self.points:
			for i in range(self.n_sides):
				self.sides[i].extend(self.next_side(i, item))

	def center_vertically(self):
		y_min = min([y for coords in self.sides for y in coords[1::2]])
		y_max = max([y for coords in self.sides for y in coords[1::2]])
		y_mod = (self.height / 2) - ((y_max-y_min) / 2) - y_min			# required height adjustment to vertically center the points

		for coords in self.sides:
			coords[1::2] = [y + y_mod for y in coords[1::2]]			# correct the height
		


def KochWrapper(args):
		
	image, layer, args = args
	
	koch = KochCurve(image, args)

	pdb.gimp_progress_init("Plotting lines ...", None)
	koch.plot_lines()

	pdb.gimp_progress_set_text("Rotating lines ...")
	koch.rotate_lines()
	koch.center_vertically()

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
		layer_type = RGBA_IMAGE if image.base_type is RGB else GRAYA_IMAGE
		layer = pdb.gimp_layer_new(image, image.width, image.height, layer_type, "Koch Curve", 100.00, LAYER_MODE_NORMAL)
		pdb.gimp_image_insert_layer(image, layer, None, 0)

	for coords in koch.sides:
		if len(coords):
			tools[current_tool](layer, len(coords), coords)
		



##### end of the real code #####


plugin = PythonFu(
	title = 'Koch Curves',
	icon = os.path.join(this_directory, 'icons', 'draw-spiral-2-32x32.png'),
	description = 'Draws Koch curves with the currently selected tool',
	author = 'Keith Drakard',
	date = '2019',
	menu = '<Image>/Filters/Render/Fractals/_Koch Curves...',
	dialog_width = 280,
	widgets = [
		{
			'variable'	: 'angle',
			'label'		: 'Angle',
			'tooltip'	: 'Angle that controls the shape of the Koch curve.', 
			'label_width' : 100,
			'markup'	: '{} ({}°)',
			'type'		: IntSlider,						
			'range'		: (-90,90),
			'default'	: 60,
		},
		{
			'variable'	: 'max_depth',
			'label'		: 'Iterations',
			'tooltip'	: 'Number of iterations to run.',
			'label_width' : 100,
			'type'		: IntSlider,
			'range'		: (0,6),
			'step'		: (1,1),
			'default'	: 4,
		},
		{
			'variable'	: 'sides',
			'label'		: 'Sides', 
			'tooltip'	: 'Number of times that the Koch curve will be copied and rotated.',
			'label_width' : 100,
			'type'		: IntSlider,
			'range'		: (1,10),
			'step'		: (1,1),
			'default'	: 3,
		},
		{
			'variable'	: 'size',
			'label'		: 'Side Length', 
			'tooltip'	: 'Pixel length of the first side; note that more sides will result in a bigger final image than this number.',
			'label_width' : 100,
			'type'		: IntEntry,
			'default'	: 200,
		},
	],
	help_text = {
		'label' : ('Draws a Koch curve with an angle between -90° and 90°, up to 6 iterations deep, and then rotates this line to create a 1-10 sided shape centered in the middle of the image.', 'Uses the current drawing options - ie. color, brush and tool (or the Pencil if the current tool can\'t draw).'),
	},
	code_function = KochWrapper
)

plugin.main()
