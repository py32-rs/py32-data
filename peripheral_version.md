# Peripheral Version

| Chip\Peripheral | RCC  | GPIO | TIMER | DMA | SPI | I2C | ADC |     |     |
| --------------- | ---- | ---- | ----- | --- | --- | --- | --- | --- | --- |
| F030/F003/F002A |      | v1   | v1    |     |     |     | v1  |     |     |
| F030/F003/F002A | f030 | v1   | v1    | v1  |     |     | v1  |     |     |
| F040/F07x/MD410 |      | v1   | v1    |     |     |     | v1  |     |     |
| F403            |      | v1   | v1    |     |     |     |     |     |     |

Degree of similarity to embassy-stm32

| Peripheral | py32 | stm32 | similarity |
| ---------- | ---- | ----- | ---------- |
| GPIO       | v1   | v2    | A          |
| RCC        | f030 | f0    | B          |
| TIMER      | v1   | v1    | A          |
| DMA        | v1   | v1/v2 | C          |
| ADC        | v1   | v1    | C          |
|            |      |       |            |
|            |      |       |            |
|            |      |       |            |
|            |      |       |            |
|            |      |       |            |
|            |      |       |            |
|            |      |       |            |
|            |      |       |            |
|            |      |       |            |
