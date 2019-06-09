#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Tile Layer v0.1
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
# Automates the steps in https://www.instructables.com/id/Making-Images-seamless-horizontally-or-vertically-/
# ie. tiles a layer in a single direction, unlike the default "Tile Seamless" filter which forces both directions at once
#


# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)

sys.stderr = open(this_directory + 'gimpfu_debug.txt', 'a')

from classes.mygtk import *


class TileLayer(object):
	def __init__(self, args):

		image, layer, args = args
		
		self.image = image

		if not pdb.gimp_drawable_is_layer(layer):
			layer = pdb.gimp_image_get_active_layer(self.image)
			if not layer:
				raise MyError("Please select a layer")


		#pdb.gimp_image_undo_group_start(self.image)
		#pdb.gimp_context_push()
		pdb.gimp_context_set_defaults()		# black foreground, white background?


		self.layer = pdb.gimp_layer_copy(layer, True) # work on a copy of the layer
		pdb.gimp_image_insert_layer(self.image, self.layer, None, pdb.gimp_image_get_item_position(self.image, layer) - 1)
		self.layer.name = layer.name + ' (Tileable)'

		self.width, self.height = self.layer.width, self.layer.height
		self.offx, self.offy = self.layer.offsets
		
		self.direction = args['direction']

		if self.direction == 0:
			aslice = (self.width/100) * args['size']
			names = [ 'Right', 'Left', 'Demo Tiles' ]
			resize = [ self.width - aslice, self.height, -aslice/2, 0 ]
			translate = [ self.width - aslice, 0, -self.width + aslice, 0 ]

		else:
			aslice = (self.height/100) * args['size']
			names = [ 'Bottom', 'Top', 'Demo Tiles' ]
			resize = [ self.width, self.height - aslice, 0, -aslice/2 ]
			translate = [ 0, self.height - aslice, 0, -self.height + aslice ]



		#pdb.gimp_image_undo_freeze(self.image)
		#pdb.gimp_image_undo_thaw(self.image)

		pdb.gimp_progress_init("Tiling layer...", None)

		layer1 = self.copy_chunk(aslice)
		layer1.name = 'Tiling: '+names[0]+' Blend'
		layer2 = self.copy_chunk(-aslice)
		layer2.name = 'Tiling: '+names[1]+' Blend'

		# crop the layer edges
		pdb.gimp_layer_resize(self.layer, resize[0], resize[1], resize[2], resize[3])
		pdb.gimp_layer_resize(layer1, resize[0], resize[1], resize[2], resize[3])
		pdb.gimp_layer_resize(layer2, resize[0], resize[1], resize[2], resize[3])

		# combine the edge/masks
		if args['merge']:
			merged = pdb.gimp_image_merge_down(self.image, layer1, CLIP_TO_BOTTOM_LAYER)
			merged = pdb.gimp_image_merge_down(self.image, merged, CLIP_TO_BOTTOM_LAYER)

		# demo the tiling
		if args['merge'] and args['demo']:
			for i in range(2):
				demo = pdb.gimp_layer_copy(merged, True)
				pdb.gimp_image_insert_layer(self.image, demo, None, pdb.gimp_image_get_item_position(self.image, merged) - (i+1))
				pdb.gimp_layer_translate(demo, translate[i*2], translate[(i*2)+1])

			demo = pdb.gimp_image_merge_down(self.image, demo, CLIP_TO_IMAGE)
			demo.name = names[2]



		# house keeping; restore context, wrap the undo group, make sure we display our work and close the progress bar
		#pdb.gimp_context_pop()
		#pdb.gimp_image_undo_group_end(self.image)
		#pdb.gimp_displays_flush()
		#pdb.gimp_progress_end()




	def copy_chunk(self, aslice):

		if self.direction == 0:
			x0 = 0 if aslice >= 0 else self.width + aslice
			x1 = self.width - aslice if aslice >= 0 else 0
			
			select = [ x0 + self.offx, self.offy, (x0 + abs(aslice) + self.offx), self.height ]
			translate = [ x1 - x0, 0 ]
			resize = [ x1, 0 ]
			gradient = [ (x1 - min(0, aslice)), self.offy, (x1 - min(0, aslice)) + aslice, self.offy ]

		else:
			y0 = 0 if aslice >= 0 else self.height + aslice
			y1 = self.height - aslice if aslice >= 0 else 0
			
			select = [ self.offx, y0 + self.offy, self.width, (y0 + abs(aslice) + self.offy) ]
			translate = [ 0, y1 - y0 ]
			resize = [ 0, y1 ]
			gradient = [ self.offx, (y1 - min(0, aslice)), self.offx, (y1 - min(0, aslice)) + aslice ]
			

		# copy one bit of the base layer
		pdb.gimp_image_select_rectangle(self.image, CHANNEL_OP_REPLACE, select[0],select[1], select[2],select[3])
		pdb.gimp_edit_copy(self.layer)
		layer_id = pdb.gimp_edit_paste(self.layer, False)

		# move it to the other side
		pdb.gimp_layer_translate(layer_id, translate[0],translate[1])
		
		# stop floating and resize it to the base dimensions
		pdb.gimp_floating_sel_to_layer(layer_id)
		pdb.gimp_layer_resize(layer_id, self.width, self.height, resize[0],resize[1])
		
		# add the layer mask which does the actual blending
		mask_id = pdb.gimp_layer_create_mask(layer_id, ADD_WHITE_MASK)
		pdb.gimp_layer_add_mask(layer_id, mask_id)
		pdb.gimp_drawable_edit_gradient_fill(mask_id, GRADIENT_LINEAR, 0, False,0,0.0, False, gradient[0],gradient[1], gradient[2],gradient[3])

		return layer_id


