import logging
import sys
import os

def create_parent_folders(file_path):
  directory = os.path.dirname(file_path)
  if not os.path.exists(directory):
    os.makedirs(directory)

def setup_log(level = logging.DEBUG, out=sys.stdout):
  root = logging.getLogger()
  root.setLevel(level)
  handler = logging.StreamHandler(out)
  handler.setLevel(level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  handler.setFormatter(formatter)
  root.addHandler(handler)