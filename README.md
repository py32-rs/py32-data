# py32-data & py32-metapac

[![Crates.io][badge-license]][crates]
[![Crates.io][badge-version]][crates]
[![docs.rs][badge-docsrs]][docsrs]

[badge-license]: https://img.shields.io/crates/l/py32-metapac?style=for-the-badge
[badge-version]: https://img.shields.io/crates/v/py32-metapac?style=for-the-badge
[badge-docsrs]: https://img.shields.io/docsrs/py32-metapac?style=for-the-badge
[crates]: https://crates.io/crates/py32-metapac
[docsrs]: https://docs.rs/py32-metapac

All-in-one Rust PAC(Peripheral Access Crate) for Puya MCU Series.

This repository maintains the registers and metadata for PY32, processes this information, and generates the metapac.

Whenever changes are pushed to the main branch, a workflow will automatically run to push the latest generated metapac to https://github.com/py32-rs/py32-metapac.

You can check the peripheral version corresponding to the microcontroller [here](peripheral_version.md).

https://github.com/py32-rs/py32-hal provides a cross-family HAL implementation depending on py32-metapac.

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

## Contirbute

You can refer to the relevant descriptions and explanations in[embassy-rs/stm32-data](https://github.com/embassy-rs/stm32-data) repo.

The difference is that our data sources are fewer. In addition to the content already present in this repo, the data can come from the processing of the PY32 C SDK header files, datasheets, and  Reference Manual, etc.

In fact, the IPs of peripherals in different PY32 series may be consistent, and different series can refer to each other.

Moreover, some series use the same die(e.g. F003, F002A, F030 use same die), so support a new serie might not require much work.

If you have any questions, feel free to open a discussion or an issue! Contributions are welcome!

### Generate metapac

Please install chiptool first:

```bash
cargo install --git https://github.com/embassy-rs/chiptool --locked
```

Then run the following command in the repo root directory to generate py32-metapac. The final output will be generated in `build/py32-metapac`.

```bash
./d gen
```

### Add support for new peripherals

1. Run the following command in the repo root directory to extract all peripherals.

  ```bash
  ./d extract all
  ```

  All peripherals will be exported from the SVD files under `svd/` to `tmp/`. 

2. Then, you need to manually compare the differences in registers for the same peripheral across different families, and change some register fields to enums and arrays. 

3. Rename the block name from `I2C1` to `I2C`.

4. Rename the filename to `<peripheral_name>_<version>.yaml` (e.g., `i2c_v1.yaml`, `rcc_f030.yaml`). 

5. Convert it to UTF-8 encoding and move it to `data/registers/`.

6. Complete or add the information for this peripheral in `data/peripherals/**.yaml`.

7. Rerun `./d gen` to generate the metapac and check if there are any errors.

### Add support for new families

I must admit that the current family and data management is somewhat messy; I will refactor this in the future.

### Other reference

- (In Chinese) [Rust 嵌入式开发中的外设寄存器访问：从 svd2rust 到 chiptool 和 metapac - 以 hpm-data 为例 | 猫·仁波切](https://andelf.github.io/2024/08/23/embedded-rust-peripheral-register-access-svdtools-chiptool-and-metapac-approach/)

## TODOs

- Configure the additional registers for peripherals like USART and I2C on the PY32F072, which has more registers compared to version 1 (F030).

- Set up configurations for cut-down variants such as PY32F003, PY32F002A, PY32F040.

- The py32f07x reference manual does not describe the exact layout of the UID; it only specifies the base address (0x1FFF3000).  

## License

This project is licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or
  <http://www.apache.org/licenses/LICENSE-2.0>)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or <http://opensource.org/licenses/MIT>)

at your option.