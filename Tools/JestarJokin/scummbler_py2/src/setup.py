# setup script for Scummbler

from distutils.core import setup
import py2exe

# includes for py2exe
includes=[]
includes += ['verb_helper']

opts = { 'py2exe': { 'includes':includes } }

setup(version = "2.15",
      description = "Scummbler",
      name = "Scummbler",
      author = "Laurence Dougal Myers",
      author_email = "jestarjokin@jestarjokin.net",
      console = [
        {
            "script": "scummbler.py",
        },
        {
            "script": "verb_helper.py",
        }
      ],
      options=opts
      )