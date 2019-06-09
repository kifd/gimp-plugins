#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Widgets v0.1
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
# Widget classes for gtk/gimpfu
#


# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)


import mygtk, gtk, gimp, gimpcolor, colorsys
pdb = gimp.pdb

JUSTIFY_LEFT	= gtk.JUSTIFY_LEFT
JUSTIFY_CENTER	= gtk.JUSTIFY_CENTER
JUSTIFY_RIGHT	= gtk.JUSTIFY_RIGHT

#from gimpenums import *

import logging





# easier to remember string constants available to calling plugins
TOGGLED			= 'toggled'
ON_OFF			= 'widget_link_activation_old'

FOREGROUND		= 1
BACKGROUND		= 0



class MyError(BaseException):
	def __init__(self, *args):
		#message, image = args

		gimp.message(args[0])
		dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=args[0])
		dlg.set_position(gtk.WIN_POS_CENTER)
		dlg.run()
		dlg.destroy()

		# house keeping
		try:
			gimp.pdb.gimp_context_pop()
		except RuntimeError:
			pass # no previous context push

		try:
			image = gimp.image_list()[0]
			gimp.pdb.gimp_image_undo_group_end(image)
		except RuntimeError:
			pass # no previous group start

		try:
			gimp.pdb.gimp_progress_end()
		except RuntimeError:
			pass # NOTE: this only in case, as unlike context & group, this seemingly doesn't get thrown if progress init wasn't called first

			
		gimp.pdb.gimp_displays_flush()
			





############################### Common Widget Class ##########################################################################################################################################


class GeneralWidget(object):
	def __init__(self, args):
		super(GeneralWidget, self).__init__()

		# note that not all these param defaults are used by all widgets
		self._width = args['width'] if 'width' in args else -1
		self._height = args['height'] if 'height' in args else -1

		self._label = args['label'] if 'label' in args else ''
		self._label_width = args['label_width'] if 'label_width' in args else 0
		self._markup = args['markup'] if 'markup' in args else '{}'
		self._tooltip = args['tooltip'] if 'tooltip' in args else ''
		self._range = args['range'] if 'range' in args else (0,100)
		self._step = args['step'] if 'step' in args else (1,10)
		self._default = args['default'] if 'default' in args else ''
		self._justify = args['justify'] if 'justify' in args else JUSTIFY_LEFT
		self._options = args['options'] if 'options' in args else ()


		# connects gui class function (widget_link_*) to a widget
		if 'connect' in args:
			# TODO: cope with multiple...
			signal, connecting_function, key, target = args['connect']
			self.connect(signal, connecting_function, key, target)

		pass




	def assert_integer(self, value):
		try:
			value = int(value)
		except ValueError:
			value = 0
		return value


	# allows dynamic resizing of elements to fill as much space as allowed
	# https://stackoverflow.com/a/3672395
	def size_request(self, l, s, width=None, height=None):
		if not width:
			width = s.width -1
		if not height:
			height = -1

		l.set_size_request(width, height)

	def emit_signal(self, button, signal):
		self.emit(signal)





############################### Dropdown Select ##################################

class DropDown(GeneralWidget, gtk.HBox):
	def __init__(self, args):
		super(DropDown, self).__init__(args)
		#self.connect('size-allocate', self.size_request)
		
		self._default = args['default'] if 'default' in args else 0
		
		self.set_spacing(4)
		self.set_homogeneous(False)
		self.set_tooltip_text(self._tooltip)

		self.label = gtk.Label()
		self.label.set_alignment(0, 0.5)
		self.label.set_markup(self._markup.format(self._label))
		
		self.dropdown = gtk.combo_box_new_text()
		for item in self._options:
			self.dropdown.append_text(item)

		self.dropdown.set_size_request(120, 30)
		self.dropdown.connect('changed', self.changed)
		self.dropdown.set_active(self._default)

		self.add(self.label)
		self.add(self.dropdown)
		
	def changed(self, *data):
		#widget, variable = data
		#variable = self.get_value()
		pass

	def get_value(self):
		return self.dropdown.get_active()

	def set_value(self, value):
		self.dropdown.set_active(value)



