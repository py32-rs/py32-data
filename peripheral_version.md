# Peripheral Version

| Chip\Peripheral | RCC  | GPIO | TIMER | DMA | I2C | ADC | EXTI | USART |
| --------------- | ---- | ---- | ----- | --- | --- | --- | ---- | ----- |
| F002B           |      | v1   | v1    |     | v1  | v1  | v1   |       |
| F030/F003/F002A | f030 | v1   | v1    | v1  | v1  | v1  | v1   | v1    |
| F040/F07x/MD410 | f072 | v1   | v1    | v1  | v1  | v2  | v1   | v1    |
| F403            |      | v1   | v1    |     |     | v2  | v2?  |       |

Degree of similarity to embassy-stm32

| Peripheral | py32-hal | embassy-stm32 | similarity |
| ---------- | -------- | ------------- | ---------- |
| GPIO       | v1       | v2            | A          |
| RCC        | f030     | f0            | B          |
| TIMER      | v1       | v1            | A          |
| DMA        | v1       | v1/v2         | C          |
| ADC        | v1       | v1            | C          |
| ADC        | v2       | v2            | C          |
| I2C        | v1       | v1            | B          |
| EXTI       | v1       | g0+u5         | A          |
| USART      | v1       | v2            | B          |
|            |          |               |            |
|            |          |               |            |
|            |          |               |            |
|            |          |               |            |
|            |          |               |            |
|            |          |               |            |
