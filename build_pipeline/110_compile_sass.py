#!/usr/bin/env python

# Compiles Sass templates

import sass
import os
import shutil
from util import fileutils as futil

def build(src_dir, dst_dir, opts):
  sass.compile(dirname=(src_dir, dst_dir))

  # Copy non-scss files over
  for (src_path, dst_path) in futil.pairwalk(src_dir, dst_dir):
    if futil.ext(src_path) not in ['.scss', '.swp']:
      futil.try_mkdirs(os.path.dirname(dst_path))
      shutil.copy2(src_path, dst_path)
