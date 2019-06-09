#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MyGTK v0.1
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
# My homebrewed gimpfu functions - does nothing on its own
#


# https://gitlab.gnome.org/GNOME/gimp/issues/1542
import os, sys
this_directory = os.path.dirname(os.path.realpath(__file__)) + os.sep
sys.path.append(this_directory)


from widgets import *
#from collections import OrderedDict, defaultdict

import gtk, gimp, gimpui, gobject, gimpshelf
pdb = gimp.pdb


from gimpenums import *
JUSTIFY_LEFT	= gtk.JUSTIFY_LEFT
JUSTIFY_CENTER	= gtk.JUSTIFY_CENTER
JUSTIFY_RIGHT	= gtk.JUSTIFY_RIGHT


#RUN_INTERACTIVE = 0
#RUN_NONINTERACTIVE = 2

import logging


class PythonFu(object):

	def __init__(self, *args, **kwargs):
		
		defaults = {
			'title'				: '', # human readable title of the plugin
			'description'		: '', # short description
			'author'			: '', # plugin author
			'date'				: '', # date (TODO: check if more than just year)
			'menu'				: '', # full menu path for now, including <Image> at the start and (underscored for key bind) label at the end

			'tabs'				: [], # list of tab titles
			'widgets'			: [], # list of widget dictionaries that make up the gtk gui
			'help_text'			: {}, # single InfoLabel widget that will be shown/hidden when the help button is clicked
			'code_function'		: None, # the real plugin code that the gtk wrapper calls

			'help'				: '', # (optional) short help text (else full help text)
			'copyright'			: '', # (optional) copyright holder (else author)
			'image_types'		: None, # (optional) image types the plugin works on (else all)
			'dialog_width'		: None, # (optional) requested size of the gtk gui (else min)
			'connect'			: [], # (optional) connects widgets together in fancy ways
		}
		for key, value in defaults.iteritems():
			setattr(self, key, value)

		for key, value in kwargs.iteritems():
			setattr(self, key, value)

		#logging.warn(self)

		self.proc_name = 'python-fu-' + self.title.lower().replace(' ', '_')
		self.proc_type = PLUGIN

		if self.help_text and not self.help:
			#help = help_text['markup'].format(help_text['label'])	# TODO: lists/multiple {}s
			self.help = "\n".join(self.help_text['label'])

		if not self.copyright:
			self.copyright = self.author

		if not self.image_types: #hasattr(self, 'image_types'):
			self.image_types = '*'	# TODO: note down the other possible types

		self.register_params = []	# the format we need for install_procedure
		self.param_defaults = {}	# a dictionary of key / default value for each param
		self.return_vals = []


		# TODO: fail if menu not valid
		_fields = self.menu.split('/')
		if _fields:
			if _fields[0] == '<Image>':
				self.register_params = [(PDB_INT32, 'run_mode', 'Run Mode'), (PDB_IMAGE, 'image', 'Image'), (PDB_DRAWABLE, 'drawable', 'Drawable')]
				pass

			self.menu_label = _fields.pop()
			self.menu_path = '/'.join(_fields)


		self.build_params(self.widgets)


	def build_params(self, widget_list):

		# TODO: check for required fields - variable / type / label / default
		for widget in widget_list:
			_type = PDB_INT32
			#if widget['type'] in (DropDown, IntSlider, Toggle):
			#	_type = PDB_INT32

			if 'variable' in widget.keys():
				key = widget['variable']
				_this_param = (_type, key, widget['label'])
				self.register_params.append(_this_param)
				self.param_defaults[key] = widget['default']
			
			elif 'repeats' in widget.keys():
				repeated_widgets = []
				for i in range(1, widget['repeats']+1):
					for subwidget in widget['repeat_this']:
						copy = {}
						for (key, value) in subwidget.iteritems():
							if isinstance(value, str):
								value = str.replace(value, '?', str(i))
							copy[key] = value
						repeated_widgets.append(copy)
						
				#logging.warn(repeated_widgets)
				self.build_params(repeated_widgets)







	def main(self):
		gimp.main(None, None, self.register, self.call_plugin)


	def register(self):
		gimp.install_procedure(self.proc_name, self.description, self.help, self.author, self.copyright, self.date, self.menu_label, self.image_types, self.proc_type, self.register_params, self.return_vals)
		gimp.menu_register(self.proc_name, self.menu_path)


	def call_plugin(self, proc_name, args):
		run_mode, image, drawable = args
		
		# load up previous settings from this gimp session
		proc_name = 'python-fu-save--' + proc_name
		defaults = gimpshelf.shelf[proc_name] if gimpshelf.shelf.has_key(proc_name) else self.param_defaults

		#logging.warn(defaults)
		pdb.gimp_image_undo_group_start(image)
		pdb.gimp_context_push()


		# replay the prior call
		if run_mode != RUN_INTERACTIVE:
			self.code_function((image, drawable, defaults))

		# or pop up the settings dialog and ask again
		else:
			gui = GeneralDialog(proc_name, defaults)
			gui.make_gui(
				title = self.title,
				icon_name = self.icon,
				width = self.dialog_width,
				tab_titles = self.tabs,
				widgets = self.widgets,
				help_text = self.help_text
			)

			for item in self.connect:
				gui.widgets[item['key']].connect(item['signal'], getattr(gui, item['does']), item['key'], item['controls'])
		
			gui.set_code_to_run(self.code_function, (image, drawable, gui.vars))
			gui.main()



		# house keeping; restore context, wrap the undo group, make sure we display our work and close the progress bar
		pdb.gimp_context_pop()
		pdb.gimp_image_undo_group_end(image)
		pdb.gimp_displays_flush()
		pdb.gimp_progress_end()

		


	pass









