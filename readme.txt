Scummpiler by kypello, v1.0.2

To decompile a game, run the following command:

python scummpiler.py decompile game_path decomp_path game_id

"game_id" can be one of the following: MI1EGA, MI1VGA, MI1CD, MI2
(this is a subset of the games supported by Scummpacker)


Rebuilding is similar:

python scummpiler.py build decomp_path game_path game_id


I think the only dependency that will need to be installed is Pillow

Third-party tools included in this project:
Scummpacker, Scummbler by Laurence Dougal Myers (jestarjokin.net), MIT license
Descumm by the ScummVM team (scummvm.org), GPLv2 license

Everything else is made by kypello and under the MIT license
