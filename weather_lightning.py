#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Weather - Lightning v0.1
# 
# Copyright 2019, Keith Drakard; Released under the 3-Clause BSD License
# See https://opensource.org/licenses/BSD-3-Clause for details
#
# Change Log
# ----------
# 0.1: Initial release
#
# ------------------------------------------------------------------------------
# Weather effect; lightning


# console crib...
#
# layer = pdb.gimp_image_get_active_drawable(gimp.image_list()[0])
# 

# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)

sys.stderr = open(this_directory + 'gimpfu_debug.txt', 'a')

from classes.mygtk import *
from classes.noise import *
from classes.point import *
import random



class LightningPath(object):
	def __init__(self, image, start, end, depth=1):
		self.image = image
		self.start, self.end = start, end
		self.depth = max(1, depth)

		# NOTE length is the as-the-crow-flies distance AND NOT the length of the actual path/beziers
		self.length = int(self.end.distance_from(self.start))
		self.angle = self.end.angle_of(self.start)
		
		# minimum possible starting point for branches
		self.branch_point = self.length - (self.length / (self.depth+1))

		self.path = []

		noise_defaults = [
			(8, 2.5, 0.40, 0.4, 200, self.length/2),
			(8, 2.0, 0.55, 0.2, 200, self.length)
		]
		pick = min(self.depth-1, 1)
		self.octaves, self.lacunarity, self.gain, self.scale, self.amplitude, self.hgrid = noise_defaults[pick]

		self.brush_size = 0
	pass

	''' adds two paths together; does NOT check that they are continuous, in the same image, nor of the same depth '''
	def __add__(self, other):
		obj = LightningPath(self.image, self.start, other.end, self.depth)
		obj.length = self.length + other.length
		obj.path = self.path + other.path
		return obj
	pass

	''' because random.choice(path) only returns the Point object of a path and I want the index too '''
	def random_point_along_path(self):
		index = random.randint(0, len(self.path)-1)
		return index, self.path[index]
	pass

	''' brush details for this depth '''
	def set_brush(self):
		if self.brush_size == 0:
			self.brush_size = int(self.image.width/150)
		if self.depth > 1:
			self.brush_size = max(1, int(self.brush_size / self.depth))

		pdb.gimp_context_set_paint_method("gimp-paintbrush")	# make sure we have the right tool selected in this context else gimp errors when you have a non-painting tool selected
		pdb.gimp_context_set_brush("1. Pixel")
		pdb.gimp_context_set_brush_size(self.brush_size)
		pdb.gimp_context_set_brush_hardness(0.75)
	pass

	''' makes a noisy wave along a straight line '''
	def make_path(self):
		pn = PerlinNoise(self.octaves, 0.1, self.scale)
		for i in xrange(self.length):
			n = int(normalize(pn.fractal(i, self.hgrid, self.lacunarity, self.gain)) * self.amplitude) - self.amplitude/2
			self.path.append(Point(i,n))
	pass
			
	''' rotates that wave to follow our real start->end line '''
	def rotate_path(self):
		for index, item in enumerate(self.path):
			# rotate x,y around the origin - https://en.wikipedia.org/wiki/Rotation_matrix
			x = int(item.x * math.cos(self.angle) - item.y * math.sin(self.angle))
			y = int(item.x * math.sin(self.angle) + item.y * math.cos(self.angle))
			# translate x,y according to the offset
			self.path[index] = Point(x + self.start.x, y + self.start.y)
	pass

	''' trebles each of the path coords so gimp can draw the curve '''
	def make_beziers(self):
		self.beziers = []
		for i in self.path:
			# add this to our curve
			self.beziers.extend([i.x,i.y, i.x,i.y, i.x,i.y])
	pass

	''' plot the bezier curve as a gimp path '''
	def draw_beziers_path(self):
		vectors = pdb.gimp_vectors_new(self.image, "Lightning Path")
		pdb.gimp_image_insert_vectors(self.image, vectors, None, 0)
		if len(self.beziers) > 6:
			pdb.gimp_vectors_stroke_new_from_points(vectors, VECTORS_STROKE_TYPE_BEZIER, len(self.beziers), self.beziers, False)	
		return vectors
	pass

	''' and draw the bezier curve - solid color, no messing around with gradient overlays etc '''
	def draw_beziers(self, group):
		layer = pdb.gimp_layer_new(self.image, self.image.width, self.image.height, RGBA_IMAGE, "Main Bolt", 100.00, LAYER_MODE_NORMAL)
		pdb.gimp_image_insert_layer(self.image, layer, group, 0)
		self.set_brush()
		self.make_beziers()
		vectors = self.draw_beziers_path()
		pdb.gimp_drawable_edit_stroke_item(layer, vectors)
		pdb.gimp_image_remove_vectors(self.image, vectors)
		return layer
	pass

	def draw_beziers_lighting(self, group):
		pdb.gimp_progress_set_text("Drawing main bolt (lighting) ...")
		pdb.gimp_image_undo_freeze(self.image)

		layerc = self.draw_beziers(group)

		layer1 = pdb.gimp_layer_copy(layerc, True)
		layer2 = pdb.gimp_layer_copy(layerc, True)
		layer3 = pdb.gimp_layer_copy(layerc, True)
		layer4 = pdb.gimp_layer_copy(layerc, True)
		pdb.gimp_image_remove_layer(self.image, layerc)

		pdb.gimp_image_insert_layer(self.image, layer4, group, 1)
		pdb.gimp_image_insert_layer(self.image, layer3, group, 1)
		pdb.gimp_image_insert_layer(self.image, layer2, group, 1)
		pdb.gimp_image_insert_layer(self.image, layer1, group, 1)
		
		pdb.plug_in_gauss(self.image, layer1, 10,10, 0)
		pdb.plug_in_gauss(self.image, layer2, 20,20, 0)
		pdb.plug_in_gauss(self.image, layer3, 35,35, 0)
		pdb.plug_in_gauss(self.image, layer4, 70,70, 0)
		
		pdb.gimp_drawable_brightness_contrast(layer2, 0.3, 0.3)
		pdb.gimp_drawable_brightness_contrast(layer3, -0.2, 0)
		pdb.gimp_drawable_brightness_contrast(layer4, -0.3, 0)

		layer1.mode = LAYER_MODE_HARDLIGHT
		layer = pdb.gimp_image_merge_down(self.image, layer1, CLIP_TO_IMAGE)
		layer = pdb.gimp_image_merge_down(self.image, layer, CLIP_TO_IMAGE)
		layer = pdb.gimp_image_merge_down(self.image, layer, CLIP_TO_IMAGE)
		layer.name = "Main Bolt (Underlay)"
		
		# take our now single lighting layer and do some more blurry things to it

		layer2 = pdb.gimp_layer_copy(layer, True)
		layer3 = pdb.gimp_layer_copy(layer, True)

		pdb.gimp_image_insert_layer(self.image, layer2, group, 2)
		pdb.gimp_image_insert_layer(self.image, layer3, group, 3)
		
		pdb.plug_in_mblur(self.image, layer2, 2, 100, 90, self.start.x, self.start.y)
		pdb.plug_in_mblur(self.image, layer3, 2, 250, 90, self.start.x, self.start.y)
		
		pdb.plug_in_whirl_pinch(self.image, layer2, 0.0, -1.0, 1.2)
		pdb.plug_in_whirl_pinch(self.image, layer3, 0.0, -1.0, 1.2)
		
		pdb.gimp_drawable_brightness_contrast(layer2, -0.5, -0.1)
		pdb.gimp_drawable_brightness_contrast(layer2, -0.3, 0)
		pdb.gimp_drawable_brightness_contrast(layer3, -0.5, 0)
		pdb.gimp_drawable_brightness_contrast(layer3, -0.5, 0)
		pdb.gimp_drawable_brightness_contrast(layer3, -0.2, 0) # yes, you need to repeat b/c adjustments if you want to change a layer that much
		
		layer2 = pdb.gimp_image_merge_down(self.image, layer2, CLIP_TO_IMAGE)
		layer2.name = "Main Bolt (Underlay 2)"
		layer2.opacity = 40.0

		pdb.gimp_image_undo_thaw(self.image)

		return layer
	pass


	''' paint the plain x,y coords as a gradient pixel by pixel - looks better than a solid stroke but takes longer '''
	def draw_path(self, group):
		pdb.gimp_progress_set_text("Drawing child strokes ...")
		pdb.gimp_image_undo_freeze(self.image)

		layer = pdb.gimp_layer_new(self.image, self.image.width, self.image.height, RGBA_IMAGE, "Side Bolt", 100.00, LAYER_MODE_NORMAL)
		pdb.gimp_image_insert_layer(self.image, layer, group, 0)
		self.set_brush()

		for index, item in enumerate(self.path):
			percent = float(index)/float(self.length)
			pdb.gimp_context_set_opacity((1 - percent) * 100)
			pdb.gimp_paintbrush(layer, 0, 2, (item.x,item.y), PAINT_CONSTANT, 0)
			#pdb.gimp_paintbrush(layer, 0, 2, (item.x,item.y), PAINT_CONSTANT, 0)
			#pdb.gimp_paintbrush(layer, 0, 2, (item.x,item.y), PAINT_CONSTANT, 0)
			pdb.gimp_progress_update(percent)

		pdb.gimp_image_undo_thaw(self.image)

		return layer
	pass