############################### Slider ##################################

class Slider(GeneralWidget, gtk.HBox):
	def __init__(self, args):
		super(Slider, self).__init__(args)

		self._markup = args['markup'] if 'markup' in args else '{} ({})'
		self._default = args['default'] if 'default' in args else 50

		self.connect('size-allocate', self.size_request)
		
		self.set_spacing(4)
		self.set_homogeneous(False)
		if self._tooltip != '':
			self.set_tooltip_text(self._tooltip)

		self.label = gtk.Label()
		self.label.set_alignment(0, 0.5)
		self.label.set_markup(self._markup.format(self._label, self._default))
		if self._label_width > 0:
			self.label.set_size_request(self._label_width, -1)

		
		self.slider = gtk.HScale()
		self.slider.set_draw_value(False)
		self.slider.set_range(self._range[0], self._range[1])
		self.slider.set_increments(self._step[0], self._step[1])
		self.slider.set_value(self._default)

		self.slider.connect('size-allocate', self.size_request)
		self.slider.connect('value-changed', self.changed)
		self.slider.connect('value-changed', self.update_label, self._label, self._markup)
		
		self.add(self.label)
		self.add(self.slider)
		
	def changed(self, *data):
		#self.set_value(self.get_value())
		pass

	def update_label(self, *data):
		widget, _label, _markup = data
		self.label.set_markup(_markup.format(_label, self.get_value()))

	def get_value(self):
		return self.slider.get_value()

	def set_value(self, value):
		self.slider.set_value(value)



class IntSlider(Slider):
	def __init__(self, args):
		super(IntSlider, self).__init__(args)
		self.slider.set_digits(0)

	def get_value(self):
		return self.assert_integer(super(IntSlider, self).get_value())



############################### Buttons (Toggle and Click) ##################################

class Toggle(GeneralWidget, gtk.ToggleButton):
	def __init__(self, args):
		super(Toggle, self).__init__(args)

		self._markup = args['markup'] if 'markup' in args else '<b>{}</b>'
		self._default = args['default'] if 'default' in args else False

		self.set_size_request(150, 30)
		self.set_tooltip_text(self._tooltip)
		self.connect('toggled', self.changed, self._label, self._markup)
		self.emit('toggled')
		self.set_active(self._default)

	def changed(self, *data):
		widget, _label, _markup = data
		if widget.get_active():					# self.get_value() ?
			label = widget.get_child()
			label.set_markup(_markup.format(_label))
		else:
			widget.set_label(_label)

	def get_value(self):
		return self.get_active()

	def set_value(self, value):
		self.set_active(value)

	def disable(self):
		self.set_sensitive(False)
		if self.get_value():
			self.set_active(False)

	def enable(self):
		self.set_sensitive(True)



class Button(GeneralWidget, gtk.Button):
	def __init__(self, args):
		super(Button, self).__init__(args)

		self.set_label(self._label) # plain label first
		label = self.get_child()
		label.set_markup_with_mnemonic(self._markup.format(self._label))

		self.set_use_underline(True)
		self.set_size_request(70, 30)
		self.set_tooltip_text(self._tooltip)

		#if response:
		#	self.connect('clicked', self.emit_signal, response)


############################### Text Entry ##################################

class Entry(GeneralWidget, gtk.HBox):
	def __init__(self, args):
		super(Entry, self).__init__(args)
		
		self.connect('size-allocate', self.size_request, self._width, self._height)
		
		self.set_spacing(4)
		self.set_homogeneous(False)
		if self._tooltip != '':
			self.set_tooltip_text(self._tooltip)

		self.label = gtk.Label()
		self.label.set_alignment(0, 0.5)
		self.label.set_markup(self._markup.format(self._label))

		if self._label_width > 0:
			self.label.set_size_request(self._label_width, -1)
		
		self.entry = gtk.Entry()
		self.entry.set_editable(True)
		self.entry.set_activates_default(True)
		self.entry.connect('size-allocate', self.size_request)

		self.set_value(self._default)
		
		self.add(self.label)
		self.add(self.entry)
		

	def get_value(self):
		return self.entry.get_chars(0, -1)

	def set_value(self, value):
		self.entry.delete_text(0, -1)
		self.entry.insert_text(str(value))


