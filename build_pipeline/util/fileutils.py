#!/usr/bin/env python

import os
import itertools

# Recursively walks the given source directory and returns pairs of the source
# files and destination files. Destination files are the same as the source
# files, except relative to dst_dir instead of src_dir.
def pairwalk(src_dir, dst_dir):
  for (root, dirs, files) in os.walk(src_dir):
    for f in files:
      src_path = os.path.join(root, f)
      dst_path = os.path.join(dst_dir, os.path.relpath(src_path, src_dir))

      yield (src_path, dst_path)

# Filters the given list of file paths such that only files with the allowed
# extensions are included.
def filter_ext(allowed_exts, iterator):
  return itertools.ifilter(lambda f: ext(f) in allowed_ext, iterator)

# Returns the given path with the extension removed
def chompext(path):
  return os.path.splitext(path)[0]

# Returns the extension of the given path
def ext(path):
  return os.path.splitext(path)[1]

# Recursively makes the given directories, unless it already exists in which
# case nothing happens.
def try_mkdirs(path):
  if not os.path.isdir(path):
    os.makedirs(path)

