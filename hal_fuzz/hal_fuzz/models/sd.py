# Author Giuliani Daniele
# Model based on the SD specification found on
# https://www.kingston.com/datasheets/SDCIT-specsheet-64gb_it.pdf
# encoding of some information when needed (e.g. CARD_VERSION and CARD_TYPE) found on:
# stm32f4xx_hal_sd.h and stm32f4xx_hal_sd.c

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
