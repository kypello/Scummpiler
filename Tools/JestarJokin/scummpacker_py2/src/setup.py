# setup script for ScummPacker

from distutils.core import setup
import py2exe

# includes for py2exe
includes=['pyexpat', 'xml.etree.ElementTree', 'xml.etree.cElementTree']

opts = { 'py2exe': { 'includes':includes } }
#print 'opts',opts

setup(version = "3.2",
      description = "Scummpacker",
      name = "Scummpacker",
      author = "Laurence Dougal Myers",
      author_email = "jestarjokin@jestarjokin.net",
      console = [
        {
            "script": "scummpacker.py",
        }
      ],
      options=opts
      )