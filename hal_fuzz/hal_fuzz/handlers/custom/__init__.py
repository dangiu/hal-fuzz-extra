from unicorn.arm_const import *
import time

'''
void HAL_GPIO_Init(GPIO_TypeDef  *GPIOx, GPIO_InitTypeDef *GPIO_Init)
'''
def gpio_init(uc):
    print('Executing GPIO init (doing nothing)')

'''
void HAL_GPIO_WritePin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin, GPIO_PinState PinState)
'''
def gpio_write_pin(uc):
    r0 = uc.reg_read(UC_ARM_REG_R0)
    r1 = uc.reg_read(UC_ARM_REG_R1)
    r2 = uc.reg_read(UC_ARM_REG_R2)
    print('GPIO WritePin ### Pin {}, Pinstate {}'.format(r1, r2))

'''
void HAL_GPIO_TogglePin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin)
'''
def gpio_toggle_pin(uc):
    r0 = uc.reg_read(UC_ARM_REG_R0)
    r1 = uc.reg_read(UC_ARM_REG_R1)
    # pc = uc.reg_read(UC_ARM_REG_PC)
    print('GPIO TogglePin ### Pin {}'.format(r1))
    # print('Program Counter: {}'.format(pc))

def print_r01(uc):
    r0 = uc.reg_read(UC_ARM_REG_R0)
    r1 = uc.reg_read(UC_ARM_REG_R1)
    print('R0: ', r0)
    print('R1: ', r1)

'''
__weak void HAL_Delay(uint32_t Delay)
'''
def delay(uc):
    delay = uc.reg_read(UC_ARM_REG_R0)
    time.sleep(delay/1000)  # delay must be converted from millisecond to seconds
    print('Requested delay for {} ms'.format(delay))


def return_one(uc):
    uc.reg_write(UC_ARM_REG_R0, 1)
