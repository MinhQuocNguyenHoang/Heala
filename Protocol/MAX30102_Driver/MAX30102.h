#ifndef MAX30102_H
#define MAX30102_H

#include <stdint.h> 

// I2C Address
#define MAX30102_I2C_ADDRESS 0x57

//register address
#define MAX30102_REG_INT_STATUS_1 0x00
#define MAX30102_REG_INT_STATUS_2 0x01
#define MAX30102_REG_INT_ENABLE_1 0x02
#define MAX30102_REG_INT_ENABLE_2 0x03

#define MAX30102_REG_FIFO_WR_PTR 0x04
#define MAX30102_REG_OVF_COUNTER 0x05
#define MAX30102_REG_FIFO_RD_PTR 0x06
#define MAX30102_REG_FIFO_DATA 0x07

#define MAX30102_REG_FIFO_CONFIG 0x08
#define MAX30102_REG_MODE_CONFIG 0x09
#define MAX30102_REG_SPO2_CONFIG 0x0A
#define MAX30102_REG_LED_PULSE_AMP_1 0x0C
#define MAX30102_REG_LED_PULSE_AMP_2 0x0D

#define MAX30102_REG_REV_ID 0xFE
#define MAX30102_REG_PART_ID 0xFF

// --- Mode Configuration (0x09) ---
// Bitmasks
#define MAX30102_MODE_SHDN_MASK        0b10000000 // 0x80
#define MAX30102_MODE_RESET_MASK       0b01000000 // 0x40
#define MAX30102_MODE_MASK             0b00000111 // 0x07

// Bit values
#define MAX30102_MODE_HR_ONLY          0x02
#define MAX30102_MODE_SPO2_EN          0x03
#define MAX30102_MODE_MULTI_LED        0x07

// --- SpO2 Configuration (0x0A) Bit Defines ---
#define MAX30102_SPO2_ADC_RGE_MASK     0x9F
#define MAX30102_SPO2_ADC_RGE_2048     0x00

// --- Function Prototypes ---
uint8_t MAX30102_Init();

void MAX30102_Read_FIFO(uint32_t* ir, uint32_t *red);

void MAX30102_Reset();

void MAX30102_Set_Mode(uint8_t mode);

#endif //MAX30102_H 