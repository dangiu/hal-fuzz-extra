# Author Giuliani Daniele
# Model largely based on the SD specification found on
# https://www.kingston.com/datasheets/SDCIT-specsheet-64gb_it.pdf
# encoding of some information when needed (e.g. CARD_VERSION and CARD_TYPE) found on:
# stm32f4xx_hal_sd.h and stm32f4xx_hal_sd.c


import libscrc
from bitarray import bitarray
from hal_fuzz.models.disk import Disk


def crc_and_last_bit(input_bytes):
    crc7 = libscrc.crc7(input_bytes)        # compute crc of vector
    trail = (crc7 << 1)                     # shift by 1 bit to the left
    trail = trail | 0x00000001              # set last bit to 1
    trail = trail.to_bytes(1, 'big')        # encode to hex
    return trail


def compute_CID(MID, OID, PNM, PRV, PSN, RSV, MDT):
    # combine to byte level (a single hexadecimal char cannot be converted to "bytes" since it's only 4 bit)
    RSV_MDT = RSV << 3 | MDT
    # calculate partial CID (pre CRC)
    partial_CID = MID.to_bytes(1, 'big') +\
                  OID.to_bytes(2, 'big') +\
                  bytes(PNM, 'ascii') +\
                  PRV.to_bytes(1,'big') +\
                  PSN.to_bytes(4, 'big') +\
                  RSV_MDT.to_bytes(2, 'big')
    # calculate CID
    CID = partial_CID + crc_and_last_bit(partial_CID)
    # return CID
    return CID

def compute_CSD(
        CSD_STRUCTURE,
        RSV1,
        TAAC,
        NSAC,
        TRANS_SPEED,
        CCC,
        READ_BL_LEN,
        READ_BL_PARTIAL,
        WRITE_BLK_MISALIGN,
        READ_BLK_MISALIGN,
        DSR_IMP,
        RSV2,
        C_SIZE,
        RSV3,
        ERASE_BLK_EN,
        SECTOR_SIZE,
        WP_GRP_SIZE,
        WP_GRP_ENABLE,
        RSV4,
        R2W_FACTOR,
        WRITE_BL_LEN,
        WRITE_BL_LEN2,
        RSV5,
        FILE_FORMAT_GRP,
        COPY,
        PERM_WRITE_PROTECT,
        TMP_WRITE_PROTECT,
        FILE_FORMAT,
        RSV6
):
    # create single array of bits
    bitCSD = CSD_STRUCTURE +\
             RSV1 +\
             TAAC +\
             NSAC +\
             TRANS_SPEED +\
             CCC +\
             READ_BL_LEN +\
             READ_BL_PARTIAL +\
             WRITE_BLK_MISALIGN +\
             READ_BLK_MISALIGN +\
             DSR_IMP +\
             RSV2 +\
             C_SIZE +\
             RSV3 +\
             ERASE_BLK_EN +\
             SECTOR_SIZE +\
             WP_GRP_SIZE +\
             WP_GRP_ENABLE +\
             RSV4 +\
             R2W_FACTOR +\
             WRITE_BL_LEN +\
             WRITE_BL_LEN2 +\
             RSV5 +\
             FILE_FORMAT_GRP +\
             COPY +\
             PERM_WRITE_PROTECT +\
             TMP_WRITE_PROTECT +\
             FILE_FORMAT +\
             RSV6
    partial_CSD = bitCSD.tobytes()  # convert to bytes
    CSD = partial_CSD + crc_and_last_bit(partial_CSD)   # add CRC
    return CSD


