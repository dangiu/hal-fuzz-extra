# Author Giuliani Daniele

from unicorn.arm_const import *
import struct
from ...models.sd import SDModel
import re

DEBUG = True

# HAL_StatusTypeDef HAL_SD_Init(SD_HandleTypeDef *hsd)
def HAL_SD_Init(uc):
    # get hsd base pointer
    hsd_bp = uc.reg_read(UC_ARM_REG_R0)

    # SD_PowerON() function
    # get correct CARD_VERSION and CARD_TYPE according to model
    SDCard_type_offset = 68
    SDCard_version_offset = 72

    uc.mem_write(hsd_bp + SDCard_type_offset, struct.pack("<I", SDModel.CARD_TYPE))
    uc.mem_write(hsd_bp + SDCard_version_offset, struct.pack("<I", SDModel.CARD_VERSION))

    # SD_InitCard() function

    # get CID value
    CID_offset = 116

    cid0 = SDModel.CID[0:4]
    cid1 = SDModel.CID[4:8]
    cid2 = SDModel.CID[8:12]
    cid3 = SDModel.CID[12:16]
    # change byte endianess
    cid0 = struct.pack("<I", struct.unpack(">I", cid0)[0])
    cid1 = struct.pack("<I", struct.unpack(">I", cid1)[0])
    cid2 = struct.pack("<I", struct.unpack(">I", cid2)[0])
    cid3 = struct.pack("<I", struct.unpack(">I", cid3)[0])
    # write in memory in correct position
    uc.mem_write(hsd_bp + CID_offset + 0, cid0)
    uc.mem_write(hsd_bp + CID_offset + 4, cid1)
    uc.mem_write(hsd_bp + CID_offset + 8, cid2)
    uc.mem_write(hsd_bp + CID_offset + 12, cid3)

    # get RCA value
    SDCard_offset = 68
    RelCardAdd_offset = 12
    uc.mem_write(hsd_bp + SDCard_offset + RelCardAdd_offset, struct.pack("<I", SDModel.RCA))

    # get CSD value
    CSD_offset = 100

    csd0 = SDModel.CSD[0:4]
    csd1 = SDModel.CSD[4:8]
    csd2 = SDModel.CSD[8:12]
    csd3 = SDModel.CSD[12:16]
    # change byte endianess
    packed_csd0 = struct.pack("<I", struct.unpack(">I", csd0)[0])
    packed_csd1 = struct.pack("<I", struct.unpack(">I", csd1)[0])
    packed_csd2 = struct.pack("<I", struct.unpack(">I", csd2)[0])
    packed_csd3 = struct.pack("<I", struct.unpack(">I", csd3)[0])
    # write in memory in correct position
    uc.mem_write(hsd_bp + CSD_offset + 0, packed_csd0)
    uc.mem_write(hsd_bp + CSD_offset + 4, packed_csd1)
    uc.mem_write(hsd_bp + CSD_offset + 8, packed_csd2)
    uc.mem_write(hsd_bp + CSD_offset + 12, packed_csd3)

    # get SD Class (obtained directly from CSD)
    Class_offset = 8
    SDClass_bits = SDModel.CSD[4:8]
    SDClass = struct.unpack(">I", SDClass_bits)[0]
    SDClass = SDClass >> 20 # shift to obtain class value
    uc.mem_write(hsd_bp + SDCard_offset + Class_offset, struct.pack("<I", SDClass))

    # HAL_SD_GetCardCSD() function for CardType equal to CARD_SDHC_SDXC

    # / * Byte 7 * /
    # pCSD->DeviceSize = (((hsd->CSD[1] & 0x0000003FU) << 16U) | ((hsd->CSD[2] & 0xFFFF0000U) >> 16U));
    l_bits = struct.unpack(">I", csd1)[0]
    r_bits = struct.unpack(">I", csd2)[0]
    device_size = ((l_bits & 0x0000003F) << 16) | ((r_bits & 0xFFFF0000) >> 16)

    # hsd->SdCard.BlockNbr = ((pCSD->DeviceSize + 1U) * 1024U);
    BlockNbr_offset = 16
    BlockNbr = (device_size + 1) * 1024
    packed_BlockNbr = struct.pack("<I", BlockNbr)
    uc.mem_write(hsd_bp + SDCard_offset + BlockNbr_offset, packed_BlockNbr)
    # hsd->SdCard.LogBlockNbr = hsd->SdCard.BlockNbr;
    LogBlockNbr_offset = 24
    uc.mem_write(hsd_bp + SDCard_offset + LogBlockNbr_offset, packed_BlockNbr)
    # hsd->SdCard.BlockSize = 512U;
    BlockSize_offset = 20
    packed_BlockSize = struct.pack("<I", SDModel.BLOCK_SIZE)
    uc.mem_write(hsd_bp + SDCard_offset + BlockSize_offset, packed_BlockSize)
    # hsd->SdCard.LogBlockSize = hsd->SdCard.BlockSize;
    LogBlockSize_offset = 28
    uc.mem_write(hsd_bp + SDCard_offset + LogBlockSize_offset, packed_BlockSize)


    # end of HAL_SD_Init() function
    # offset in hsd structure
    context_offset = 48
    state_offset = 52
    error_code_offset = 56

    # values to write
    context = 0
    state = 1  # HAL_SD_STATE_READY
    error_code = 0

    # write in memory
    uc.mem_write(hsd_bp + error_code_offset, struct.pack("<I", error_code))
    uc.mem_write(hsd_bp + state_offset, struct.pack("<I", context))
    uc.mem_write(hsd_bp + context_offset, struct.pack("<I", state))

    # return 0
    uc.reg_write(UC_ARM_REG_R0, 0)

