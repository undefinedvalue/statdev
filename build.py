#!/usr/bin/env python

# Entrypoint into build and development tools
# For usage run: ./dev/build.py -h

# See README.md for documentation on the development system.

from os.path import dirname, abspath, join
import argparse
import build_pipeline.build
import workflow.server

base_dir = dirname(dirname(abspath(__file__)))
src_dir = join(base_dir, 'www')
dst_dir = join(base_dir, 'build')

def build(args):
  build_pipeline.build.build(src_dir, dst_dir, **vars(args))

def server(args):
  server = workflow.server.Server(src_dir, dst_dir, **vars(args))
  server.start()

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='do_action')

# build
build_parser = subparsers.add_parser('build', help='Build the project')
build_parser.set_defaults(do_action=build)
build_parser.add_argument('--skip', action='append', default=[],
        help='Skips a step in the pipeline. e.g. --skip s3_upload')

# server
server_parser = subparsers.add_parser('server', help='Start a development server')
server_parser.set_defaults(do_action=server)

args = parser.parse_args()
args.do_action(args)

