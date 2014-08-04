# import sys
from setuptools import setup
from setuptools import find_packages
import glob #, subprocess
# import os


PROJECT = "Active Thumbnails"
ICON = "Minimal.icns"

plist = {
    "CFBundleIconFile" : ICON,
    "CFBundleIdentifier" : "com.minimal-project.%s" % PROJECT,
    }


setup(
    name = "Active Thumbnails",
    version = "0.1",
    packages = find_packages(),
    author = "Adam Rule",
    description = "A simple pyobjc project to get you started",
    app=["Application.py"],
    data_files=["English.lproj"] +glob.glob("Resources/*.*"),
    options=dict(py2app=dict(
        plist=plist,
    )),
)
