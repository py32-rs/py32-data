# Peripheral Version

| Chip\Peripheral | RCC   | GPIO | TIMER | DMA  | I2C  | ADC  | EXTI | USART | SYSCFG | USB      | SPI  |
| --------------- | ----- | ---- | ----- | ---- | ---- | ---- | ---- | ----- | ------ | -------- | ---- |
| F002B           |       | v1   | v1    |      | v1   | v1?  | v1   |       |        |          |      |
| F030/F003/F002A | f030  | v1   | v1    | f030 | v1   | v1   | v1   | v1    | f030   |          | v1   |
| F040/F07x/MD410 | f072  | v1   | v1    | f072 | v1   | v2   | v1   | v1    | f072   | py32f07x |      |
| F403            | f403? | v1   | v1    |      |      | v2   | v2?  |       |        | py32f403 |      |

Degree of IP Core similarity

| Peripheral | py32-hal  |                                                              | similarity |
| ---------- | --------- | ------------------------------------------------------------ | ---------- |
| GPIO       | v1        | embassy-stm32::gpio_v2                                       | A          |
| RCC        | f030/f072 | embassy-stm32::rcc_f0                                        | C          |
| RCC        | f403      | embassy-stm32::rcc_f1                                        | B          |
| TIMER      | v1        | embassy-stm32::timer_v1                                      | A          |
| ADC        | v1        | embassy-stm32::adc_v1                                        | C          |
| ADC        | v2        | embassy-stm32::adc_v2                                        | C          |
| I2C        | v1        | embassy-stm32::i2c_v1                                        | B          |
| EXTI       | v1        | embassy-stm32::exti_g0+u5                                    | A          |
| USART      | v1        | embassy-stm32::usart_v2                                      | B          |
| USB        | v1        | [musb](https://github.com/decaday/musb)::builtin-py32f07x/py32f403 | musb IP    |
|            |           |                                                              |            |
