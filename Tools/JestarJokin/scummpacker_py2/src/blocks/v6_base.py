from common import BlockContainer
from shared import BlockDefaultSharedV5V6

class BlockDefaultV6(BlockDefaultSharedV5V6):
    pass

class BlockContainerV6(BlockContainer, BlockDefaultV6):
    block_ordering = [
        #"LECF", # don't... just don't.
        "LOFF",
        "LFLF",

        # Inside LFLF
        "ROOM",

        # Inside ROOM
        "RMHD",
        "CYCL",
        "TRNS",
        # palettes are handled differently in v6
        "PALS",
          "WRAP",
            "OFFS",
            "APAL",
        "RMIM",
         #Inside RMIM
         "RMIH",
         "IM", # IMxx
          #Inside IMxx
          "SMAP",
          "ZP", # ZPxx
        "objects",
        "OBIM",
         #Inside OBIM
         "IMHD",
         "IM",
          #Inside IMxx
          "SMAP",
          "BOMP", # appears in object 1045 in MI1CD.
          "ZP", # ZPxx
        "OBCD",
         #Inside OBCD
         "CDHD",
         "VERB",
         "OBNA",
        "scripts",
        "EXCD",
        "ENCD",
        "NLSC",
        "LSCR",
        "BOXD", # moved down in rank from v5
        "BOXM", # moved down in rank from v5
        "SCAL", # moved down in rank from v5

        # Inside LFLF
        "SCRP",
        "SOUN",
         # Inside SOUN
         "SOU",
         "SOU ",
         "ROL",
         "ROL ",
         "SBL",
         "SBL ",
         "ADL",
         "ADL ",
         "SPK",
         "SPK ",
         "MIDI",
         "GMD",
         "GMD ",
        "COST",
        "CHAR"
    ]

    def _find_block_rank_lookup_name(self, block):
        rank_lookup_name = block.name
        # dumb crap here
        if rank_lookup_name[:2] == "ZP" or rank_lookup_name[:2] == "IM":
            rank_lookup_name = rank_lookup_name[:2]
        return rank_lookup_name