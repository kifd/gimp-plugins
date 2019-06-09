#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Point v0.1
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
# Useful 2d coord related functions - does nothing on its own
#

import math, random
from gimpfu import *


class Point(object):
	def __init__(self, x=0.0, y=0.0):
		self.x, self.y = x, y
		self.padding = 0.05 # image boundary minimum distance (%)

	def __str__(self):
		return "({0},{1})".format(int(self.x), int(self.y))

	def __add__(self, other):
		self.x = self.x + other.x
		self.y = self.y + other.y
		return self

	def __sub__(self, other):
		self.x = self.x - other.x
		self.y = self.y - other.y
		return self


	def distance_from(self, other):
		return ((self.x - other.x)**2 + (self.y - other.y)**2) ** 0.5

	def angle_of(self, other):
		return math.atan2(self.y - other.y, self.x - other.x)

	def make_point(self, radius, radians):
		obj = Point()
		obj.x = self.x + (radius * math.cos(radians))
		obj.y = self.y + (radius * math.sin(radians))
		return obj


	def rotate(self, radians, origin=None):
		if not origin: origin = Point()
		
		c = math.cos(radians)
		s = math.sin(radians)

		self-= origin

		new_x = (self.x * c) - (self.y * s)
		new_y = (self.x * s) + (self.y * c)
		self.x = new_x
		self.y = new_y

		self+= origin


	def reflect(self, origin=None):
		if not origin: origin = Point()
		self.reflect_x(origin)
		self.reflect_y(origin)

	def reflect_x(self, origin=None):
		if not origin: origin = Point()
		self.x = 2 * origin.x - self.x

	def reflect_y(self, origin=None):
		if not origin: origin = Point()
		self.y = 2 * origin.y - self.y



	# not needed?
	def translate(self, xmod, ymod):
		self.x = self.x + xmod
		self.y = self.y + ymod


	def move_point(self, xmod, ymod):
		xmod, ymod = random.randint(-int(xmod), int(xmod)), random.randint(-int(ymod), int(ymod))
		self.translate(xmod, ymod)
		

	def check_bounds(self, max_x, max_y):
		padding_x, padding_y = (max_x * self.padding), (max_y * self.padding)
		self.x = max(0+padding_x, min(max_x-padding_x, self.x))
		self.y = max(0+padding_y, min(max_y-padding_y, self.y))

	def halfway_to(self, other):
		obj = Point()
		obj.x = int((self.x + other.x) / 2)
		obj.y = int((self.y + other.y) / 2)
		return obj

pass
