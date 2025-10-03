/*
 * File: MAX30102.cpp
 * Author: Phạm Nhung
 * Date: 28/09/2025
 * Description: Implementation file for the MAX30102 driver.
 */

 #include <Arduino.h>
 #include <Wire.h>
 #include "MAX30102.h"

 // --- Private Helper Functions for I2C Communication ---

 /**
 * @brief Writes a single byte to a specific register on the MAX30102.
 * @param reg The register address to write to.
 * @param value The byte value to write.
 */
static void writeRegister8(uint8_t reg, uint8_t value){
    Wire.beginTransmission(MAX30102_I2C_ADDRESS);
    Wire.write(reg);
    Wire.write(value);
    Wire.endTransmission();
}

/**
 * @brief Reads a single byte from a specific register.
 * @param reg The register address to read from.
 * @return The byte value read from the register.
 */
static uint8_t readRegister8(uint8_t reg){
    Wire.beginTransmission(MAX30102_I2C_ADDRESS);
    Wire.write(reg);
    Wire.endTransmission(false);

    Wire.requestFrom(MAX30102_I2C_ADDRESS, 1);
    if(Wire.available()){
        return Wire.read();
    }

    return 0; // Return 0 on error
}

/**
 * @brief Reads a block of bytes from a register (used for FIFO).
 * @param reg The starting register address.
 * @param buffer Pointer to the byte array to store the data.
 * @param length The number of bytes to read.
 */
static void readRegisters(uint8_t reg, uint8_t* buffer, uint8_t length){
    Wire.beginTransmission(MAX30102_I2C_ADDRESS);
    Wire.write(reg);
    Wire.endTransmission(false);

    Wire.requestFrom(MAX30102_I2C_ADDRESS, (int)length);
    for(uint8_t i = 0; i < length; i++){
        if(Wire.available()){
            buffer[i] = Wire.read();
        }
    }
}

// --- Public Function Implementations ---

uint8_t MAX30102_Init() {
    // Start I2C
    Wire.begin();

    // Check if the sensor is connected by reading its Part ID
    if (readRegister8(MAX30102_REG_PART_ID) != 0x15) {
        return 0; // Return 0 (false) to indicate failure
    }

    // Reset the sensor to a known state
    MAX30102_Reset();
    delay(100); // Wait for reset to complete

    // --- Configure the sensor with some default settings ---

    // Set FIFO Almost Full interrupt to trigger when 15 samples are left
    // 0x0F means FIFO depth is 17-15=2.
    writeRegister8(MAX30102_REG_INT_ENABLE_1, 0b10000000); // A_FULL_EN

    // Clear FIFO pointers
    writeRegister8(MAX30102_REG_FIFO_WR_PTR, 0x00);
    writeRegister8(MAX30102_REG_FIFO_RD_PTR, 0x00);
    writeRegister8(MAX30102_REG_OVF_COUNTER, 0x00);

    // FIFO Config: Sample averaging = 4, No FIFO rollover, FIFO almost full = 15
    writeRegister8(MAX30102_REG_FIFO_CONFIG, 0b01001111); // SMP_AVE=4, FIFO_ROLLOVER_EN=false, FIFO_A_FULL=15

    // Mode Config: SpO2 mode
    MAX30102_Set_Mode(MAX30102_MODE_SPO2_EN);

    // SpO2 Config: ADC Range = 4096, Sample Rate = 100Hz, Pulse Width = 411us
    writeRegister8(MAX30102_REG_SPO2_CONFIG, 0b00100111);

    // LED Pulse Amplitude: Set a moderate brightness for IR and Red LEDs
    writeRegister8(MAX30102_REG_LED_PULSE_AMP_1, 0x24); // Red LED
    writeRegister8(MAX30102_REG_LED_PULSE_AMP_2, 0x24); // IR LED

    return 1; // Return 1 (true) to indicate success
}

void MAX30102_Reset() {
    // Read current mode config
    uint8_t original_mode = readRegister8(MAX30102_REG_MODE_CONFIG);

    // Set the reset bit (bit 6)
    writeRegister8(MAX30102_REG_MODE_CONFIG, original_mode | MAX30102_MODE_RESET_MASK);
}

void MAX30102_Set_Mode(uint8_t mode) {
    // Read current mode config
    uint8_t config = readRegister8(MAX30102_REG_MODE_CONFIG);

    // Clear the mode bits [2:0]
    config &= ~MAX30102_MODE_MASK;

    // Set the new mode
    config |= mode;

    // Write the new configuration back
    writeRegister8(MAX30102_REG_MODE_CONFIG, config);
}

void MAX30102_Read_FIFO(uint32_t* ir, uint32_t* red) {
    uint8_t buffer[6]; // Each sample is 2 * 3 = 6 bytes

    // Read 6 bytes from the FIFO data register
    readRegisters(MAX30102_REG_FIFO_DATA, buffer, 6);

    // Combine the 3 bytes into one 32-bit integer for IR
    *ir = ((uint32_t)buffer[0] << 16) | ((uint32_t)buffer[1] << 8) | buffer[2];
    
    // Combine the 3 bytes into one 32-bit integer for Red
    *red = ((uint32_t)buffer[3] << 16) | ((uint32_t)buffer[4] << 8) | buffer[5];

    // The sensor data is 18-bit, so we mask out the unused upper bits
    *ir &= 0x03FFFF;
    *red &= 0x03FFFF;
}
