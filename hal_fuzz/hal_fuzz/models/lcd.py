# Author Giuliani Daniele

from unicorn.arm_const import *
import struct

# void BSP_LCD_DisplayStringAt(uint16_t Xpos, uint16_t Ypos, uint8_t *Text, Text_AlignModeTypdef Mode (1,2,3 == C,R,L))
def BSP_LCD_DisplayStringAt(uc):
    # get hsd base pointer
    x_pos = uc.reg_read(UC_ARM_REG_R0)
    y_pos = uc.reg_read(UC_ARM_REG_R1)
    text_pointer = uc.reg_read(UC_ARM_REG_R2)
    align_mode = uc.reg_read(UC_ARM_REG_R3)

    string = []
    offset = 0
    curr_byte = uc.mem[text_pointer:text_pointer + 1]
    while curr_byte != b'\x00':
        string.append(curr_byte)
        offset = offset + 1
        curr_byte = uc.mem[text_pointer + offset: text_pointer + offset + 1]

    string = b''.join(string).decode('ascii')

    print('DISPLAY   X={:<4}Y={:<4}  ALIGN={:1}'.format(x_pos, y_pos, align_mode))
    print('STRING    \'{}\''.format(string))

    return