#!/usr/bin/env python

import SimpleHTTPServer
import SocketServer
import os
from datetime import datetime
import shutil
import threading
import signal
import watchdog
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import build_pipeline.build

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
    self.build_sem = threading.Semaphore()
    self.httpd = None
    self.server_thread = None

  def start(self):
    # Watch the source files for changes
    filewatch = Observer()
    filewatch.schedule(FilewatchHandler(parent=self,
        ignore_patterns=['*.swp', '*~']),
        self.src_dir,
        recursive=True)

    # Clean shutdown on ctrl+c
    def signal_handler(signal, frame):
      print
      print 'Shutting down...'
      self.stop_server()
      filewatch.stop()

    signal.signal(signal.SIGINT, signal_handler)

    self.rebuild()
    self.start_server()

    print 'Serving at port', self.port
    print 'Serving files from', self.final_build_dir
    print('Press Ctrl+C to stop')

    filewatch.start()
    signal.pause()
    filewatch.join(5000)

  # Rebuilds the project, as if by "build.py build --skip s3_upload"
  def rebuild(self):
    self.build_sem.acquire()
    try:
      print 'Building', self.src_dir
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
    finally:
      self.build_sem.release()

  def server(self):
    os.chdir(self.final_build_dir)
    SocketServer.TCPServer.allow_reuse_address = True
    self.httpd = SocketServer.TCPServer(('', self.port), QuieterHTTPRequestHandler)

    try:
      self.httpd.serve_forever()
    finally:
      self.httpd.server_close()
      print 'Server stopped'

  # Runs the HTTP server in a separate thread
  def start_server(self):
    print 'Starting server'
    self.server_thread = threading.Thread(target=lambda: self.server())
    self.server_thread.start()

  def stop_server(self):
    if self.httpd:
      print 'Stopping server'
      self.httpd.shutdown()
      self.server_thread.join(5000)


class FilewatchHandler(PatternMatchingEventHandler):
  def __init__(self, parent, *args, **kwargs):
    super(FilewatchHandler, self).__init__(*args, **kwargs)
    self.parent = parent
    self.last_event_time = datetime.now()

  # Rebuilds the project if any change is detected, unless we just rebuilt in
  # the last second.
  def on_any_event(self, event):
    dt = datetime.now() - self.last_event_time

    if not event.is_directory and dt.total_seconds() > 1:
      print 'Detected change in', event.src_path
      self.last_event_time = datetime.now()
      self.parent.rebuild()

