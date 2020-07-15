# Author Giuliani Daniele
# Model based on the SD specification found on
# https://www.kingston.com/datasheets/SDCIT-specsheet-64gb_it.pdf
# encoding of some information when needed (e.g. CARD_VERSION and CARD_TYPE) found on:
# stm32f4xx_hal_sd.h and stm32f4xx_hal_sd.c

import re

class SDModel:

    CARD_VERSION = 0x00000001   # version 2
    CARD_TYPE = 0x00000001  # CARD_SDHC_SDXC
    RCA = 0x1234    # Relative Card Address # TODO don't really know how this affects stuff... shoud be checked out more

    CID = bytes.fromhex("413432736463697430123456780112c7")
    CSD = bytes.fromhex("400e005a5b590001d27f7f800a400001")

    BLOCK_SIZE = 512

    disk = {}

    #THESE METHOD WORK ONLY FOR SINGLE BLOCK WRITE/READ
    @classmethod
    def write_block(cls, addr, content):
        # write block
        cls.disk[addr] = content

    @classmethod
    def read_block(cls, addr):
        # initialize return value as block (512 bytes) of zeros
        block = bytes(512)
        # if block exists return it
        if addr in cls.disk:
            block = cls.disk[addr]
        return block

    @classmethod
    def get_block_count(cls):
        # return the number of blocks written (that are not empty) on the disk
        return len(cls.disk.keys())

    @classmethod
    def get_block_list(cls):
        # return the list of addresses of blocks not empty
        blocks = []
        for addr in cls.disk.keys():
            blocks.append(addr)
        return blocks

    @classmethod
    def print_block(cls, addr):
        if addr in cls.disk:
            block = cls.disk[addr]
            block_string = re.sub("(.{32})", "\\1\n", block.hex(), 0, re.DOTALL)
            block_string = re.sub("(.{2})", "\\1 ", block_string, 0)
            print(block_string)
        else:
            print("This block does not exist!")

    @classmethod
    def export_to_file(cls, name):
        path = './' + name
        f = open(path, 'wb')
        block_list = cls.get_block_list()
        block_list.sort()
        first_block = block_list[0]
        last_block = block_list[-1]
        for i in range(first_block, last_block + 1):
            f.write(cls.read_block(i))
        f.close()
