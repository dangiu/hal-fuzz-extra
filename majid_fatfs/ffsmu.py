# Author Giuliani Daniele
# FAT FileSystem Manipulation Utility - FFSMU

import struct
from majid_fatfs.disk import Disk
from bitarray import bitarray
import os


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

    def read_sector(self, sec_number):
        return self.disk.read(self.base_offset + (sec_number * self.bs_bpb['BPB_BytsPerSec']), self.bs_bpb['BPB_BytsPerSec'])

    def write_sector(self, sec_number, sec_content):
        if len(sec_content) != self.bs_bpb['BPB_BytsPerSec']:
            print('FFSMU write_sector() error: sector content of wrong size')
        else:
            self.disk.write(self.base_offset + (sec_number * self.bs_bpb['BPB_BytsPerSec']), self.bs_bpb['BPB_BytsPerSec'], sec_content)

    def write_cluster(self, cluster, content):
        """
        Writes content to the beginning of the cluster.
        Content size must be smaller or equal to cluster size, remaining space in cluster is filled with zeros.
        """
        if len(content) > self.CLUSTER_SIZE:
            print('Error write_cluster(): content must be smaller than CLUSTER_SIZE')
            return

        # TODO test this method

        content_index = 0
        offset = self.get_offset_from_cluster(cluster)
        end_offset = offset + self.CLUSTER_SIZE
        while offset < end_offset:
            # get a block worth of content
            if content_index + self.disk.block_size < len(content):
                chunk = content[content_index:content_index + self.disk.block_size]
            if content_index < len(content):
                # get last bit of content
                chunk = content[content_index:]
                # pad content with 0 until end of block
                if len(chunk) < self.disk.block_size:
                    chunk = chunk + bytes(self.disk.block_size - len(chunk))
            else:
                chunk = bytes(self.disk.block_size)
            content_index = content_index + 512
            # write block
            self.disk.write(offset, chunk)
            # increase offset
            offset = offset + self.disk.block_size


    def get_cluster_from_offset(self, offset):
        """Given an offset, returns the cluster number (which is also the entry index in the FAT)."""
        shifted = offset - self.data_offset             # distance from beginning of the first data cluster)
        return (shifted // (self.CLUSTER_SIZE)) + self.bs_bpb['BPB_RootClus']     # cluster number

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

    def get_free_cluster(self, n):
        """Return a list of indexes, the first n encountered empty clusters in the FAT (possibly not contiguous)"""
        # start looking from cluster 3 (first 2 entry are reserved, 3rd is root dir)
        index = 3
        free_clusters = []
        while True:
            entry = self.disk.read(self.fat_offset + index * 4, 4)
            entry = mask_bytes(entry, b'\xff\xff\xff\x0f')
            if entry == b'\x00\x00\x00\x00':
                free_clusters.append(index)
                if len(free_clusters) == n:
                    return free_clusters
            index = index + 1

    def create_cluster_chain(self, size):
        """Allocates a cluster chain of given size in the FAT and returns a list of cluster indexes used."""
        clusters = self.get_free_cluster(size)
        # write chain inside FAT
        for i in range(len(clusters)):
            if i == len(clusters) - 1: # last element
                next = b'\xff\xff\xff\x0f'  # End of Chain marker
            else:
                next = struct.pack('<I', clusters[i + 1])
            self.disk.write(self.fat_offset + clusters[i] * 4, next)
        return clusters

    def ls(self):
        """
        Lists Directory Entries in current position.
        TODO cannot read long entries, implement
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
                print('{}.{} -- Attr: {} -- Clus: {} -- Size in bytes: {}'.format(e['DIR_Name'].decode('ascii').strip(), e['DIR_Ext'].decode('ascii'), attr, first_clus, size))

            # prepare new position
            pos = pos + 32
            if pos >= (self.get_offset_from_cluster(cluster) + self.CLUSTER_SIZE):
                # end of cluster reached, go to beginning of next cluster if available
                if len(cluster_chain) == 0:
                    return
                else:
                    cluster = cluster_chain.pop(0)  # get next cluster
                    pos = self.get_offset_from_cluster(cluster)


    def cd(self, shortname):
        """
        Given a shortname, changes position form current location to an another directory,
        if a dir entry with such name exists.
        TODO cannot read long entries, implement
        """
        cluster = self.get_cluster_from_offset(self.current_position)
        cluster_chain = self.get_cluster_chain(cluster)  # get cluster allocated to current position
        cluster_chain.pop(0)  # remove first cluster (current cluster already setted)
        pos = self.current_position
        while True:
            entry = self.disk.read(pos, 32)  # dir entries are 32 byte in size
            attr = entry[11]
            if entry[0] == 0x00:
                print('{} does not exist!'.format(shortname))
                break  # This entry is empty and there are no more entries after this one
            if attr == 0x0f:
                # FAT Long Directory Entry
                print('Long Dir Entry NOT SUPPORTED: ' + entry.hex())
            else:
                # "normal" Directory Entry
                e = {}
                for k, v in FFSMU.directory_entry_layout.items():
                    e[k] = entry[v[0]:v[0] + v[1]]

                if e['DIR_Name'].decode('ascii').strip() == shortname:
                    # possible match found, check if it is a directory
                    attr = bitarray()
                    attr.frombytes(e['DIR_Attr'])
                    if attr[3]:
                        # directory found
                        first_clus = e['DIR_FstClusLO'] + e['DIR_FstClusHI']
                        first_clus = struct.unpack('<I', first_clus)[0]
                        # change current position
                        self.current_position = self.get_offset_from_cluster(first_clus)
                        print('New position: {}'.format(e['DIR_Name'].decode('ascii').strip()))
                        break

            # prepare new position
            pos = pos + 32
            if pos >= (self.get_offset_from_cluster(cluster) + self.CLUSTER_SIZE):
                # end of cluster reached, go to beginning of next cluster if available
                if len(cluster_chain) == 0:
                    return
                else:
                    cluster = cluster_chain.pop(0)  # get next cluster
                    pos = self.get_offset_from_cluster(cluster)

    def import_file(self, file):
        """
        Given a file, adds it to the filesystem.
        Creates a new directory entry at the current position,
        writes the content of the file to the filesystem in one or more empty clusters
        """
        cluster = self.get_cluster_from_offset(self.current_position)
        cluster_chain = self.get_cluster_chain(cluster)  # get cluster allocated to current position
        cluster_chain.pop(0)  # remove first cluster (current cluster already setted)
        pos = self.current_position
        while True:
            # get first empty entry
            entry = self.disk.read(pos, 32)  # dir entries are 32 byte in size
            attr = entry[11]
            if entry[0] == 0x00:
                # empty entry found
                parts = file.split('.')
                name = parts[0].upper()
                ext = b''
                if len(name) > 8:   # trim file name if too long
                    name = name[:8]
                while len(name) < 8:   # pad file name if too short
                    name = name + ' '

                if len(parts) > 1:  # check if file has extension
                    ext = parts[-1].upper()
                    if len(ext) > 3:
                        ext = ext[:3]
                    while len(ext) < 3:
                        name = ext + ' '
                else:
                    ext = '   '

                DIR_Name = name.encode() + ext.encode()    # final shortname of entry
                DIR_Attr = bitarray('00100000').tobytes()     # ATTR_ARCHIVE set to 1 because new file is written
                DIR_NTRes = b'\x00'
                DIR_CrtTimeTenth = b'\x00'
                DIR_CrtTime = b'\x00\x00'
                DIR_CrtDate = b'\x00\x00'
                DIR_LstAccDate = b'\x00\x00'
                DIR_WrtTime = b'\x00\x00'
                DIR_WrtDate = b'\x00\x00'

                # get file size
                size = os.stat(file).st_size
                DIR_FileSize = struct.pack('<I', size)

                # allocate clusters for content
                num_cluster = (size // self.CLUSTER_SIZE) + 1   # compute number of cluster needed to store file
                allocated_clusters = self.create_cluster_chain(num_cluster)
                cluster_bytes = struct.pack('<I', allocated_clusters[0])

                # compute first cluster entry
                DIR_FstClusLO = cluster_bytes[:2]
                DIR_FstClusHI = cluster_bytes[2:]

                # write entry to filesystem
                entry = DIR_Name + DIR_Attr + DIR_NTRes + DIR_CrtTimeTenth + DIR_CrtTime + DIR_CrtDate + DIR_LstAccDate + DIR_FstClusHI + DIR_WrtTime + DIR_WrtDate + DIR_FstClusLO + DIR_FileSize
                self.disk.write(pos, entry) # write to disk

                # write file content to clusters
                f = open(file, "rb")
                remaining = size
                while remaining > 0:
                    # read file one cluster at the time and write it to the disk
                    content = f.read(self.CLUSTER_SIZE)
                    remaining = remaining - len(content)
                    curr_clust = allocated_clusters.pop(0)
                    self.write_cluster(curr_clust, content)
                f.close()

                if len(allocated_clusters) != 0:
                    print("import_file() exception!")   # sanity check, after importing we should have used all clusters
                return

            # prepare new position
            pos = pos + 32
            if pos >= (self.get_offset_from_cluster(cluster) + self.CLUSTER_SIZE):
                # end of cluster reached, go to beginning of next cluster if available
                if len(cluster_chain) == 0:
                    return
                else:
                    cluster = cluster_chain.pop(0)  # get next cluster
                    pos = self.get_offset_from_cluster(cluster)


def main():
    d = Disk(512)
    d.import_from_dictionary('mediadict')
    h = FFSMU(d)

    h.cd('test')
    h.cd('MEDIA')

    h.import_file('testo.txt')
    h.disk.export_as_image('endresult')

    print('END') # TODO remove


if __name__ == '__main__':
    main()