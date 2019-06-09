# GIMP Plugins v0.1

A collection of experimental GIMP plugins by [Keith Drakard](https://drakard.com). All released under the [3-Clause BSD License](https://opensource.org/licenses/BSD-3-Clause).

Tested on: GIMP 2.10.8


# Installation
Start by opening GIMP, then select Edit->Preferences. Expand the Folders item in the lefthand pane (at the bottom) and select Plugins. This will show you where GIMP looks for plugins.

Copy all the files into this folder and restart GIMP.

Note that most of the plugins require extra sub-classes of mine, so make sure the "classes" folder is copied as well.


# Plugins

## Image Guides v0.1:
Just adds a grid of horizontal and vertical guide lines to the image in one step.

**Found in: Image/Guides/Add Grid**


## Tile Layer v0.1:
Automates the steps in this [instructables.com](https://www.instructables.com/id/Making-Images-seamless-horizontally-or-vertically-/) guide - ie. tiles a layer in a single direction, unlike the default "Tile Seamless" filter which forces both directions at once. Leaves the original image untouched, and optionally will demo the finished effect or leave the newly created layers separate for you to fine-tune.

**Found in: Layer/Tiling**

<details><summary>Requires</summary>
* MyGTK
</details>


## Weather - Lightning v0.1:
Draws a customizable bolt of lightning, and leaves the new layers intact so that you can tweak them afterwards.

**Found in: Filters/Render/Nature/Lightning**

<details><summary>Requires</summary>
* MyGTK
* Point
* Noise
</details>


## Koch Curves v0.1:
A fractal renderer, this one draws a [Koch snowflake](https://en.wikipedia.org/wiki/Koch_snowflake) by making a Koch curve with an angle between -90 to 90 degrees, up to 6 iterations deep, and then rotates this line to create a 1-10 sided shape centered in the middle of the image.

**Found in: Filters/Render/Fractals/Koch Curves**

<details><summary>Requires</summary>
* MyGTK
* Point
</details>


## Sierpinski Triangles v0.1:
Another fractal renderer, this draws [Sierpiński triangles](https://en.wikipedia.org/wiki/Sierpinski_triangle) with the currently selected tool.

**Found in: Filters/Render/Fractals/Sierpinski Triangles**

<details><summary>Requires</summary>
* Point
</details>


## Fractal Tree v0.1:
Makes a variety of tree like fractals. Like the other fractal renderers (and the concentric ellipses), this is pretty much following the exercises in chapter 8 of the [natureofcode.com](https://natureofcode.com/book/chapter-8-fractals/) except being translated into Python and GIMP.

**Found in: Filters/Render/Fractals/Fractal Tree**

<details><summary>Requires</summary>
* MyGTK
* Point
* Colorful
</details>


## Concentric Ellipses v0.1:
Draws a set of ever decreasing concentric ellipses around a center point.

**Found in: Filters/Render/Pattern/Concentric Ellipses**





# Extra Classes

None of these do anything on their own; they are listed so you can see what the above plugins are calling in the classes subfolder.

* **MyGTK v0.1**
    My homebrewed gimpfu replacement, written because I wanted more control over certain elements of the plugin interface. Completely replaces gimpfu for my plugins that use it (ie. it registers the plugin with GIMP and handles the GTK gubbins) but is *NOT* a complete replacement for gimpfu, as I've only written what I've needed so far.

* **Widgets v0.1**
    Contains the widgets (dropdown menus, buttons, sliders, colour pickers etc) that I'm calling from MyGTK.

* **Point v0.1**
    Another class for 2D coordinates; distances, reflections, rotations etc.

* **Noise v0.1**
    Just the Perlin Noise functions from [SimplexNoise](https://github.com/bradykieffer/SimplexNoise).

* **Colorful v0.1**
    Conversion between GIMP's own colour type and Pythonic colorsys functions, and common operations like blending or contrasting colours.




### Changelog

* **0.1**
    * Initial release.

