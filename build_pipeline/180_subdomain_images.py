#!/usr/bin/env python

# Compiles Sass templates

import sass
import os
import io
import shutil
from itertools import ifilter
from util import fileutils as futil
from bs4 import BeautifulSoup

def build(src_dir, dst_dir, opts):
  sd = Subdomainer(src_dir)
  img_subdomain = opts.get('img_subdomain')

  img_paths = [p for p in sd.filepaths() if futil.ext(p) in ['.jpg', '.png']]

  for (src_path, dst_path) in futil.pairwalk(src_dir, dst_dir):
    if futil.ext(src_path) == '.html':
      # Replace paths in html files
      sd.replace(src_path, dst_path, img_paths, img_subdomain)
    else:
      # Copy non-html files over
      futil.try_mkdirs(os.path.dirname(dst_path))
      shutil.copy2(src_path, dst_path)

class Subdomainer:
  def __init__(self, src_dir):
    self.src_dir = src_dir

  def filepaths(self):
    for root, dirs, files in os.walk(self.src_dir):
      path = os.path.relpath(root, self.src_dir)

      for name in files:
        if path == '.':
          p = os.path.join('/', name)
        else:
          p = os.path.join('/', path, name)

        yield p

  def replace(self, src_path, dst_path, replace_paths, subdomain):
    with open(src_path, 'rb') as src, \
         open(dst_path, 'wb') as dst:

      html = BeautifulSoup(src, 'html.parser')

      if subdomain:
        for tag in html.find_all(attrs={'src': replace_paths}):
          tag['src'] = '//' + subdomain + tag['src']

      dst.write(str(html))
