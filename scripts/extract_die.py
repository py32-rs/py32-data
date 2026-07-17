#!/usr/bin/env python3
"""
Extract Die Configuration Script
--------------------------------
This script extracts peripheral and interrupt configurations for a specific Die
by parsing a target SVD file and a vendor RCC HAL header file.

Usage:
  python3 scripts/extract_die.py --die DIE030 --svd svd/PY32F030xx.svd --rcc-header /path/to/CSDK/py32f0xx_hal_rcc.h

Smart Merge Feature:
  If `data/dies/DIExxx/peripherals.yaml` already exists, this script will NOT overwrite
  manually maintained fields like `pins` and `dma_channels`. It will only update the
  `address`, `rcc` fields, and missing `interrupts` while preserving everything else.
"""

import argparse
import os
import re
import yaml
import xml.etree.ElementTree as ET

class HexInt(int): pass

def representer(dumper, data):
    return yaml.ScalarNode('tag:yaml.org,2002:int', hex(data))

yaml.add_representer(HexInt, representer)

def get_rcc_h_define(file_path):
    enable_dict = {}
    reset_dict = {}

    if not file_path or not os.path.exists(file_path):
        print(f"Warning: RCC header file not found at {file_path}. Skipping RCC extraction.")
        return enable_dict, reset_dict

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        h_file = file.read().replace(" \\\n", "")

    for line in h_file.splitlines():
        if "__HAL_RCC_" in line:
            if "_FORCE_RESET" in line and "SET_BIT" in line:
                match = re.search(r'__HAL_RCC_(.*)_FORCE_RESET', line)
                if match:
                    device_name = match.group(1)
                    variables_match = re.search(r'SET_BIT\((.*?), (.*?)\)', line)
                    if variables_match:
                        variables = variables_match.groups()
                        register = variables[0].split('->')[-1].strip()
                        field = variables[1].split('_')[-1].strip()
                        reset_dict[device_name] = {
                            "register": register,
                            "field": field
                        }

            elif "_CLK_ENABLE()" in line and "SET_BIT" in line:
                match = re.search(r'__HAL_RCC_(.*)_CLK_', line)
                if match:
                    device_name = match.group(1)
                    variables_match = re.search(r'SET_BIT\((.*?), (.*?)\)', line)
                    if variables_match:
                        variables = variables_match.groups()
                        register = variables[0].split('->')[-1].strip()
                        field = variables[1].split('_')[-1].strip()
                        enable_dict[device_name] = {
                            "register": register,
                            "field": field
                        }

    return enable_dict, reset_dict

def parse_svd(svd_path):
    if not os.path.exists(svd_path):
        print(f"Error: SVD file not found at {svd_path}.")
        exit(1)

    tree = ET.parse(svd_path)
    root = tree.getroot()
    peripherals = root.find('peripherals')

    svd_peripherals = []
    global_interrupts = {}
    group_name_dict = {}

    for peripheral in peripherals:
        p_dict = {}
        name_elem = peripheral.find('name')
        if name_elem is None:
            continue
        name = name_elem.text
        p_dict['name'] = name

        derived_from = peripheral.get('derivedFrom')
        group_name = ""
        if derived_from:
            group_name = group_name_dict.get(derived_from, "")
        elif peripheral.find('groupName') is not None:
            group_name = peripheral.find('groupName').text.lower()
        else:
            # Fallback heuristic
            if name.startswith("TIM"):
                group_name = "tim"
            elif name.startswith("USART"):
                group_name = "usart"
            else:
                group_name = name.lower()
        
        group_name_dict[name] = group_name
        p_dict['groupName'] = group_name

        addr_elem = peripheral.find('baseAddress')
        if addr_elem is not None:
            p_dict['address'] = HexInt(int(addr_elem.text, 16))

        ints = peripheral.findall('interrupt')
        if ints:
            p_dict['interrupts'] = []
            for i in ints:
                i_name = i.find('name').text
                i_val = int(i.find('value').text)
                global_interrupts[i_name] = i_val
                p_dict['interrupts'].append(i_name)

        svd_peripherals.append(p_dict)

    # Some interrupts might be defined globally or in the CPU section (rare in these SVDs but possible)
    # We rely on peripheral interrupts for now.
    
    return svd_peripherals, global_interrupts