class SDModel:

    CARD_VERSION = 0x00000001   # version 2
    CARD_TYPE = 0x00000001      # CARD_SDHC_SDXC
    RCA = 0x1234                # Relative Card Address
    BLOCK_SIZE = 512            # Block/Sector size in bytes

    # CID Register - Card Identification Register (128 bits)
    MID = 0x41              # Manufacturer ID
    OID = 0x3432            # OEM ID
    PNM = 'SDCIT'           # Product Name
    PRV = 0x30              # Product Version
    PSN = 0x12345678        # Product Serial Number
    RSV = 0x0               # Reserved
    MDT = 0x112             # Production Date

    # CSD Register - Card Specific Data Register (128 bits)
    CSD_STRUCTURE = bitarray('01')      # CSD structure version - 2 bits
    RSV1 = bitarray('000000')           # Reserved - 6 bits
    TAAC = bitarray()                   # 8 bits
    TAAC.frombytes(0x0e.to_bytes(1, 'big'))
    NSAC = bitarray()                   # 8 bits
    NSAC.frombytes(0x00.to_bytes(1, 'big'))
    TRANS_SPEED = bitarray()            # Max transfer speed - 8 bits
    TRANS_SPEED.frombytes(0x5a.to_bytes(1, 'big'))
    CCC = bitarray()                    # SD class - 12 bits
    CCC.frombytes(0x5b5.to_bytes(2, 'big'))
    CCC = CCC[-12:]
    READ_BL_LEN = bitarray()            # 4 bits
    READ_BL_LEN.frombytes(0x9.to_bytes(1, 'big'))
    READ_BL_LEN = READ_BL_LEN[-4:]
    READ_BL_PARTIAL = bitarray('0')     # 1 bit
    WRITE_BLK_MISALIGN = bitarray('0')  # 1 bit
    READ_BLK_MISALIGN = bitarray('0')   # 1 bit
    DSR_IMP = bitarray('0')             # 1 bit
    RSV2 = bitarray('000000')           # Reserved - 6 bits

    C_SIZE = bitarray()                 # Size - 22 bits
    C_SIZE.frombytes(0x00127F.to_bytes(3, 'big'))
    C_SIZE = C_SIZE[-22:]

    RSV3 = bitarray('0')                # Reserved - 1 bit
    ERASE_BLK_EN = bitarray('1')        # 1 bit

    SECTOR_SIZE = bitarray()            # 7 bits
    SECTOR_SIZE.frombytes(0x7f.to_bytes(1, 'big'))
    SECTOR_SIZE = SECTOR_SIZE[-7:]

    WP_GRP_SIZE = bitarray('0000000')   # 7 bits
    WP_GRP_ENABLE = bitarray('0')       # 1 bit
    RSV4 = bitarray('00')               # Reserved - 2 bit

    R2W_FACTOR = bitarray()             # 3 bits
    R2W_FACTOR.frombytes(0x02.to_bytes(1, 'big'))
    R2W_FACTOR = R2W_FACTOR[-3:]

    WRITE_BL_LEN = bitarray()           # 4 bits
    WRITE_BL_LEN.frombytes(0x09.to_bytes(1, 'big'))
    WRITE_BL_LEN = WRITE_BL_LEN[-4:]
    WRITE_BL_LEN2 = bitarray('0')       # 1 bit
    RSV5 = bitarray('00000')            # Reserved - 5 bit
    FILE_FORMAT_GRP = bitarray('0')     # 1 bit
    COPY = bitarray('0')                # 1 bit
    PERM_WRITE_PROTECT = bitarray('0')  # 1 bit
    TMP_WRITE_PROTECT = bitarray('0')   # 1 bit


    FILE_FORMAT = bitarray('00')        # 2 bit
    RSV6 = bitarray('00')               # 2 bit


    CSD = compute_CSD(CSD_STRUCTURE, RSV1, TAAC, NSAC, TRANS_SPEED, CCC, READ_BL_LEN, READ_BL_PARTIAL,
                      WRITE_BLK_MISALIGN, READ_BLK_MISALIGN, DSR_IMP, RSV2, C_SIZE, RSV3, ERASE_BLK_EN,
                      SECTOR_SIZE, WP_GRP_SIZE, WP_GRP_ENABLE, RSV4, R2W_FACTOR, WRITE_BL_LEN, WRITE_BL_LEN2,
                      RSV5, FILE_FORMAT_GRP, COPY, PERM_WRITE_PROTECT, TMP_WRITE_PROTECT, FILE_FORMAT, RSV6)


    CID = compute_CID(MID, OID, PNM, PRV, PSN, RSV, MDT)

    # initialize empty disk
    disk = Disk(BLOCK_SIZE)

    # input is loaded from SD HAL during HAL_SD_Init()