##### end of the real code #####


plugin = PythonFu(
	title = 'Layer Tiling',
	icon = os.path.join(this_directory, 'icons', 'view-calendar-week-32x32.png'),
	description = 'Creates a tileable version of the current layer',
	author = 'Keith Drakard',
	date = '2019',
	menu = '<Image>/Layer/_Tiling...',
	widgets = [
		{
			'variable'	: 'direction',
			'label'		: 'Direction', 
			'tooltip'	: 'Which direction will this layer be tiled in?', 
			'type'		: DropDown,
			'options'	: ('Horizontal', 'Vertical'),
			'default'	: 0,
		},
		{
			'line'		: 1,
			'variable'	: 'size',
			'label'		: 'Edge',
			'markup'	: '{} ({:d}%)',
			'tooltip'	: 'What % of the layer dimension will be used to blend each edge?',
			'type'		: IntSlider,
			'range'		: (1,50),
			'default'	: 33,
		},
		{
			'variable'	: 'merge',
			'label'		: 'Merge Working Layers', 
			'tooltip'	: 'Unset this in order to preserve the working layers and so alter the masks manually.',
			'type'		: Toggle,
			'default'	: True,
		},
		{
			'line'		: 2,
			'variable'	: 'demo',
			'label'		: 'Make a Demo Layer', 
			'tooltip'	: 'Copies the merged tile to either side so you can quickly see what the join looks like.',
			'type'		: Toggle,
			'default'	: True,
		},
	],
	help_text = {
		'label' : ('Working on a copy of the currently selected layer, this plugin then copies each relevant edge and switches it to the other side.', 'It next applies a linear gradient to each edge copy to blend it into the layer below.', 'Finally, the newly created layers are cropped to remove the unblended portions of each edge.', 'Note: a) this obviously results in a smaller layer than the original, and b) you\'ll probably still need to postprocess the tile for a perfect join.'), 
		'markup' : '{}\n\n{}\n\n{}\n\n<i>{}</i>'
	},
	connect = [
		{ 'key': 'merge', 'signal': TOGGLED, 'does': ON_OFF, 'controls': 'demo' },
	],
	code_function = TileLayer
)

plugin.main()