def WeatherLightningWrapper(args):
	
	image, layer, args = args


	pdb.gimp_progress_init("Drawing lighting ...", None)

	#random.seed(seed)
	width = image.width
	height = image.height

	start = Point(width * args['start_x']/100, height * args['start_y']/100)
	mid = Point(width * args['mid_x']/100, height * args['mid_y']/100)
	end = Point(width * args['end_x']/100, height * args['end_y']/100)

	n_main = max(1, min(10, int(args['n_main']))) # between 1-10 main bolts
	n_side = max(0, min(20, int(args['n_side']))) # and 0-20 side bolts


	side_points = []

	group = gimp.GroupLayer(image)
	group.name = "Lightning"
	pdb.gimp_image_insert_layer(image, group, None, 0)

	for i in range(n_main):
		pdb.gimp_progress_set_text("Drawing main bolt(s) ...")
		path1 = LightningPath(image, start, mid)
		path1.make_path()
		path1.rotate_path()
		
		if args['move_end_point_a_bit']:
			end.move_point(width/20, height/20) # 5% wiggle room

		path2 = LightningPath(image, mid, end)
		path2.make_path()
		path2.rotate_path()
		
		main_path = path1 + path2

		size_mod = random.choice([120,150,180,200])
		main_path.brush_size = int(image.width/size_mod)

		pdb.gimp_context_set_foreground(args['color_bolt'])
		layer1 = main_path.draw_beziers(group)

		pdb.gimp_context_set_foreground(args['color_lighting'])
		layer2 = main_path.draw_beziers_lighting(group)

		# need to pick points/angles here from each bolt for the side ones
		for i in range(n_side):
			j, side_start = main_path.random_point_along_path()
			side_next = main_path.path[j+1]

			angle = side_next.angle_of(side_start)
			distance = random.randint(int(main_path.length/15), int(main_path.length/3))

			#debug.write("{}: {} {} {}\n".format(i, main_path.angle, angle, distance))

			side_end = side_start.make_point(distance, angle)
			side_end.check_bounds(width, height)

			#debug.write("{}: {} to {} @ {} {}\n".format(i, side_start, side_end, distance, angle))
			side_points.append((side_start, side_end))



	pdb.gimp_context_set_foreground(args['color_bolt']) # reset after doing the main bolt lighting

	random.shuffle(side_points)

	for i in range(0, n_side): # still only picking n_side items from a list n_main*n_side long 

		start, end = side_points[i]
		
		side_path = LightningPath(image, start, end, 2)
		side_path.make_path()
		side_path.rotate_path()

		layer1 = side_path.draw_path(group)
		
		layer2 = pdb.gimp_layer_copy(layer1, True)
		layer2.mode = LAYER_MODE_HARDLIGHT
		pdb.gimp_image_insert_layer(image, layer2, None, 1)
		pdb.plug_in_gauss(image, layer2, 10,10, 0)
		pdb.gimp_brightness_contrast(layer2, 0, 123)