# HAL_StatusTypeDef HAL_SD_ConfigWideBusOperation(SD_HandleTypeDef *hsd,uint32_t WideMode)
def HAL_SD_ConfigWideBusOperation(uc):
    # get hsd base pointer
    bp = uc.reg_read(UC_ARM_REG_R0)

    # offset in hsd structure
    state_offset = 52

    # values to write
    state = 1 # HAL_SD_STATE_READY

    # encoded values
    state = struct.pack("<I", state)

    # write in memory
    uc.mem_write(bp + state_offset, state)

    # return 0
    uc.reg_write(UC_ARM_REG_R0, 0)

# HAL_SD_CardStateTypeDef HAL_SD_GetCardState(SD_HandleTypeDef *hsd)
def HAL_SD_GetCardState(uc):
    # return 1 (HAL_SD_CARD_READY stm32f4xx_hal_sd.h) THIS SHOULD NOT BE DONE
    # HAL_SD_CARD_TRANSFER ???      WHY WOULD THIS BE DONE INSTED?
    uc.reg_write(UC_ARM_REG_R0, 4)

# HAL_SD_WriteBlocks(SD_HandleTypeDef *hsd,uint8_t *pData,uint32_t BlockAdd,uint32_t NumberOfBlocks, uint32_t Timeout)
def HAL_SD_WriteBlocks(uc):
    # hsd base pointer
    hsd_bp = uc.reg_read(UC_ARM_REG_R0)
    # pointer to data to be written
    data_p = uc.reg_read(UC_ARM_REG_R1)
    # address of the first block to write to
    block_add = uc.reg_read(UC_ARM_REG_R2)
    # number of blocks to write
    number_of_blocks = uc.reg_read(UC_ARM_REG_R3)

    # data length
    data_length = number_of_blocks * SDModel.BLOCK_SIZE;

    if DEBUG:
        print("hsd_bp: 0x{}".format(struct.pack(">I", hsd_bp).hex()))
        print("data pointer: 0x{}".format(struct.pack(">I", data_p).hex()))
        print("block address: 0x{}".format(struct.pack(">I", block_add).hex()))
        print("number of blocks: {}".format(number_of_blocks))
        # format data nicely in strings of 64 chars (instead of a single line)
        data_string = re.sub("(.{64})", "\\1\n", uc.mem[data_p:data_p + data_length].hex(), 0, re.DOTALL)
        print("data: \n{}".format(data_string))

    # TODO refractor this part
    if number_of_blocks == 1:
        SDModel.write_block(block_add, bytes(uc.mem[data_p:data_p + data_length]))
    else:
        print("ERROR: MULTI BLOCK WRITE NOT SUPPORTED")

    # return 0
    uc.reg_write(UC_ARM_REG_R0, 0)

# HAL_StatusTypeDef HAL_SD_ReadBlocks(SD_HandleTypeDef *hsd, uint8_t *pData, uint32_t BlockAdd, uint32_t NumberOfBlocks, uint32_t Timeout)
def HAL_SD_ReadBlocks(uc):
    # hsd base pointer
    hsd_bp = uc.reg_read(UC_ARM_REG_R0)
    # pointer to the buffer where data will be stored
    data_p = uc.reg_read(UC_ARM_REG_R1)
    # address of the first block to read from
    block_add = uc.reg_read(UC_ARM_REG_R2)
    # number of blocks to write
    number_of_blocks = uc.reg_read(UC_ARM_REG_R3)

    # data length
    data_length = number_of_blocks * SDModel.BLOCK_SIZE;

    if DEBUG:
        print("hsd_bp: 0x{}".format(struct.pack(">I", hsd_bp).hex()))
        print("data pointer: 0x{}".format(struct.pack(">I", data_p).hex()))
        print("block address: 0x{}".format(struct.pack(">I", block_add).hex()))
        print("number of blocks: {}".format(number_of_blocks))

    # TODO refractor this part
    if number_of_blocks == 1:
        data = SDModel.read_block(block_add)
        # place the content inside the correct buffer
        #  uc.mem_write(hsd_bp + context_offset, struct.pack("<I", state))
        uc.mem_write(data_p, data)


    else:
        print("ERROR: MULTI BLOCK READ NOT SUPPORTED")

    # return 0
    uc.reg_write(UC_ARM_REG_R0, 0)


def Error_Handler(uc):
    # TODO remove this, just used for debugging purposes
    while True:
        print("ERROR HANDLER")

