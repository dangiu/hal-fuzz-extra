# Author Giuliani Daniele
# FAT FileSystem Manipulation Utility - FFSMU

import struct
from majid_fatfs.disk import Disk


class FFSMU:
    DEFAULT_SECTOR_SIZE = 512
    mbr_layout = {
        # name: offset
        'partition_entry_1': 0x1be,
        'partition_entry_2': 0x1ce,
        'partition_entry_3': 0x1de,
        'partition_entry_4': 0x1ee
    }
    partition_entry_size = 16
    partition_entry_layout = {
        # name: (offset, unpack string)
        'status': (0x00, 'c'),
        'CHS_start': (0x01, 'sss'),
        'partition_type': (0x04, 'c'),
        'CHS_end': (0x05, 'sss'),
        'LBA_first_sector': (0x08, '<I'),
        'num_sectors': (0x0C, '<I')
    }
    bs_bpb_layout = {   # Boot Sector and BIOS Parameter Block layout
        'BPB_BytsPerSec': (11, '<H'),   # bytes per cluster
        'BPB_SecPerClus': (13, 'B'),    # sectors per cluster
        'BPB_TotSec32': (32, '<I'),     # total number of sector in volume
        'BPB_FATSz32': (36, '<I'),      # number of sectors occupied by the FAT (File Allocation Table)
        'BPB_RootClus': (44, '<I'),     # first cluster of root directory
        'BPB_FSInfo': (48, '<H')        # sector number of the FSINFO structure
    }


    def __init__(self, disk):
        self.disk = disk
        partition_entry = disk.read(FFSMU.mbr_layout['partition_entry_1'], FFSMU.partition_entry_size)
        LBA_first_sector = struct.unpack_from(FFSMU.partition_entry_layout['LBA_first_sector'][1], partition_entry, offset=FFSMU.partition_entry_layout['LBA_first_sector'][0])[0]
        volume_offset = LBA_first_sector * FFSMU.DEFAULT_SECTOR_SIZE
        boot_sector = disk.read(volume_offset, 512)
        for k, v in FFSMU.bs_bpb_layout.items():
            print(k + ": " + str(struct.unpack_from(v[1], boot_sector, offset=v[0])[0]))

        # TODO think better how we want tu structure this module in relation with the stuff that it interacts with (SD model, disk, a real file image???)
        # TODO implement methods to parse MBR FAT, add file by editing FAT and Clusters


def main():
    d = Disk(512)
    d.import_from_dictionary('2gdict')
    h = FFSMU(d)


if __name__ == '__main__':
    main()