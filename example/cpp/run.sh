#!/bin/sh

export LD_PRELOAD=../../src/ftracer.so:libdl.so

./test
