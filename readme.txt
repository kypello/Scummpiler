To decompile a game, run decompile.py with the following three arguments: game folder, output folder, game version
The game version argument can be one of the following: MI1EGA, MI1VGA, MI1CD, MI2 (this is a subset of the game arguments accepted by scummpacker)
For example:

python3 decompile.py \path\to\monkey \path\to\monkey_decompiled MI1CD

Optionally, you can add a fourth argument, "no_images". This will decompile the game without decoding any images
Image decompilation and recompilation requires the Pillow module to be installed. it can be installed with: pip install Pillow

To recompile the game, run recompile.py with the following three arguments: decompiled folder, output folder, game version
For example:

python3 recompile.py \path\to\monkey_decompiled \path\to\monkey_recompiled MI1CD

Recompile will automatically detect any files that have been edited and will only recompile what's needed
Note that if you are recompiling the CD version, the mp3 files will not be carried over, so you'll need to copy them from the original game folder
The recompiled game should run in ScummVM

---

Credits:
decompile.py, descumm.py, recompile.py, rescumm.py made by kypello
scummpacker, scummbler, scummimg made by JestarJokin www.jestarjokin.net
scummimg modified and converted to python 3 by kypello
descumm.exe made by the ScummVM team