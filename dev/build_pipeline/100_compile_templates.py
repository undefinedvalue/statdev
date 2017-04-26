#!/usr/bin/env python

# Compiles Jinja templates (.j2 extension)

import os
import shutil
from jinja2 import Environment, FileSystemLoader
from util import fileutils as futil

def build(src_dir, dst_dir, opts):
  loader = FileSystemLoader(src_dir)
  env = Environment(auto_reload=False,
                    trim_blocks=True,
                    lstrip_blocks=True,
                    loader=loader)
  env.globals['environment'] = opts.get('environment')

  # Render all files in the src_dir that have a ".j2" extension
  for (src_path, dst_path) in futil.pairwalk(src_dir, dst_dir):
    futil.try_mkdirs(os.path.dirname(dst_path))

    if futil.ext(src_path) == '.j2':
      template = os.path.relpath(src_path, src_dir)

      # If it starts with "_" then it is a partial
      if not os.path.basename(template).startswith('_'):
        env.globals['template_name'] = template
        out_path = futil.chompext(dst_path)
        env.get_template(template).stream().dump(out_path)
    elif not src_path.endswith(('.swp', '~')):
      # Copy all other files straight over
      shutil.copy2(src_path, dst_path)

