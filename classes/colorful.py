#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Colorful v0.1
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
# Useful color related functions - does nothing on its own
#

import os, sys, random, colorsys
from gimpfu import *



class Colorful(object):
	def __init__(self, rgba=None):
		self.rgba = rgba if rgba is not None else self.get_foreground()

		self.r = float(self.rgba[0]) / 255.0
		self.g = float(self.rgba[1]) / 255.0
		self.b = float(self.rgba[2]) / 255.0
		self.a = int(self.rgba[3]) # not used

 		self.get_luminance()
		#self.hls = list(colorsys.rgb_to_hls(self.r, self.g, self.b))
		#pdb.gimp_message("{} vs {}".format(self.hls, self.luminance))


	def __str__(self):
		return "({} {} {})".format(self.r, self.g, self.b)

		

	def get_foreground(self):
		return pdb.gimp_context_get_foreground()

	def set_foreground(self):
		self.rgba = tuple([self.r,self.g,self.b, self.a])
		return pdb.gimp_context_set_foreground(self.rgba)


	# https://www.w3.org/TR/WCAG20/#relativeluminancedef
	def get_luminance(self):
		for v in [self.r, self.g, self.b]:
			if v <= 0.03928:
				v = v / 12.92
			else:
				v = math.pow(((v + 0.055) / 1.055), 2.4)
		self.luminance = (self.r * 0.2126) + (self.g * 0.7152) + (self.b * 0.0722)

	# http://www.w3.org/TR/WCAG20/#contrast-ratiodef
	def contrast_ratio(self, other):
		# returns 1.0 (no contrast) to 21.0 (max contrast); WCAG recommend a minimum of 3 - 4.5 for (AA), and at least 4.5 - 7 for (AAA) compliance
		return (max(self.luminance, other.luminance) + 0.05) / (min(self.luminance, other.luminance) + 0.05)

	# https://en.wikipedia.org/wiki/Linear_interpolation helper function
	def lerp(self, start, end, amount):
		return (1 - amount)*start + amount*end

	# changes one color somewhere towards another one
	def blend(self, other, amount):
		self.r = self.lerp(self.r, other.r, amount)
		self.g = self.lerp(self.g, other.g, amount)
		self.b = self.lerp(self.b, other.b, amount)
		
	def lighten(self, amount):
		white = Colorful([255,255,255, 255])
		self.blend(white, amount)

	def darken(self, amount):
		black = Colorful([0,0,0, 255])
		self.blend(black, amount)




