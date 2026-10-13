#!/usr/bin/env python3
"""
Generator for Multi-AZ WordPress Deployment Instances (Phase 1 Extension).
Loads authentic hardware catalogs from the respective base files:
- 20 offers from Wordpress_Offers20.dzn
- 40 offers from Wordpress_Offers40.dzn
- 250 offers from Wordpress_Offers250.dzn
- 500 offers from Wordpress_Offers500.dzn
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"

CATALOG_FILES = {
    20: DATA_DIR / "Wordpress_Offers20.dzn",
    30: DATA_DIR / "Wordpress_Offers40.dzn",   # slice 30 from Offers40
    40: DATA_DIR / "Wordpress_Offers40.dzn",
    50: DATA_DIR / "Wordpress_Offers250.dzn",  # slice 50 from Offers250
    250: DATA_DIR / "Wordpress_Offers250.dzn",
    500: DATA_DIR / "Wordpress_Offers500.dzn",
}


def load_catalog(offer_count):
    src_file = CATALOG_FILES[offer_count]
    content = src_file.read_text()

    comp_match = re.search(r"CompREQ\s*=\s*\[\|([\s\S]*?)\|\];", content)
    specs_match = re.search(r"VMSpecs\s*=\s*\[\|([\s\S]*?)\|\];", content)
    price_match = re.search(r"VMPrice\s*=\s*\[([\s\S]*?)\];", content)

    comp_req = comp_match.group(1).strip()
    spec_rows = [
        r.strip().rstrip("|").strip()
        for r in specs_match.group(1).split("|")
        if r.strip()
    ]
    prices = [
        p.strip()
        for p in price_match.group(1).replace("\n", " ").split(",")
        if p.strip()
    ]

    return comp_req, spec_rows[:offer_count], prices[:offer_count]


def generate_dzn_content(
    name, wp_instances, vm_count, no_zones, vm_zone, vm_offers, comp_req, spec_rows, prices
):
    specs_str = "    " + "\n|   ".join(spec_rows)
    prices_formatted = []
    chunk_size = 10
    for i in range(0, len(prices), chunk_size):
        prices_formatted.append(", ".join(prices[i : i + chunk_size]))
    price_str = ",\n    ".join(prices_formatted)

    vm_zone_str = "[" + ", ".join(map(str, vm_zone)) + "]"

    return f"""% ================================================================
% Instance: {name}
% Course: Symbolic Explainable Artificial Intelligence (S-XAI)
% Problem: WordPress Multi-AZ Cloud Deployment (CSPLib prob090 Extension)
% WPInstances: {wp_instances} | VM Slots: {vm_count} | Zones: {no_zones} | Offers: {vm_offers}
% ================================================================

% --- AVAILABILITY ZONE EXTENSION PARAMETERS ---
NoZones = {no_zones};
VMZone = {vm_zone_str};

% --- BASE HARDWARE & COMPONENT PARAMETERS ---
WPInstances = {wp_instances};
VM = {vm_count};
NoComponents = 5;
HardwareREQ = 3;
VMOffers = {vm_offers};

CompREQ = [|
{comp_req}
|];

VMSpecs = [|
{specs_str}
|];