plugin = PythonFu(
	title = 'Lightning',
	icon = os.path.join(this_directory, 'icons', 'draw-spiral-2-32x32.png'),
	description = 'Draws a bolt of lightning',
	author = 'Keith Drakard',
	date = '2019',
	menu = '<Image>/Filters/Render/Nature/_Lightning...',

	dialog_width = 500,
	widgets = [
		{
			'variable'	: 'start_x',
			'label'		: 'X Start',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image width % used to determine where the bolt starts from.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 10,
		},
		{
			'line'		: 1,
			'variable'	: 'start_y',
			'label'		: 'Y Start',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image height % used to determine where the bolt starts from.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 50,
		},

		{
			'variable'	: 'mid_x',
			'label'		: 'X Mid',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image width % used to determine where the bolt bends.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 40,
		},
		{
			'line'		: 2,
			'variable'	: 'mid_y',
			'label'		: 'Y Mid',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image height % used to determine where the bolt bends.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 40,
		},

		{
			'variable'	: 'end_x',
			'label'		: 'X End',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image width % used to determine where the bolt goes to.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 90,
		},
		{
			'line'		: 3,
			'variable'	: 'end_y',
			'label'		: 'Y End',
			'markup'	: '{} ({}%)',
			'tooltip'	: 'Image height % used to determine where the bolt goes to.',
			'type'		: IntSlider,
			'range'		: (0,100),
			'default'	: 60,
		},

		{
			'variable'	: 'n_main',
			'label'		: 'Main Bolts',
			'tooltip'	: 'Number of big bolts.',
			'type'		: IntSlider,
			'range'		: (1,10),
			'default'	: 1,
		},
		{
			'variable'	: 'n_side',
			'label'		: 'Side Bolts',
			'tooltip'	: 'Number of little bolts...',
			'type'		: IntSlider,
			'range'		: (0,20),
			'default'	: 0,
		},

		{
			'variable'	: 'move_end_point_a_bit',
			'label'		: 'Randomize end point',
			'tooltip'	: 'Move the end X,Y co-ords slightly for each main bolt.',
			'type'		: Toggle,
			'default'	: True,
		},
		{
			'variable'	: 'seed',
			'label'		: 'Random Seed',
			'tooltip'	: '',
			'type'		: IntEntry,
			'default'	: 0,
		},
		{
			'variable'	: 'color_bolt',
			'label'		: 'Bolt Color',
			'tooltip'	: 'Color of the main (and side) bolt.',
			'type'		: ColorPicker,
			'default'	: FOREGROUND,
		},
		{
			'variable'	: 'color_lighting',
			'label'		: 'Lighting Color',
			'tooltip'	: 'The glow that makes this more than just a wiggly line.',
			'type'		: ColorPicker,
			'default'	: BACKGROUND,
		},

	],
	help_text = {
		'label' : ('Draws a bolt of lightning.'),
	},
	code_function = WeatherLightningWrapper
)

plugin.main()

