import sys
import os
from setuptools import setup
from setuptools import find_packages
import glob #, subprocess


PROJECT = "Active Thumbnails"

plist = {
    'iconfile':'Resources/eye.icns',
}

setup(
      name = "Active Thumbnails",
      version = "0.1",
      setup_requires=["py2app"],
      options={'py2app': plist},
      packages = find_packages(),
      author = "Adam Rule",
      description = "A simple pyobjc project to get you started",
      app=["Application.py"],
      data_files=["English.lproj"] +glob.glob("Resources/*.*"),
      )

