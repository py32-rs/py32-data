# py32-data Development Guide

Welcome to the `py32-data` development guide. This repository is responsible for maintaining the registers and metadata for Puya PY32 microcontrollers and generating the `py32-metapac` (Peripheral Access Crate). 

This project's architecture and logic are ported heavily from [stm32-data](https://github.com/embassy-rs/stm32-data), so you can also refer to their documentation for additional context and advanced usage.

The difference is that our data sources are fewer. In addition to the content already present in this repo, the data can come from the processing of the PY32 C SDK header files, datasheets, and Reference Manual, etc.

In fact, the IPs of peripherals in different PY32 series may be consistent, and different series can refer to each other. Moreover, some series use the same die (e.g. F003, F002A, F030 C612 M030 use same die), so supporting a new series might not require much work.

Therefore, we have designed a data structure and workflow based on [stm32-data](https://github.com/embassy-rs/stm32-data) to handle them efficiently.

If you have any questions, feel free to open a discussion or an issue! Contributions are welcome!

---

## 1. Project Structure and Data Flow

The project separates the raw hardware data from the Rust code generation logic. The data is processed in a hierarchical, multi-stage pipeline.

### 1.1 Data Flow Overview
The data in the `data/` directory stores all hardware definitions, which are explained in detail in section 1.2.

1. **Phase 1 Generation (`py32-data-gen`)**: 
   Reads all the YAML files in the `data/` directory, resolves the hierarchical relationships (`Chip -> Generic -> Series -> Die`), applies disabled features, and generates a consolidated, flat JSON description for each chip in `build/data/chips/`.

2. **Phase 2 Generation (`py32-metapac-gen`)**: 
   Consumes the JSON files and the register definitions (from `data/registers/`). It uses `chiptool` to render the intermediate representation (IR) into final Rust source code (structs, enums, etc.) and deduplicates metadata (like peripherals and interrupts) across similar chips. The final output is written to `build/py32-metapac`. 
   
Because this is largely ported from `stm32-data`, please refer to the [stm32-data documentation](https://github.com/embassy-rs/stm32-data) for deeper insights into the code generation logic.

### 1.2 The `data/` Directory Structure
The `data/` directory contains the core YAML configurations. It is maintained using a hybrid approach: **One-time script generation -> Manual correction -> Batch script updating**. It uses a 4-level inheritance model to maximize reuse and avoid duplication:

- **`data/dies/`**: The base level. Each subdirectory (e.g., `DIE030/`) represents a distinct silicon die architecture. *Note that many PY32 series share the same wafer/die (e.g., PY32F030, PY32F003, PY32F002A, PY32M030, PY32C613 share the same die), which greatly reduces workload and increases code reuse.* It contains:
  - `peripherals.yaml`: The master list of peripherals on this die, including their base addresses, RCC (clock/reset) bindings, and interrupts. It references specific register definitions (e.g., `kind: timer, version: v1`). 
  - `interrupts.yaml`: The NVIC interrupt vector table for the die.
  - `dma_channels.yaml`, `af.yaml`, and `dma_requests.yaml`: These files define physical DMA channels, alternate function (AF) mappings for GPIO pins, and DMA request multiplexing. They can generally be obtained by slightly processing data from the official manuals or SDK.
- **`data/series/`**: The third level. Each file (e.g., `PY32F030.yaml`) maps to a physical silicon die (`die: DIE030`). It specifies `disabled_peripherals` or `disabled_interrupts` to artificially limit the capabilities of the die for cheaper product tiers. This file is typically managed automatically by running `python3 scripts/extract_all_series.py` to batch-compute differences from SVDs.
- **`data/generics/`**: The second level. Each file (e.g., `PY32F030x8.yaml`) defines a product line variant, primarily focusing on the memory layout (Flash and RAM size, start addresses, page/sector sizes) and points to a `series`.
- **`data/chips/`**: The top level. Each file (e.g., `PY32F030K18.yaml`) defines a specific physical chip model. It contains the chip name, the `generic` (product line) it belongs to, package types, and device ID.

- **`data/registers/`**: Contains YAML files (e.g., `i2c_v1.yaml`) describing the exact register layouts, bitfields, and enums for a specific version of an IP block. These are initially extracted via `./d extract-all` and then manually tuned. You should also refer to [peripheral_version.md](peripheral_version.md) in the repository root to understand how IP versions map across different chips.

### 1.3 Scripts in `scripts/`

The repository contains essential python scripts in the `scripts/` directory to automate boilerplate generation. Please refer to the inline script comments and run them with `--help` for more usage details.

- **`extract_die.py`**: Used when a new architecture (Die) is introduced or when an existing Die needs to be updated. This script parses a canonical SVD file and vendor RCC HAL headers to automatically generate or update the base `peripherals.yaml` and `interrupts.yaml`. You can use the "merge" mode to preserve any subsequent manual overrides you make.
- **`extract_series.py`** and **`extract_all_series.py`**: These scripts automatically compare a series' SVD against its parent Die's canonical config to deduce missing features. They populate `disabled_peripherals` and `disabled_interrupts` in `data/series/<series>.yaml`.

---

## 2. How to Fix Register Issues

If you find a bug where a register is missing, has the wrong offset, or a bitfield enum is incorrect, you need to modify the register YAML.

**Steps:**
1. Check [peripheral_version.md](peripheral_version.md) to determine the specific `version` (e.g. `usart_v1`) of the peripheral for the affected chip.
2. Open the corresponding register file: `data/registers/<kind>_<version>.yaml` (e.g., `data/registers/usart_v1.yaml`). 
*Note: If fixing this issue will break other series sharing this YAML, you should create a new YAML version (e.g., `usart_v2.yaml`) instead of modifying the existing one.*
3. Locate the faulty register or field in the YAML structure.
4. Make the necessary manual corrections:
   - Change `bitOffset` or `bitWidth` if the field is misaligned.
   - Add/modify `enum` key-value pairs if the documented values are incorrect.
   - Add a missing register if it was absent in the original SVD.
   - For more details on the YAML structure and schema, please refer to [embassy-rs/chiptool](https://github.com/embassy-rs/chiptool).
5. Save the file and run `./d gen` in the project root to regenerate the PAC.
6. Verify the generated Rust code in `build/py32-metapac/src/peripherals/`.

---

## 3. How to Fix Chip or Series Issues

Issues here usually involve incorrect memory sizes, missing packages, or features that shouldn't be present on a specific part number.

**Steps to fix a specific chip (e.g., incorrect package):**
1. Open `data/chips/<chip_name>.yaml`.
2. Modify the `packages` list.

**Steps to fix memory layout (Flash/RAM size):**
1. Check the chip's YAML to find its `generic`.
2. Open `data/generics/<generic>.yaml`.
3. Modify the `memory` array (adjust `size`, `address`, or `page_size`). Note that this will affect all chips sharing this generic.

**Steps to fix series features (e.g., a peripheral is documented but not available on this series):**
1. Ensure the series SVD in `svd/` is correct and up to date.
2. Run `python3 scripts/extract_all_series.py` or run `extract_series.py` for the specific series. The script will automatically compute the missing features and update the `data/series/<series>.yaml` file's `disabled_peripherals` list.

**Steps to fix DIE features (e.g., peripheral version, DMA request, interrupt signal, clock configuration is incorrect, or a peripheral is not yet supported):**
1. Locate the corresponding DIE configuration (`data/dies/<DIE>/peripherals.yaml`).
2. Directly modify the peripheral's configuration block to correct the `version`, `block`, `rcc`, or `interrupts` signals, or add the missing peripheral definition entirely.

**Finally:** Run `./d gen` to apply changes.

---

## 4. How to Add New Peripherals

If a DIE has a peripheral that is not currently supported or mapped, follow these steps:

1. Run the following command in the repo root directory to extract all peripherals:
   ```bash
   ./d extract all
   ```
   All peripherals will be exported from the SVD files under `svd/` to `tmp/`.
2. Manually compare the differences in registers for the same peripheral across different families, and change some register fields to enums and arrays. Use the maximum superset.
3. Rename the block name inside the YAML file (e.g., from `I2C1` to `I2C`).
4. Rename the filename to `<peripheral_name>_<version>.yaml` (e.g., `i2c_v1.yaml`, `rcc_f030.yaml`).
5. Convert the file to UTF-8 encoding and move it to `data/registers/`.
6. Complete or add the information for this peripheral in `data/dies/<DIE>/peripherals.yaml`. 
7. Rerun `./d gen` to generate the metapac and check if there are any errors.

---

## 5. How to Add New Chips/Series

Many PY32 series share the same wafer/die (e.g., PY32F030, PY32F003, PY32F002A, PY32M030, PY32C613 share the same die), which greatly reduces workload and increases code reuse.

You can determine whether a chip uses an existing DIE (e.g., `DIE030`, `DIE072`, found in [`data/dies/`](data/dies/)) or a completely new DIE by comparing its naming convention, flash/RAM specifications, and specific peripheral registers extracted from the SVD (refer to [Section 4: How to Add New Peripherals](#4-how-to-add-new-peripherals)).

### 5.A. Based on an Existing DIE

When a new chip/series is released that uses a known silicon die (e.g., a new package or a cut-down version of PY32F030).

**Steps:**
1. **Determine the Series**: Ensure the appropriate Series configuration exists. You can create or update it by running `python3 scripts/extract_all_series.py` or `python3 scripts/extract_series.py` to automatically compute missing peripherals and interrupts against the base DIE.
2. **Determine the Generic**: Check if the memory layout of the new chip matches an existing generic (product line) in `data/generics/`. If not, create a new `data/generics/<new_generic>.yaml` and point its `series` field to the appropriate series.
3. **Create the Chip Config**:
   - Create `data/chips/<new_chip>.yaml` (e.g., `PY32F030F16.yaml`).
   - Specify the `name`, `generic` (product line), `device_id`, and available `packages`:
     ```yaml
     name: PY32F030F16
     generic: PY32F030x6
     device_id: 1234 # (unnecessary)
     packages:
       - name: PY32F030F16P6
         package: TSSOP20
         pins: 20
     ```
4. Run `./d gen` to generate the PAC for the new chip.

---

### 5.B. Based on a Completely New DIE

When a completely new MCU family is introduced with a new architecture or significant silicon changes.

**Steps:**
1. Place the SVD files in `svd/` (e.g., `PY32F072xx.svd`).
2. **Create and Populate the DIE**:
   - Run `python3 scripts/extract_die.py --die <NEW_DIE> --svd svd/<NEW_SVD> --rcc-header /path/to/py32f0xx_hal_rcc.h`. This automatically creates `data/dies/<NEW_DIE>/peripherals.yaml` and `interrupts.yaml`.
   - Manually modify `peripherals.yaml` to adjust the `version` and `block` segments, and manually complete the interrupt signals.
   - Manually create `dma_channels.yaml`, `af.yaml`, and `dma_requests.yaml` in the new DIE folder (these can be extracted and processed from the SDK or the Manual).
   - For any completely new peripherals introduced, ensure their register definitions are added to `data/registers/` (see section 4).
3. **Create the Series**:
   Run `python3 scripts/extract_series.py --die <NEW_DIE> --series <NEW_SERIES> --svd svd/<NEW_SVD>`. This creates `data/series/<new_series>.yaml` and computes disabled features.
4. **Create the Generic(s)**:
   Create `data/generics/<new_generic>.yaml`. Point `series` to the new series created in step 3, and define the memory limits.
5. **Create the Chip(s)**:
   Create `data/chips/<new_chip>.yaml`. Point `generic` to the new generic created in step 4.
6. **Generate and Test**:
   - Run `./d gen`.
   - Then you can develop and test the generated PAC inside the `py32-hal` repository.

---
*Contributions are welcome!*

---

### Other reference

- (In Chinese) [Rust 嵌入式开发中的外设寄存器访问：从 svd2rust 到 chiptool 和 metapac - 以 hpm-data 为例 | 猫·仁波切](https://andelf.github.io/2024/08/23/embedded-rust-peripheral-register-access-svdtools-chiptool-and-metapac-approach/)
