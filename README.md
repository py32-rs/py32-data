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

[py32-hal](https://github.com/py32-rs/py32-hal)
provides a cross-family HAL implementation depending on py32-metapac.

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

## Development & Contributing

If you want to add new chips, fix register bugs, or understand how this repository works, please read the **[Development Guide](DEVELOPMENT.md)**.

### Generate metapac

Please install chiptool first:

```bash
cargo install --git https://github.com/embassy-rs/chiptool --locked
```

Then run the following command in the repo root directory to generate py32-metapac. The final output will be generated in `build/py32-metapac`.

```bash
./d gen
```

## TODOs

- Update(rescrape) chips data.

- PY32F403 Series.

- Configure the additional registers for peripherals like USART and I2C on the PY32F072, which has more registers compared to version 1 (F030).

- The py32f07x reference manual does not describe the exact layout of the UID; it only specifies the base address (0x1FFF3000).  

## License

This project is licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or
  <http://www.apache.org/licenses/LICENSE-2.0>)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or <http://opensource.org/licenses/MIT>)

at your option.