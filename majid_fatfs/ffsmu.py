# Author Giuliani Daniele
# FAT FileSystem Manipulation Utility - FFSMU

import struct
from majid_fatfs.disk import Disk
from bitarray import bitarray


def mask_bytes(input, mask):
    if len(input) != len(mask):
        print('Error: Input and mask have different size!')
    else:
        output = b''
        for i in range(len(mask)):
            b = input[i] & mask[i]
            output = output + b.to_bytes(1, 'big')
        return output


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
        'BPB_RsvdSecCnt': (14, '<H'),   # number of reserved sector in the volume (used to compute FAT position)
        'BPB_TotSec32': (32, '<I'),     # total number of sector in volume
        'BPB_FATSz32': (36, '<I'),      # number of sectors occupied by the FAT (File Allocation Table)
        'BPB_RootClus': (44, '<I'),     # first cluster of root directory
        'BPB_FSInfo': (48, '<H')        # sector number of the FSINFO structure
    }
    fsinfo_layout = {   # FSINFO layout
        'free_ClsCnt': (0x1E8, '<I'),   # last known number of free data cluster
        'used_ClsCnt': (0x1EC, '<I')    # last known number of occupied data cluster
    }
    directory_entry_layout = {  # FAT Directory Entry Layout (32 bytes)
        'DIR_Name': (0, 8),             # entry name
        'DIR_Ext': (8, 3),              # entry extension
        'DIR_Attr': (11, 1),            # attributes
        'DIR_CrtTime': (14, 2),         # creation time
        'DIR_CrtDate': (16, 2),         # creation date
        'DIR_LstAccDate': (18, 2),      # last access date
        'DIR_FstClusHI': (20, 2),       # high word of this entry's first cluster number
        'DIR_WrtTime': (22, 2),         # last write time
        'DIR_WrtDate': (24, 2),         # last write date
        'DIR_FstClusLO': (26, 2),       # low word of this entry's first cluster number
        'DIR_FileSize': (28, 4),        # file size in bytes
    }

    def __init__(self, disk):
        self.disk = disk
        partition_entry = disk.read(FFSMU.mbr_layout['partition_entry_1'], FFSMU.partition_entry_size)
        LBA_first_sector = struct.unpack_from(FFSMU.partition_entry_layout['LBA_first_sector'][1], partition_entry, offset=FFSMU.partition_entry_layout['LBA_first_sector'][0])[0]

        # Compute volume offset (base offset used by FFSMU)
        self.base_offset = LBA_first_sector * FFSMU.DEFAULT_SECTOR_SIZE

        # Read Boot Sector and BPB
        self.bs_bpb = {}
        boot_sector = disk.read(self.base_offset, FFSMU.DEFAULT_SECTOR_SIZE)
        for k, v in FFSMU.bs_bpb_layout.items():
            self.bs_bpb[k] = struct.unpack_from(v[1], boot_sector, offset=v[0])[0]

        # Compute main structures offsets
        self.fsinfo_offset = self.base_offset + (self.bs_bpb['BPB_FSInfo'] * self.bs_bpb['BPB_BytsPerSec'])
        self.fat_offset = self.base_offset + (self.bs_bpb['BPB_RsvdSecCnt'] * self.bs_bpb['BPB_BytsPerSec'])
        self.data_offset = self.fat_offset + (self.bs_bpb['BPB_FATSz32'] * self.bs_bpb['BPB_BytsPerSec'])

        # Read FSINFO
        self.fsinfo = {}
        fsinfo = self.read_sector(self.bs_bpb['BPB_FSInfo'])
        for k, v in FFSMU.fsinfo_layout.items():
            self.fsinfo[k] = struct.unpack_from(v[1], fsinfo, offset=v[0])[0]

        # Setup of common constant values
        self.CLUSTER_SIZE = self.bs_bpb['BPB_SecPerClus'] * self.bs_bpb['BPB_BytsPerSec']

        # Setup variables used to navigate filesystem
        self.current_position = self.data_offset    # set initial position to root directory

        print('test') # TODO remove
        # TODO see notebook
        # TODO get offset to all main structures

    def read_sector(self, sec_number):
        return self.disk.read(self.base_offset + (sec_number * self.bs_bpb['BPB_BytsPerSec']), self.bs_bpb['BPB_BytsPerSec'])

    def write_sector(self, sec_number, sec_content):
        if len(sec_content) != self.bs_bpb['BPB_BytsPerSec']:
            print('FFSMU write_sector() error: sector content of wrong size')
        else:
            self.disk.write(self.base_offset + (sec_number * self.bs_bpb['BPB_BytsPerSec']), self.bs_bpb['BPB_BytsPerSec'], sec_content)

    def get_cluster_from_offset(self, offset):
        """Given an offset, returns the cluster number (which is also the entry index in the FAT)."""
        shifted = offset - self.data_offset             # distance from beginning of the first data cluster)
        return (shifted % (self.CLUSTER_SIZE)) + self.bs_bpb['BPB_RootClus']     # cluster number

    def get_offset_from_cluster(self, cluster):
        """Given a cluster number, returns the offset at which it starts."""
        base = self.data_offset  # distance from beginning of the first data cluster)
        clust_dist = cluster - self.bs_bpb['BPB_RootClus']
        return base + (clust_dist * self.CLUSTER_SIZE)

    def get_cluster_chain(self, index):
        """Given a cluster number (or FAT entry), returns the chain of entries assigned to the same file."""
        entry = self.disk.read(self.fat_offset + index * 4, 4)     # FAT entries are 32 bit in size (4 bytes)
        # entries are 28 bit long, the 4 most significant bits (entries encoding in Little Endian) must be masked off
        entry = mask_bytes(entry, b'\xff\xff\xff\x0f')
        entries = [index]
        while entry != b'\xff\xff\xff\x0f':  # repeat until End of Chain marker is reached
            new_index = struct.unpack('<I', entry)[0]
            entries.append(new_index)
            entry = self.disk.read(self.fat_offset + new_index * 4, 4)
            entry = mask_bytes(entry, b'\xff\xff\xff\x0f')
        return entries

    def ls(self):
        """
        Lists Directory Entries in current position.
        TODO cannot read long entries
        """
        cluster = self.get_cluster_from_offset(self.current_position)
        cluster_chain = self.get_cluster_chain(cluster)  # get cluster allocated to current position
        cluster_chain.pop(0)    # remove first cluster (current cluster already setted)
        pos = self.current_position
        while True:
            entry = self.disk.read(pos, 32) # dir entries are 32 byte in size
            attr = entry[11]
            if entry[0] == 0x00:
                break   # This entry is empty and there are no more entries after this one
            if attr == 0x0f:
                # FAT Long Directory Entry
                print('Long Dir Entry NOT SUPPORTED: ' + entry.hex())
            else:
                # "normal" Directory Entry
                e = {}
                for k, v in FFSMU.directory_entry_layout.items():
                    e[k] = entry[v[0]:v[0] + v[1]]
                attr = bitarray()
                attr.frombytes(e['DIR_Attr'])
                first_clus = e['DIR_FstClusLO'] + e['DIR_FstClusHI']
                first_clus = struct.unpack('<I', first_clus)[0]
                size = struct.unpack('<I', e['DIR_FileSize'])[0]
                print('{}.{} -- Attr: {} -- Clus: {} -- Size in bytes: {}'.format(e['DIR_Name'], e['DIR_Ext'], attr, first_clus, size))

            # prepare new position
            pos = pos + 32
            if pos >= (self.get_cluster_from_offset(cluster) + self.CLUSTER_SIZE):
                # end of cluster reached, go to beginning of next cluster if available
                if len(cluster_chain) == 0:
                    return
                else:
                    cluster = cluster_chain.pop(0)  # get next cluster
                    pos = self.get_offset_from_cluster(cluster)


    def cd(self, name):
        """
        Change current position to another directory.
        TODO cannot read long entries
        """
        print('IMPLEMENT') # TODO implement

    def import_file(self, file):
        """
        Given a file, adds it to the filesystem.
        Creates a new directory entry at the current position,
        writes the content of the file to the filesystem in one or more empty clusters
        """
        print('IMPLEMENT')  # TODO implement


def main():
    d = Disk(512)
    d.import_from_dictionary('2gdict')
    h = FFSMU(d)

    h.get_cluster_chain(2)
    h.ls()
    print('test') # TODO remove


if __name__ == '__main__':
    main()