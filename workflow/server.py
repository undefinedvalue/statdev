#!/usr/bin/env python

import SimpleHTTPServer
import SocketServer
import os
from time import sleep
import shutil
import threading
import signal
import build_pipeline.build
from build_pipeline.util import fileutils as futil

refresh_js_path = os.path.join(os.path.dirname(__file__), 'refresh.js')

class QuieterHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def log_request(self, code='-', size='-'):
    if not self.requestline.startswith('HEAD'):
      SimpleHTTPServer.SimpleHTTPRequestHandler.log_request(self, code, size)

class Server:
  def __init__(self, src_dir, dst_dir, port=8080, **kwargs):
    self.src_dir = src_dir
    self.dst_dir = dst_dir
    self.port = port
    self.final_build_dir = os.path.join(self.dst_dir, 'final')
    self.httpd = None
    self.server_thread = None
    self.watch = True

  def start(self):
    # Clean shutdown on ctrl+c
    def signal_handler(signal, frame):
      print
      print 'Shutting down...'
      self.watch = False
      self.stop_server()

    signal.signal(signal.SIGINT, signal_handler)

    print 'Serving at port', self.port
    print 'Serving files from', self.final_build_dir
    print('Press Ctrl+C to stop')

    (lastmtime, path) = self.getUpdatedFile(0)
    self.rebuild()
    self.start_server()

    while self.watch:
      (lastmtime, path) = self.getUpdatedFile(lastmtime)
      if path:
        print 'File changed:', path
        self.stop_server()
        self.rebuild()
        self.start_server()

      sleep(0.25)

  def getUpdatedFile(self, lastmtime):
    updatedPath = None

    for (root, dirs, files) in os.walk(self.src_dir):
      for f in files:
        if futil.ext(f) not in ['.swp'] and f != '.DS_Store':
          path = os.path.join(root, f)
          mtime = os.path.getmtime(path)

          if mtime > lastmtime:
            lastmtime = mtime
            updatedPath = path

    return (lastmtime, updatedPath)

  # Rebuilds the project, as if by "build.py build --skip s3_upload"
  def rebuild(self):
    try:
      print 'Building', self.src_dir
      os.chdir(self.src_dir)
      build_pipeline.build.build(self.src_dir, self.dst_dir, skip=['s3_upload'],
          opts={'environment': 'development'})

      # Copy the refresh.js file last, since that will indicate that the
      # build is done.
      dst_js_dir = os.path.join(self.final_build_dir, 'js')
      if not os.path.exists(dst_js_dir):
        os.mkdir(dst_js_dir)
      shutil.copy(refresh_js_path, dst_js_dir)
    except Exception as e:
      print e

  def server(self):
    os.chdir(self.final_build_dir)
    SocketServer.TCPServer.allow_reuse_address = True
    self.httpd = SocketServer.TCPServer(('', self.port), QuieterHTTPRequestHandler)

    try:
      self.httpd.serve_forever()
    finally:
      self.httpd.server_close()

  # Runs the HTTP server in a separate thread
  def start_server(self):
    self.server_thread = threading.Thread(target=lambda: self.server())
    self.server_thread.start()

  def stop_server(self):
    if self.httpd:
      self.httpd.shutdown()
      self.server_thread.join()