class IntEntry(Entry):
	def __init__(self, args):
		super(IntEntry, self).__init__(args)

	def get_value(self):
		return self.assert_integer(super(IntEntry, self).get_value())



############################### Text Display ##################################

class InfoLabel(GeneralWidget, gtk.Label):
	def __init__(self, args):
		super(InfoLabel, self).__init__(args)

		if isinstance(self._label, str):
			self.set_markup(self._markup.format(self._label))

		# TODO: copy this to the general widget so that all of them can use this
		elif isinstance(self._label, (tuple, list)):
			diff = len(self._label) - self._markup.count('{}')
			# won't cope with correcting major differences in fancier formatting, so don't do that...
			if diff > 0:
				self._markup = self._markup + ('\n\n{}' * diff)

			self.set_markup(self._markup.format(*self._label))

		self.set_line_wrap(True)
		self.set_justify(self._justify)
		self.connect('size-allocate', self.size_request)
		
	#def get_value(self):
	#	return self.get_label()



############################### Pickers ##################################

class Picker(GeneralWidget, gtk.HBox):
	def __init__(self, args):
		super(Picker, self).__init__(args)
		
		self.connect('size-allocate', self.size_request, self._width, self._height)
		
		self.set_spacing(4)
		self.set_homogeneous(False)
		if self._tooltip != '':
			self.set_tooltip_text(self._tooltip)

		self.label = gtk.Label()
		self.label.set_alignment(0, 0.5)
		self.label.set_markup(self._markup.format(self._label))

		if self._label_width > 0:
			self.label.set_size_request(self._label_width, -1)
		
		#self.picker = gtk.Entry()
		#self.entry.set_editable(True)
		#self.entry.set_activates_default(True)
		#self.entry.connect('size-allocate', self.size_request)

		self.add(self.label)
		
	#def get_value(self):
	#	return self.picker.get_chars(0, -1)

	#def set_value(self, value):
	#	self.entry.delete_text(0, -1)
	#	self.entry.insert_text(str(value))


# my cut down version of the gimpui.ColorSelector until that works in windows again
# (see https://gitlab.gnome.org/GNOME/gimp/issues/1438 - first reported June 2018)

class ColorPicker(Picker):
	def __init__(self, args):
		super(ColorPicker, self).__init__(args)

		self.picker = gtk.ColorButton()
		self.add(self.picker)


	def gimp_to_gdk(self, gimp_rgb):
		r = float(gimp_rgb[0])/255.0
		g = float(gimp_rgb[1])/255.0
		b = float(gimp_rgb[2])/255.0
		return gtk.gdk.Color(r,g,b)

	def gdk_to_gimp(self, value):
		value = value.to_string().lstrip('#')
		#logging.warn(value)
		(r,g,b) = tuple(int(value[i:i+2], 16) for i in range(0, 12, 4))
		(r,g,b) = (r/255.0, g/255.0, b/255.0)
		return (r,g,b)

	def get_value(self):
		(r,g,b) = self.gdk_to_gimp(self.picker.get_color())
		return gimpcolor.RGB(r,g,b)
		
	def set_value(self, value):
		#logging.warn(value)
		if isinstance(value, int):
			if value == FOREGROUND:
				value = pdb.gimp_context_get_foreground()
			elif value == BACKGROUND:
				value = pdb.gimp_context_get_background()

		if isinstance(value, gimpcolor.RGB):
			value = self.gimp_to_gdk(value)
		elif isinstance(value, dict) and 'hsv' in value:
			r,g,b = colorsys.hsv_to_rgb(value['hsv'][0], value['hsv'][1], value['hsv'][2])
			value = gtk.gdk.Color(r,g,b)
			
		else:
			raise MyError("Color type {} not dealt with properly!".format(type(value)))

		try:
			self.picker.set_color(value)
		except TypeError:
			value = gtk.gdk.color_parse('red')
			self.picker.set_color(value)


