#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Fractal Tree v0.1
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
# Draws a fractal tree
#


# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)

sys.stderr = open(this_directory + 'gimpfu_debug.txt', 'a')

from classes.mygtk import *
from classes.colorful import *
from classes.point import *
import random


class FractalTree(object):
	def __init__(self, image, args):
		self.image = image
		self.width = pdb.gimp_image_width(self.image)
		self.height = pdb.gimp_image_height(self.image)

		base_x = int(self.width * args['base_x'] * 0.01)
		base_y = int(self.height * args['base_y'] * 0.01)
		self.base = Point(base_x, base_y)

		self.branches = max(0, min(6, int(args['branches'])))
		self.branch_angle = max(0, min(180, int(args['angle'])))

		self.angle = -90 # initial angle (up)

		self.depth = 0
		self.max_depth = max(1, min(10, int(args['max_depth'])))

		self.length = max(100, int(args['length'])) # self.height * 0.25 # initial height
		self.decrease = 1.0 - float(max(1, min(100, int(args['decrease']))) * 0.01)  # keep this much of the branch each depth

		self.vectors = []


	def plot_tree(self, base=None, depth=None, angle=None, length=None):
		base = base if base is not None else self.base
		depth = depth if depth is not None else self.depth
		angle = angle if angle is not None else self.angle
		length = length if length is not None else self.length

		if depth < self.max_depth and length > 2:
			pdb.gimp_image_undo_freeze(self.image)

			tip = base.make_point(length, math.radians(angle))
			if self.branches == 1:
				tip.check_bounds(self.width, self.height)

			length *= self.decrease

			if len(self.vectors) <= depth:
				self.vectors.append(pdb.gimp_vectors_new(self.image, "Fractal Tree "+str(depth)))
				pdb.gimp_image_insert_vectors(self.image, self.vectors[depth], None, 0)

			#half = base.halfway_to(tip)
			#points = [base.x,base.y] * 3 + [half.x+random.uniform(-10,10),half.y] * 3 + [tip.x,tip.y] * 3
			points = [base.x,base.y] * 3 + [tip.x,tip.y] * 3

			stroke_id = pdb.gimp_vectors_stroke_new_from_points(self.vectors[depth], VECTORS_STROKE_TYPE_BEZIER, len(points), points, 0)

			if self.branches > 0:
				noof_branches = self.branches
			else:
				noof_branches = random.randint(2, 4)

			if self.branch_angle > 0:
				degrees_offset = (sum((i * self.branch_angle) for i in range(1, noof_branches, 1)) / noof_branches)
				for i in range(noof_branches):
					theta = (i * self.branch_angle) - degrees_offset
					self.plot_tree(tip, depth+1, angle + theta, length)
			else:
				sd = 20 if noof_branches == 1 else 50

				for i in range(noof_branches):
					mu = tip.angle_of(base)
					theta = random.gauss(mu, sd)
					#pdb.gimp_message("{} {} = {} {} {}".format(depth, length, angle, mu, theta))
					self.plot_tree(tip, depth+1, angle + theta, length)


			pdb.gimp_image_undo_thaw(self.image)
	

##### end of class #####


