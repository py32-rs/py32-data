# py32-data

Puya MCU Series metapac.

This repo is adapted from [embassy-rs/stm32-data](https://github.com/embassy-rs/stm32-data).

Contributions are welcome!

You can check the peripheral version corresponding to the microcontroller [here](peripheral_version.md).

## Contirbute

You can refer to the relevant descriptions and explanations in[embassy-rs/stm32-data](https://github.com/embassy-rs/stm32-data) repo. 

The difference is that our data sources are fewer. In addition to the content already present in this repo, the data can come from the processing of the PY32 C language SDK header files, datasheets, and  Reference Manual, etc. 

In fact, the IPs of peripherals in different PY32 series may be consistent, and different series can refer to each other. 

Moreover, some series use the same die(e.g. F003, F002A, F030 use same die), so support a new serie might not require much work.

[Rust 嵌入式开发中的外设寄存器访问：从 svd2rust 到 chiptool 和 metapac - 以 hpm-data 为例 | 猫·仁波切](https://andelf.github.io/2024/08/23/embedded-rust-peripheral-register-access-svdtools-chiptool-and-metapac-approach/)

## Families

Date: 20240312

- Low Cost
  - PY32F002A
  - PY32F002B
  - PY32F003
- Mainstream
  - PY32F030
  - PY32F031
  - PY32F040
  - PY32F071
  - PY32F072
  - PY32F403
- Low Power
  - PY32L020
- Moter Control
  - PY32M010
  - PY32M020
  - PY32M030
  - PY32M031
  - PY32M070
  - PY32MD
- Touch Control
  - PY32T020
