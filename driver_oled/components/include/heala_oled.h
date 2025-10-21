// libirary oled I2C
#pragma once
#include "driver/i2c_master.h"
#include "stdio.h"
#include "ctype.h"
#include "string.h"

extern const uint8_t font5x7_basic[95][5];
extern const uint8_t pin_100[65];
extern const uint8_t pin_75[65];
extern const uint8_t pin_50[65];
extern const uint8_t pin_25[65];
extern const uint8_t pin_0[65];
extern const uint8_t bluetooth[13];
extern const uint8_t noBluetooth[13];
extern const uint8_t wifi[27];
extern const uint8_t noWifi[27];
extern const uint8_t health[31];
extern const uint8_t movebutton[6];
extern const uint8_t HRV[37];

#ifdef __cplusplus
extern "C"
{
#endif
    // send byte to slave
    void master_transmit_cmd(uint8_t *cmd_wr, uint8_t byte);

    // oled init
    void oled_init();

    // oled clear
    void oled_clear();

    // Set position
    void config_position(uint8_t col_start, uint8_t col_finish, uint8_t page_start, uint8_t page_finish);

    // Send data
    void master_transmit_data(uint8_t data_wr);

    // oled draw
    void oled_draw_auto(const uint8_t *bitmap, uint8_t width,
                        uint8_t height, uint8_t col_start, uint8_t page_start);

    void oled_draw_char(uint8_t col, uint8_t page, char c);

    void oled_draw_string(uint8_t col, uint8_t page, char *str);

    void oled_clear_data(uint8_t page_start, uint8_t page_finish, uint8_t col_start, uint8_t col_finish);

#ifdef __cplusplus
}
#endif