VMPrice = [
    {price_str}
];
"""


def build_zone_distribution(vm_count, counts_per_zone):
    assert sum(counts_per_zone) == vm_count, f"Zone counts {counts_per_zone} must sum to {vm_count}"
    zone_list = []
    for zone_id, count in enumerate(counts_per_zone, 1):
        zone_list.extend([zone_id] * count)
    return zone_list


def main():
    instances = [
        # Tier 1: Small (3 instances)
        {
            "filename": "AZ_Small_WP3_VM8_Z2_Offers20.dzn",
            "wp": 3, "vm": 8, "no_zones": 2, "zone_counts": [4, 4], "offers": 20,
        },
        {
            "filename": "AZ_Small_WP3_VM8_Z3_Offers20.dzn",
            "wp": 3, "vm": 8, "no_zones": 3, "zone_counts": [3, 3, 2], "offers": 20,
        },
        {
            "filename": "AZ_Small_WP3_VM6_Z2_Offers20_tight.dzn",
            "wp": 3, "vm": 6, "no_zones": 2, "zone_counts": [3, 3], "offers": 20,
        },

        # Tier 2: Medium (9 instances, 30-50 offers)
        {
            "filename": "AZ_Med_WP4_VM10_Z2_Offers40.dzn",
            "wp": 4, "vm": 10, "no_zones": 2, "zone_counts": [5, 5], "offers": 40,
        },
        {
            "filename": "AZ_Med_WP5_VM12_Z3_Offers30.dzn",
            "wp": 5, "vm": 12, "no_zones": 3, "zone_counts": [4, 4, 4], "offers": 30,
        },
        {
            "filename": "AZ_Med_WP5_VM12_Z3_Offers40_imb.dzn",
            "wp": 5, "vm": 12, "no_zones": 3, "zone_counts": [6, 3, 3], "offers": 40,
        },
        {
            "filename": "AZ_Med_WP6_VM14_Z3_Offers40.dzn",
            "wp": 6, "vm": 14, "no_zones": 3, "zone_counts": [5, 5, 4], "offers": 40,
        },
        {
            "filename": "AZ_Med_WP6_VM14_Z4_Offers50.dzn",
            "wp": 6, "vm": 14, "no_zones": 4, "zone_counts": [4, 4, 3, 3], "offers": 50,
        },
        {
            "filename": "AZ_Med_WP7_VM15_Z2_Offers40.dzn",
            "wp": 7, "vm": 15, "no_zones": 2, "zone_counts": [8, 7], "offers": 40,
        },
        {
            "filename": "AZ_Med_WP7_VM15_Z3_Offers40.dzn",
            "wp": 7, "vm": 15, "no_zones": 3, "zone_counts": [5, 5, 5], "offers": 40,
        },
        {
            "filename": "AZ_Med_WP7_VM15_Z3_Offers50_imb.dzn",
            "wp": 7, "vm": 15, "no_zones": 3, "zone_counts": [8, 4, 3], "offers": 50,
        },
        {
            "filename": "AZ_Med_WP8_VM18_Z4_Offers50.dzn",
            "wp": 8, "vm": 18, "no_zones": 4, "zone_counts": [5, 5, 4, 4], "offers": 50,
        },

        # Tier 3: Large (4 instances)
        {
            "filename": "AZ_Large_WP8_VM19_Z3_Offers250.dzn",
            "wp": 8, "vm": 19, "no_zones": 3, "zone_counts": [7, 6, 6], "offers": 250,
        },
        {
            "filename": "AZ_Large_WP10_VM23_Z3_Offers500.dzn",
            "wp": 10, "vm": 23, "no_zones": 3, "zone_counts": [8, 8, 7], "offers": 500,
        },
        {
            "filename": "AZ_Large_WP10_VM23_Z4_Offers500.dzn",
            "wp": 10, "vm": 23, "no_zones": 4, "zone_counts": [6, 6, 6, 5], "offers": 500,
        },
        {
            "filename": "AZ_Large_WP12_VM26_Z3_Offers500_imb.dzn",
            "wp": 12, "vm": 26, "no_zones": 3, "zone_counts": [13, 8, 5], "offers": 500,
        },
    ]

    for inst in instances:
        comp_req, spec_rows, prices = load_catalog(inst["offers"])
        vm_zone = build_zone_distribution(inst["vm"], inst["zone_counts"])
        dzn_text = generate_dzn_content(
            name=inst["filename"],
            wp_instances=inst["wp"],
            vm_count=inst["vm"],
            no_zones=inst["no_zones"],
            vm_zone=vm_zone,
            vm_offers=inst["offers"],
            comp_req=comp_req,
            spec_rows=spec_rows,
            prices=prices,
        )
        out_path = DATA_DIR / inst["filename"]
        out_path.write_text(dzn_text)

    print(f"Successfully generated all {len(instances)} test instances using proper base catalogs.")


if __name__ == "__main__":
    main()