class GeneralDialog(gtk.Dialog):

	def __init__(self, proc_name, defaults):
		super(GeneralDialog, self).__init__()
		self.proc_name = proc_name
		if 'current_tab' not in defaults.keys():
			defaults['current_tab'] = 0
		self.vars = defaults
		self.widgets = {}
		


	def make_gui(self, title='', icon_name=None, width=None, height=-1, tab_titles=[], widgets={}, help_text=None):

		self.set_title(title)							# whole reason why I'm writing a separate gui; so I can retitle the damn popup...
		if icon_name:
			self.set_icon_from_file(icon_name)				# TODO: set default pygimp-logo.png
		self.set_position(gtk.WIN_POS_CENTER)			# popup in the center
		#self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		#self.set_keep_above(True)
		self.set_resizable(False)						# user can resize the window
		#self.set_geometry_hints(None, 350,200, 500,300)	# min and max window sizes
		self.width = width if width else -1
		self.set_size_request(self.width, height)
		#self.set_default_size(-1, -1)					# default size (ignored if window is bigger)
		self.set_border_width(5)						# internal border around all the gui elements

		if help_text:
			self.widgets['help_text'] = InfoLabel(help_text)

		self.parent_container = gtk.Alignment(0.5, 0, 1, 1)			# L/R, T/B, Expand L/R, Expand T/B
		self.parent_container.set_padding(5,0,5,5)						# T, B, L, R
		self.vbox.add(self.parent_container)

		#logging.warn(widgets)


		for idx, widget in enumerate(widgets):
			if 'repeats' in widget.keys():
				repeated_widgets = []
				for i in range(1, widget['repeats']+1):
					for subwidget in widget['repeat_this']:
						copy = {}
						for (key, value) in subwidget.iteritems():
							if isinstance(value, str):
								value = str.replace(value, '?', str(i))
							copy[key] = value
						repeated_widgets.append(copy)
				
				t = len(repeated_widgets)
				widgets[idx:t] = repeated_widgets

		#logging.warn(widgets)				



		# takes the passed bunch of widgets and standardises them (ie. always with tabs and lines, even on a default one widget per line, single tab plugin)
		_tab = 0
		_line = 0
		tabs = {}

		for widget in widgets:
			if 'variable' in widget.keys():
				key = widget['variable']

				# work out the notebook tab for this widget
				if not tab_titles:
					which_tab = 1
				else:
					if 'tab' in widget.keys():
						which_tab = int(widget['tab'])
						if which_tab < 1 or which_tab > len(tab_titles):
							which_tab = 1
					else:
						which_tab = _tab if _tab > 0 else 1

				# and make a new container if this is a new tab
				if which_tab != _tab:	# > instead?
					tabs[which_tab] = {}
					_tab = which_tab
					_line = 0

				# now work out the "line" this widget is on
				if 'line' in widget.keys():
					which_line = int(widget['line'])
					if which_line < 1:
						which_line = 1
				else:
					_line += 1
					which_line = _line

				# and make a new container if this is a new line
				if which_line not in tabs[which_tab].keys():
					tabs[which_tab][which_line] = []

				# note where the widget will appear
				tabs[which_tab][which_line].append(key)

				# and init the actual widget
				self.widgets[key] = widget['type'](widget)


			else:
				raise MyError("Bad widget definition: {}".format(widget))


		#logging.warn(tabs)

		
		# now build the gtk elements up from this standardized array of dictionaries
		# TODO: test the assumption that this will appear in the right order...
		self.tab_container = gtk.Notebook()

		if len(tabs) == 1: # pretend we don't have any tabs at all
			self.tab_container.set_show_tabs(False)
			self.tab_container.set_show_border(False)
		else:
			self.tab_container.set_tab_pos(gtk.POS_TOP)	# TODO: allow for the other sides
	
			#tab_container.set_shadow_type(gtk.SHADOW_NONE)
			self.tab_container.show_border = 0

		for tab_number, tab_content in list(tabs.items()):
			page = gtk.VBox(spacing=10, homogeneous=False)
			page.set_border_width(10)

			for line_num, line_of_widgets in list(tab_content.items()):
				widget_line = gtk.HBox(spacing=10, homogeneous=False)
				for key in line_of_widgets:
					widget_line.add(self.widgets[key])
				page.add(widget_line)

			title = gtk.Label(tab_titles[tab_number-1]) if tab_titles else None
			self.tab_container.append_page(page, title)

		if len(tabs) == 1: # oops, reset the padding on the single page notebook
			page.set_border_width(0)


		self.container = gtk.VBox(spacing=12, homogeneous=False)
		self.container.add(self.tab_container)

		self.add_standard_buttons()						# add the progress bar, help text and help/okay/cancel buttons
		self.parent_container.add(self.container)

		self.show_all()									# show the whole gui

		self.set_defaults(self.vars)
		self.set_states_and_responses()					# then link in the widget states and click events



	def add_standard_buttons(self):
		controls = {
			'progress' : gimpui.ProgressBar(), #gtk.ProgressBar() # is easier to use gimpui's built in bar than construct a new one
			'help' : Button({'label':'_Help'}),
			'okay' : Button({'label':'_Okay'}),
			'close' : Button({'label':'_Cancel'}),
		}
		self.widgets = dict(self.widgets.items() + controls.items())

		self.container.add(self.widgets['progress'])

		if 'help_text' in self.widgets.keys():
			self.container.add(self.widgets['help_text'])

		#self.add_buttons(gtk.STOCK_HELP, gtk.RESPONSE_HELP, gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		#self.set_alternative_button_order((gtk.RESPONSE_OK, gtk.RESPONSE_CANCEL))
		#self.set_default_response(gtk.RESPONSE_OK)

		separator = gtk.HSeparator()
		self.container.add(separator)
		
		widget_line = gtk.HBox(spacing=10, homogeneous=True)
		if 'help_text' in self.widgets.keys():
			widget_line.add(self.widgets['help'])
		widget_line.add(self.widgets['okay'])
		widget_line.add(self.widgets['close'])
		self.container.add(widget_line)



	def widget_link_activation_old(self, *data):
		widget, key, controlled = data
		if key in self.widgets:
			if not self.widgets[key].get_value():
				self.widgets[controlled].disable()
			else:
				self.widgets[controlled].enable()

	def widget_link_activation(self, *data):
		widget, key, controlled = data
		if self.widgets[controlled].get_active():
			self.widgets[controlled].disable()
		else:
			self.widgets[controlled].enable()
	
	def widget_link_visibility(self, *data):
		widget, key, controlled = data
		if self.widgets[controlled].get_visible():
			self.widgets[controlled].set_visible(False)
		else:
			self.widgets[controlled].set_visible(True)
		



	def set_states_and_responses(self):
		if 'help_text' in self.widgets.keys():
			self.widgets['help_text'].set_visible(False)
			self.widgets['help'].connect('clicked', self.widget_link_visibility, 'help', 'help_text')

		self.widgets['okay'].connect('clicked', self.run_and_quit)
		self.widgets['okay'].grab_focus()

		self.widgets['close'].connect('clicked', gtk.main_quit)

		self.connect('destroy', gtk.main_quit)			# make sure we obey the window manager quit signal


	def set_defaults(self, defaults):
		for key, value in defaults.items():
			if key in self.widgets.keys():
				self.widgets[key].set_value(value)
		self.tab_container.set_current_page(defaults['current_tab'])


	def set_code_to_run(self, codeFunction, code_params):
		self.code = codeFunction
		self.code_params = code_params


	def run_and_quit(self, widget):
		# disable the interface
		[self.widgets[key].set_sensitive(False) for key in self.widgets.keys()]

		# get the new params
		for key in self.vars.keys():
			if key in self.widgets.keys():
				self.vars[key] = self.widgets[key].get_value()
		self.vars['current_tab'] = self.tab_container.get_current_page()

		# and save them
		gimpshelf.shelf[self.proc_name] = self.vars
		
		# queue up the real code
		gobject.idle_add(self.code, self.code_params)
		
		# and close the dialog
		gobject.idle_add(gtk.main_quit)


	def main(self):
		gtk.main()