def merge_and_write(die, svd_peripherals, global_interrupts, enable_dict, reset_dict):
    out_dir = os.path.join("data", "dies", die)
    os.makedirs(out_dir, exist_ok=True)

    peri_yaml = os.path.join(out_dir, "peripherals.yaml")
    int_yaml = os.path.join(out_dir, "interrupts.yaml")

    # 1. Load existing peripherals to preserve manual overrides
    existing_peripherals = []
    if os.path.exists(peri_yaml):
        try:
            with open(peri_yaml, 'r', encoding='utf-8') as f:
                existing_peripherals = yaml.safe_load(f) or []
        except Exception as e:
            print(f"Warning: Failed to parse existing {peri_yaml}: {e}")

    final_peripherals = []
    
    # Map old peripherals by address and name for correlation
    old_by_addr = {p.get('address'): p for p in existing_peripherals if 'address' in p}
    old_by_name = {p['name']: p for p in existing_peripherals if 'name' in p}
    processed_old_names = set()

    for svd_p in svd_peripherals:
        svd_name = svd_p['name']
        svd_addr = svd_p.get('address')
        
        # Match by address first (e.g. SVD ADC = 0x40012400 matches old ADC1 = 0x40012400)
        old_p = old_by_addr.get(svd_addr) or old_by_name.get(svd_name) or {}
        name = old_p.get('name', svd_name)
        
        if name in processed_old_names:
            continue
        processed_old_names.add(name)
        
        new_p = {
            'name': name,
            'address': svd_addr or old_p.get('address', 0)
        }

        # Keep manual 'registers' fields: kind, version, block
        old_regs = old_p.get('registers', {})
        kind = old_regs.get('kind', svd_p.get('groupName', svd_name.lower()) or svd_name.lower())
        version = old_regs.get('version', 'common')
        block = old_regs.get('block', 'TODO')
        
        new_p['registers'] = {
            'kind': kind,
            'version': version,
            'block': block
        }


        # Merge rcc
        rcc_block = old_p.get('rcc', {}).copy()
        if 'bus_clock' not in rcc_block:
            rcc_block['bus_clock'] = 'PCLK1'
        if 'kernel_clock' not in rcc_block:
            rcc_block['kernel_clock'] = rcc_block['bus_clock']
        
        # Look up RCC enables/resets by SVD name and fallback to old name
        rcc_name = None
        if svd_name in enable_dict or svd_name in reset_dict:
            rcc_name = svd_name
        elif name in enable_dict or name in reset_dict:
            rcc_name = name
            
        if rcc_name:
            if rcc_name in enable_dict:
                rcc_block['enable'] = enable_dict[rcc_name]
            if rcc_name in reset_dict:
                rcc_block['reset'] = reset_dict[rcc_name]
                
        # Only add rcc if it existed before or if we found an enable/reset
        if 'enable' in rcc_block or 'rcc' in old_p:
            new_p['rcc'] = rcc_block

        # Merge interrupts
        svd_ints = svd_p.get('interrupts', [])
        old_ints = old_p.get('interrupts', [])
        
        merged_ints = []
        old_int_names = {oi.get('interrupt'): oi for oi in old_ints}
        
        # Keep ALL old interrupts intact exactly as they were manually defined
        for oi in old_ints:
            merged_ints.append(oi)
            
        # Append any newly discovered SVD interrupts
        for i_name in svd_ints:
            if i_name not in old_int_names:
                merged_ints.append({'signal': 'GLOBAL', 'interrupt': i_name})
                
        if merged_ints:
            new_p['interrupts'] = merged_ints

        final_peripherals.append(new_p)

    # Append any old peripherals that were NOT in the SVD at all (e.g., UID, CONFIGBYTES)
    for old_p in existing_peripherals:
        if old_p['name'] not in processed_old_names:
            final_peripherals.append(old_p)
            processed_old_names.add(old_p['name'])
            
    # Sort by address for consistency
    final_peripherals.sort(key=lambda x: x.get('address', 0) if isinstance(x.get('address'), int) else 0)

    # Custom Dump to enforce nice block syntax
    yaml.Dumper.ignore_aliases = lambda self, data: True
    
    with open(peri_yaml, 'w', encoding='utf-8') as f:
        yaml_str = yaml.dump(final_peripherals, default_flow_style=False, allow_unicode=True, sort_keys=False, Dumper=yaml.Dumper)
        # Add blank lines between items for readability
        yaml_str = yaml_str.replace("- name:", "\n- name:")
        f.write(yaml_str.strip() + "\n")
    print(f"Updated: {peri_yaml}")

    # Write interrupts.yaml
    int_list = []
    for i_name, i_val in sorted(global_interrupts.items(), key=lambda x: x[1]):
        int_list.append({'name': i_name, 'number': i_val})

    with open(int_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(int_list, f, default_flow_style=False, sort_keys=False, Dumper=yaml.Dumper)
    print(f"Updated: {int_yaml}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Die Peripheral and Interrupt data from SVD and Header.")
    parser.add_argument("--die", required=True, help="Target Die (e.g., DIE030)")
    parser.add_argument("--svd", required=True, help="Path to SVD file")
    parser.add_argument("--rcc-header", required=False, help="Path to RCC HAL header file")
    args = parser.parse_args()

    enable_dict, reset_dict = get_rcc_h_define(args.rcc_header)
    svd_peripherals, global_interrupts = parse_svd(args.svd)
    
    merge_and_write(args.die, svd_peripherals, global_interrupts, enable_dict, reset_dict)
    print(f"Extraction for {args.die} completed successfully!")
