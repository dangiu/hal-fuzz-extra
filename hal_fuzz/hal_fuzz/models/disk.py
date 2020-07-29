# Author Giuliani Daniele

import re
import struct


class Disk:
    def __init__(self, block_size):
        self.content = {}               # content of the disk
        self.block_size = block_size    # block size

    def read(self, offset, size):
        # TODO span read to multiple blocks
        block_num = offset // self.block_size
        block_offset = offset % self.block_size
        if block_offset + size > self.block_size:
            print("Disk read() error: read cannot span more than one block")
        else:
            return self.read_block(block_num)[block_offset:block_offset + size]

    def write(self, offset, content):
        # TODO span write to multiple blocks
        block_num = offset // self.block_size
        block_offset = offset % self.block_size
        if block_offset + len(content) > self.block_size:
            print("Disk write() error: write cannot span more than one block")
        else:
            old_block = self.read_block(block_num)
            left = old_block[:block_offset]
            right = old_block[block_offset + len(content):]
            new_block = left + content + right
            self.write_block(block_num, new_block)

    def write_block(self, addr, content):
        # write block
        if (len(content) != self.block_size) | (type(content) != bytes):
            print('Disk write_block() error: bad content length')
        else:
            # when trying to write an empty block (all zeros) remove the entry from the dictionary
            if content == bytes(self.block_size):
                self.content.pop(addr, None)
            else:
                self.content[addr] = content

    def read_block(self, addr):
        # initialize return value as block (512 bytes) of zeros
        block = bytes(self.block_size)
        # if block exists return it
        if addr in self.content:
            block = self.content[addr]
        return block

    def get_block_count(self):
        # return the number of blocks written (that are not empty) on the disk
        return len(self.content.keys())

    def get_block_list(self):
        # return the list of addresses of blocks not empty
        blocks = []
        for addr in self.content.keys():
            blocks.append(addr)
        return blocks

    def print_block(self, addr):
        if addr in self.content:
            block = self.content[addr]
            block_string = re.sub("(.{32})", "\\1\n", block.hex(), 0, re.DOTALL)
            block_string = re.sub("(.{2})", "\\1 ", block_string, 0)
            print(block_string)
        else:
            print("This block does not exist!")

    def export_as_image(self, name):
        """Export disk as binary image file that can be mounted."""
        path = './' + name
        f = open(path, 'wb')
        block_list = self.get_block_list()
        block_list.sort()
        first_block = block_list[0]
        last_block = block_list[-1]
        for i in range(first_block, last_block + 1):
            f.write(self.read_block(i))
        f.close()

    def import_from_image(self, name):
        """Import disk from a binary image."""
        path = './' + name
        f = open(path, 'rb')
        addr = 0
        while True:
            buff = f.read(self.block_size)
            if len(buff) == 0:
                break   # EOF reached
            self.write_block(addr, buff)
            addr = addr + 1
        f.close()

    def import_from_dictionary(self, name):
        """
        Import disk from a binary dictionary in the form:
        block address: block content
        - "block address" is a 32 bit integer encoded in big endian format
        - "block content" is an array of size "block_size"
        """
        path = './' + name
        f = open(path, 'rb')
        while True:
            buff = f.read(4 + self.block_size)
            if len(buff) == 0:
                break   # EOF reached
            a_bytes = buff[:4]
            block = buff[4:]
            addr = struct.unpack('>I', a_bytes)[0]
            self.write_block(addr, block)
        f.close()

    def export_as_dictionary(self, name):
        """
        Export disk as a binary dictionary in the form:
        block address: block content
        - "block address" is a 32 bit integer encoded in big endian format
        - "block content" is an array of size "block_size"
        """
        path = './' + name
        f = open(path, 'wb')
        for k, v in self.content.items():
            f.write(struct.pack('>I', k))
            f.write(v)
        f.close()