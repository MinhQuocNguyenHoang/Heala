#include <stdio.h>
#include <heala_oled.h>
#include <esp_log.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "driver/gpio.h"
#include "esp_task_wdt.h"

#define moveButton 12
#define choiceButton 13
SemaphoreHandle_t sem_moveButton;
SemaphoreHandle_t sem_choiceButton;

typedef enum
{
    MENU_EVENT_MOVE,
    MENU_EVENT_SELECT
} menu_event_t;

QueueHandle_t menuQueue;
static const char *TAG_I2C = "I2C";

static void IRAM_ATTR isr_moveButton(void *arg)
{
    static uint32_t last_tick_move = 0;
    uint32_t now = xTaskGetTickCountFromISR();

    if ((now - last_tick_move) > pdMS_TO_TICKS(200))
    {
        last_tick_move = now;
        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        xSemaphoreGiveFromISR(sem_moveButton, &xHigherPriorityTaskWoken);
        if (xHigherPriorityTaskWoken)
            portYIELD_FROM_ISR();
    }
}
static void IRAM_ATTR isr_choiceButton(void *arg)
{
    static uint32_t last_tick_choice = 0;
    uint32_t now = xTaskGetTickCountFromISR();

    if ((now - last_tick_choice) > pdMS_TO_TICKS(200))
    {
        last_tick_choice = now;
        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        xSemaphoreGiveFromISR(sem_choiceButton, &xHigherPriorityTaskWoken);
        if (xHigherPriorityTaskWoken)
            portYIELD_FROM_ISR();
    }
}

void vTaskMoveButton(void *arg)
{
    menu_event_t evt = MENU_EVENT_MOVE;
    while (1)
    {
        if (xSemaphoreTake(sem_moveButton, portMAX_DELAY))
        {
            xQueueSend(menuQueue, &evt, 0);
        }
    }
}

void vTaskChoiceButton(void *arg)
{
    menu_event_t evt = MENU_EVENT_SELECT;
    while (1)
    {
        if (xSemaphoreTake(sem_choiceButton, portMAX_DELAY))
        {
            xQueueSend(menuQueue, &evt, 0);
        }
    }
}

void vTaskMonitorMenu(void *arg)
{
    menu_event_t evt;
    uint8_t status = 0; // 0 = Health, 1 = HRV

    // Vẽ menu ban đầu
    oled_clear();
    oled_draw_auto(wifi, 13, 16, 0, 0);
    oled_draw_auto(bluetooth, 6, 16, 15, 0);
    oled_draw_auto(pin_100, 32, 16, 96, 0);
    oled_draw_string(45, 0, "HEALA");
    oled_draw_string(40, 2, "23:15:01");
    oled_draw_auto(health, 15, 16, 15, 4);
    oled_draw_auto(HRV, 18, 16, 99, 4);
    oled_draw_string(7, 7, "Health");
    oled_draw_string(99, 7, "HRV");
    oled_draw_auto(movebutton, 5, 8, 0, 7); // Con trỏ ban đầu

    while (1)
    {
        if (xQueueReceive(menuQueue, &evt, portMAX_DELAY))
        {
            switch (evt)
            {
            case MENU_EVENT_MOVE:
                // Di chuyển chọn giữa Health ↔ HRV
                if (status == 0)
                {
                    oled_clear_data(7, 7, 0, 5);
                    oled_draw_auto(movebutton, 5, 8, 92, 7);
                    status = 1;
                }
                else
                {
                    oled_clear_data(7, 7, 92, 97);
                    oled_draw_auto(movebutton, 5, 8, 0, 7);
                    status = 0;
                }
                break;

            case MENU_EVENT_SELECT:
                // Nháy chữ khi chọn
                if (status == 0)
                {
                    for (int i = 0; i < 2; i++)
                    {
                        oled_clear_data(7, 7, 0, 50);
                        vTaskDelay(pdMS_TO_TICKS(200));
                        oled_draw_string(7, 7, "Health");
                        vTaskDelay(pdMS_TO_TICKS(200));
                    }
                }
                else
                {
                    for (int i = 0; i < 2; i++)
                    {
                        oled_clear_data(7, 7, 92, 125);
                        vTaskDelay(pdMS_TO_TICKS(200));
                        oled_draw_string(99, 7, "HRV");
                        vTaskDelay(pdMS_TO_TICKS(200));
                    }
                }
                break;
            }
        }
    }
}

void OledInit()
{
    esp_task_wdt_delete(NULL);
    oled_init();
    vTaskDelay(pdMS_TO_TICKS(10));
    oled_clear();
    vTaskDelay(pdMS_TO_TICKS(10));
    ESP_LOGI(TAG_I2C, "Oled Ready");
}

void GPIOInit()
{
    esp_task_wdt_delete(NULL);
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_POSEDGE,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pin_bit_mask = (1ULL << moveButton) | (1ULL << choiceButton)};
    gpio_config(&io_conf);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(moveButton, isr_moveButton, NULL);
    gpio_isr_handler_add(choiceButton, isr_choiceButton, NULL);
    ESP_LOGI("GPIO", "Ready");
}

void app_main(void)
{
    sem_moveButton = xSemaphoreCreateBinary();
    sem_choiceButton = xSemaphoreCreateBinary();
    menuQueue = xQueueCreate(5, sizeof(menu_event_t));

    OledInit();
    GPIOInit();

    xTaskCreate(vTaskMoveButton, "moveButton is pressed", 2000, NULL, 3, NULL);
    xTaskCreate(vTaskChoiceButton, "moveButton is pressed", 2000, NULL, 3, NULL);
    xTaskCreate(vTaskMonitorMenu, "is running...", 2048, NULL, 4, NULL);
}
