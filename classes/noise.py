#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Noise v0.1
# 
# Change Log
# ----------
# 0.1: Initial release
#
# ------------------------------------------------------------------------------
#
# perlin noise from https://github.com/bradykieffer/SimplexNoise/blob/master/simplexnoise/noise.py
#

import math, random

# see also https://www.redblobgames.com/articles/noise/introduction.html

# Constants to avoid magic numbers
DEFAULT_NOISE_SCALE = -1  # Check noise_scale against this
DEFAULT_1D_NOISE_SCALE = 0.188
DEFAULT_LACUNARITY = 2.0
DEFAULT_GAIN = 0.65
DEFAULT_SHUFFLES = 100

def normalize(x):
    res = (1.0 + x) / 2.0

    # Clamp the result, this is not ideal
    if res > 1:
        res = 1
    if res < 0:
        res = 0

    return res

class PerlinNoiseOctave(object):

    def __init__(self, num_shuffles=DEFAULT_SHUFFLES):
        self.p_supply = [i for i in xrange(0, 256)]

        for i in xrange(num_shuffles):
            random.shuffle(self.p_supply)

        self.perm = self.p_supply * 2

    def noise(self, xin, noise_scale):
        ix0 = int(math.floor(xin))
        fx0 = xin - ix0
        fx1 = fx0 - 1.0
        ix1 = (ix0 + 1) & 255
        ix0 = ix0 & 255

        s = self.fade(fx0)

        n0 = self.grad(self.perm[ix0], fx0)
        n1 = self.grad(self.perm[ix1], fx1)

        return noise_scale * self.lerp(s, n0, n1)

    def lerp(self, t, a, b):
        return a + t * (b - a)

    def fade(self, t):
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    def grad(self, hash, x):
        h = hash & 15
        grad = 1.0 + (h & 7)  # Gradient value from 1.0 - 8.0
        if h & 8:
            grad = -grad  # Add a random sign
        return grad * x


class PerlinNoise(object):
    """ 
        Implementation of 1D Perlin Noise ported from C code: 
        https://github.com/stegu/perlin-noise/blob/master/src/noise1234.c
    """

    def __init__(self, num_octaves, persistence, noise_scale=DEFAULT_NOISE_SCALE):
        self.num_octaves = num_octaves

        if DEFAULT_NOISE_SCALE == noise_scale:
            self.noise_scale = DEFAULT_1D_NOISE_SCALE
        else:
            self.noise_scale = noise_scale

        self.octaves = [PerlinNoiseOctave() for i in xrange(self.num_octaves)]
        self.frequencies = [1.0 / pow(2, i) for i in xrange(self.num_octaves)]
        self.amplitudes = [pow(persistence, len(self.octaves) - i)
                           for i in xrange(self.num_octaves)]

    def noise(self, x):
        noise = [
            self.octaves[i].noise(
                xin=x * self.frequencies[i],
                noise_scale=self.noise_scale
            ) * self.amplitudes[i] for i in xrange(self.num_octaves)]

        return sum(noise)

    def fractal(self, x, hgrid, lacunarity=DEFAULT_LACUNARITY, gain=DEFAULT_GAIN):
        """ A more refined approach but has a much slower run time """
        noise = []
        frequency = 1.0 / hgrid
        amplitude = gain

        for i in xrange(self.num_octaves):
            noise.append(
                self.octaves[i].noise(
                    xin=x * frequency,
                    noise_scale=self.noise_scale
                ) * amplitude
            )

            frequency *= lacunarity
            amplitude *= gain

        return sum(noise)