def FractalTreeWrapper(args):
	
	image, layer, args = args

	tree = FractalTree(image, args)
	
	if args['branches'] == 1:
		tree.angle = random.gauss(tree.angle,20)

	pdb.gimp_progress_init("Plotting tree ...", None)
	tree.plot_tree()


	pdb.gimp_progress_set_text("Drawing lines ...")
	tools = {
		'gimp-airbrush': pdb.gimp_airbrush_default,
		'gimp-paintbrush': pdb.gimp_paintbrush_default,
		'gimp-pencil': pdb.gimp_pencil,
		#'gimp-convolve': pdb.gimp_convolve_default,
		#'gimp-dodge-burn': pdb.gimp_dodgeburn_default,
		#'gimp-eraser': pdb.gimp_eraser_default,
		#'gimp-smudge': pdb.gimp_smudge_default,
	}
	need_new_layer = ['gimp-airbrush', 'gimp-paintbrush', 'gimp-pencil']
	
	current_tool = pdb.gimp_context_get_paint_method()
	if current_tool not in tools:
		#pdb.gimp_message(current_tool)
		current_tool = 'gimp-pencil'
		pdb.gimp_context_set_paint_method(current_tool)
	
	if current_tool in need_new_layer:
		layer_type = RGBA_IMAGE if image.base_type is RGB else GRAYA_IMAGE
		layer = pdb.gimp_layer_new(image, image.width, image.height, layer_type, 'Fractal Tree', 100.00, LAYER_MODE_NORMAL)
		pdb.gimp_image_insert_layer(image, layer, None, 0)


	#first_color = Colorful(pdb.gimp_context_get_foreground())
	#second_color = Colorful(pdb.gimp_context_get_background())
	first_color = Colorful(args['color_start'])
	second_color = Colorful(args['color_end'])

	#pdb.gimp_message("contrast ratio = {}".format(first_color.contrast_ratio(second_color)))

	for index, vectors in enumerate(tree.vectors):
		size = 3 #((tree.max_depth-index) * 2) + 3
		pdb.gimp_context_set_brush_size(size)

		amount = float(index)/float(tree.max_depth)
		first_color.blend(second_color, amount)
		first_color.set_foreground()
		
		pdb.gimp_drawable_edit_stroke_item(layer, vectors)
		#tools[current_tool](layer, len(coords), coords)
		





plugin = PythonFu(
	title = 'Fractal Tree',
	icon = os.path.join(this_directory, 'icons', 'draw-spiral-2-32x32.png'),
	description = 'Draw a fractal tree',
	author = 'Keith Drakard',
	date = '2019',
	menu = '<Image>/Filters/Render/Fractals/_Fractal Tree...',

	dialog_width = 500,
	tabs = ['Initial Settings', 'Per Iteration'],
	widgets = [
		{
			'variable'	: 'base_x',
			'label'		: 'X Base',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image width % used to determine where the tree starts to grow up from.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 50,
		},
		{
			'line'		: 1,
			'variable'	: 'base_y',
			'label'		: 'Y Base',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image height % used to determine where the tree starts to grow up from.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 100,
			#'position'	: (0,1),
		},
		{
			'variable'	: 'length',
			'label'		: 'Branch Length',
			'tooltip'	: 'Initial length in pixels of the first branch (trunk).',
			'type'		: IntEntry,
			'default'	: 150,
			'width'		: 120,
		},
		{
			'variable'	: 'color_start',
			'label'		: 'Start Color',
			'tooltip'	: 'Initial color before any fading occurs.',
			'type'		: ColorPicker,
			'default'	: FOREGROUND,
		},
		{
			'line'		: 3,
			'variable'	: 'color_end',
			'label'		: 'End Color',
			'tooltip'	: 'Final color of the tree branches.',
			'type'		: ColorPicker,
			'default'	: BACKGROUND,
		},

		{
			'tab'		: 2,
			'variable'	: 'branches',
			'label'		: 'Branches',
			'label_width' : 140,
			'tooltip'	: '',
			'type'		: IntSlider,
			'range'		: (0,6),
			'step'		: (1,1),
			'default'	: 2,
		},
		{
			'variable'	: 'angle',
			'label'		: 'Branch Angle',
			'label_width' : 140,
			'markup'	: '{} ({}°)',
			'tooltip'	: '',
			'type'		: IntSlider,
			'range'		: (0,180),
			'default'	: 45,
		},
		{
			'variable'	: 'decrease',
			'label'		: 'Decrease Branches By',
			'label_width' : 140,
			'markup'	: '{} ({}%)',
			'tooltip'	: '',
			'type'		: IntSlider,
			'range'		: (1,100),
			'default'	: 33,
		},
		{
			'variable'	: 'max_depth',
			'label'		: 'Iterations',
			'label_width' : 140,
			'tooltip'	: '',
			'type'		: IntSlider,
			'range'		: (1,10),
			'step'		: (1,1),
			'default'	: 5,
		},
	],
	help_text = {
		'label' : ('Draws a tree ala https://natureofcode.com/book/chapter-8-fractals/#85-trees - set branches or branch angle to zero to randomize either parameter.'),
	},
	code_function = FractalTreeWrapper
)

plugin.main()
