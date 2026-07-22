#!/usr/bin/env python3
"""
Extract Series Configuration Script
-----------------------------------
This script generates or updates the series configuration YAML (e.g., PY32F003.yaml)
by comparing the Series' SVD file against the target Die's canonical definitions.

Usage:
  python3 scripts/extract_series.py --die DIE030 --series PY32F003 --svd svd/PY32F003xx.svd

Logic:
  It identifies missing peripherals and missing interrupts in the SVD compared to the Die,
  and updates `disabled_peripherals` and `disabled_interrupts` in `data/series/<series>.yaml`
  while preserving other top-level keys like `family`.
"""

import argparse
import os
import yaml
import xml.etree.ElementTree as ET

def extract_series(die, series, svd_path):
    peri_yaml = os.path.join("data", "dies", die, "peripherals.yaml")
    int_yaml = os.path.join("data", "dies", die, "interrupts.yaml")

    if not os.path.exists(peri_yaml) or not os.path.exists(int_yaml):
        print(f"Error: Canonical Die config missing at {peri_yaml} or {int_yaml}")
        exit(1)
        
    if not os.path.exists(svd_path):
        print(f"Error: Series SVD missing at {svd_path}")
        exit(1)

    # 1. Load Canonical Die lists
    die_peris = []
    with open(peri_yaml, 'r', encoding='utf-8') as f:
        die_peris = yaml.safe_load(f) or []
            
    die_ints = set()
    with open(int_yaml, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or []
        for i in data:
            die_ints.add(i['name'])

    # 2. Extract SVD lists
    tree = ET.parse(svd_path)
    root = tree.getroot()
    svd_peris_names = set()
    svd_peris_addrs = set()
    svd_peris_list = []
    svd_ints = set()
    
    for peripheral in root.findall(".//peripheral"):
        name_elem = peripheral.find('name')
        addr_elem = peripheral.find('baseAddress')
        
        name = name_elem.text if name_elem is not None else None
        addr = int(addr_elem.text, 16) if addr_elem is not None else None
        
        if name:
            svd_peris_names.add(name)
            svd_peris_list.append({'name': name, 'address': addr})
        if addr is not None:
            svd_peris_addrs.add(addr)
            
        for interrupt in peripheral.findall('interrupt'):
            i_elem = interrupt.find('name')
            if i_elem is not None:
                svd_ints.add(i_elem.text)
                
    # 3. Calculate differences
    die_peris_names = {p['name'] for p in die_peris}
    die_peris_addrs = {p['address'] for p in die_peris if 'address' in p}
    
    extra_peripherals = []
    for sp in svd_peris_list:
        if sp['name'] not in die_peris_names and sp.get('address') not in die_peris_addrs:
            extra_peripherals.append(sp['name'])
            
    if extra_peripherals:
        print(f"WARNING: Series SVD contains peripherals not found in Die {die}: {', '.join(extra_peripherals)}")
        
    disabled_peripherals = []
    for p in die_peris:
        name = p['name']
        addr = p.get('address')
        
        # Protect custom manual peripherals from being disabled
        if name in ['UID', 'CONFIGBYTES']:
            continue
            
        # Address matching is primary, name matching is fallback
        if addr in svd_peris_addrs or name in svd_peris_names:
            continue
            
        disabled_peripherals.append(name)
        
    disabled_peripherals = sorted(disabled_peripherals)
    disabled_interrupts = sorted(list(die_ints - svd_ints))
    
    # 4. Update series YAML
    series_yaml = os.path.join("data", "series", f"{series}.yaml")
    os.makedirs(os.path.dirname(series_yaml), exist_ok=True)
    
    series_config = {}
    if os.path.exists(series_yaml):
        with open(series_yaml, 'r', encoding='utf-8') as f:
            series_config = yaml.safe_load(f) or {}
            
    series_config['die'] = die
    series_config['disabled_peripherals'] = disabled_peripherals
    series_config['disabled_interrupts'] = disabled_interrupts
    
    # Custom Yaml dump without aliases
    yaml.Dumper.ignore_aliases = lambda self, data: True
    
    with open(series_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(series_config, f, default_flow_style=False, sort_keys=False, Dumper=yaml.Dumper)
        
    print(f"Updated {series_yaml}")
    print(f" - Disabled Peripherals: {len(disabled_peripherals)}")
    print(f" - Disabled Interrupts: {len(disabled_interrupts)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Series diffs against a Die canonical config.")
    parser.add_argument("--die", required=True, help="Target Die (e.g., DIE030)")
    parser.add_argument("--series", required=True, help="Series name (e.g., PY32F003)")
    parser.add_argument("--svd", required=True, help="Path to Series SVD file")
    
    args = parser.parse_args()
    extract_series(args.die, args.series, args.svd)
