#!/usr/bin/env python3

from pathlib import Path

import phototracks as pt

photos = pt.PhotoCollection(Path("tests/assets"))
tracks = pt.TrackCollection(Path("tests/assets"))
