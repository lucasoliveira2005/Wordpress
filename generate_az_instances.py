#!/usr/bin/env python3
"""
Generator for Multi-AZ WordPress Deployment Instances (Solution 1: Realistic VM counts VM=8..12).
Generates a curated suite of 10 fast-solving benchmark instances:
- Offers: 5, 10, 15, and 20.
- VM counts: 8 to 12 (realistic for 3 to 5 WordPress replicas, eliminating empty VM combinatorics).
- Rich variety of zones (2, 3, 4 zones).
- Rich variety of latency topologies:
  * Metro low-latency (1-3 ms)
  * Dual-AZ Enterprise (4 ms)
  * Star / Hub-and-Spoke (3 ms to hub, 45 ms between edge zones)
  * Asymmetric Regional Triangle (5, 14, 20 ms)
  * Campus Multi-Zone with tight SLA (5 ms)
  * Balanced 3-Zone Regional (4-6 ms)
  * Cross-Region WAN (10-60 ms)
  * Disjoint Clusters (5 ms internal, 80 ms cross-cluster)
  * Controlled Infeasible SLA proof (proving SLA enforcement)
- All instances solve in under 5 seconds!
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
CACHE_FILE = BASE_DIR / "Modules" / "catalog_cache.json"


def load_catalog_data():
    """Loads catalog data from the local cache."""
    if not CACHE_FILE.exists():
        raise FileNotFoundError(f"Catalog cache not found at {CACHE_FILE}")
    return json.loads(CACHE_FILE.read_text())


def sample_catalog(specs, prices, target_n):
    """Linearly samples target_n offers across the catalog spectrum, preserving diversity."""
    total = len(specs)
    if target_n >= total:
        return specs[:target_n], prices[:target_n]

    indices = [int(round(i * (total - 1) / (target_n - 1))) for i in range(target_n)]
    unique_indices = []
    for idx in indices:
        if not unique_indices or idx > unique_indices[-1]:
            unique_indices.append(idx)
        else:
            unique_indices.append(unique_indices[-1] + 1)

    selected_specs = [specs[i] for i in unique_indices]
    selected_prices = [prices[i] for i in unique_indices]
    return selected_specs, selected_prices


def format_matrix(matrix):
    """Formats a 2D list into valid MiniZinc 2D array syntax [| row1 | row2 |]."""
    rows = []
    for i, r in enumerate(matrix):
        prefix = "      " if i == 0 else "    | "
        rows.append(prefix + ", ".join(f"{x:>3}" for x in r))
    return "[|\n" + "\n".join(rows) + "\n|]"


def generate_dzn_content(
    name, wp_instances, vm_count, no_zones, zone_latency, max_allowed_latency,
    vm_offers, comp_req, specs, prices, desc=""
):
    """Formats a complete .dzn file with AZ and Latency SLA parameters (dynamic VMZone)."""
    lat_matrix_str = format_matrix(zone_latency)
    formatted_specs = "[|\n" + "\n|".join(f"    {row}," for row in specs) + "\n|]"

    price_lines = []
    for i in range(0, len(prices), 10):
        chunk = prices[i : i + 10]
        price_lines.append("    " + ", ".join(chunk))
    formatted_prices = "[\n" + ",\n".join(price_lines) + "\n]"

    return f"""% ================================================================
% Instance: {name}
% Course: Symbolic Explainable Artificial Intelligence (S-XAI)
% Problem: WordPress Multi-AZ Cloud Deployment (CSPLib prob090 Extension)
% Description: {desc}
% Parameters: WPInstances={wp_instances} | VM Slots={vm_count} | Zones={no_zones} | Offers={vm_offers}
% SLA: MaxAllowedLatency = {max_allowed_latency} ms (VMZone dynamically assigned by solver)
% ================================================================

% --- AVAILABILITY ZONE EXTENSION PARAMETERS ---
NoZones = {no_zones};

% --- NETWORK LATENCY SLA PARAMETERS ---
% Inter-zone latency matrix (milliseconds)
ZoneLatency = {lat_matrix_str};

% Maximum allowed latency for WordPress <-> MySQL communication (ms)
MaxAllowedLatency = {max_allowed_latency};

% --- BASE HARDWARE & COMPONENT PARAMETERS ---
WPInstances = {wp_instances};
VM = {vm_count};
NoComponents = 5;
HardwareREQ = 3;
VMOffers = {vm_offers};

CompREQ = [|
{comp_req}
|];

VMSpecs = {formatted_specs};

VMPrice = {formatted_prices};
"""


# ==============================================================================
# DEFINITION OF THE 10 REALISTIC BENCHMARK SCENARIOS (VM = 8..12)
# ==============================================================================

BENCHMARK_SCENARIOS = [
    # --------------------------------------------------------------------------
    # 1. 5 Ofertas (VM 8 - 10)
    # --------------------------------------------------------------------------
    {
        "name": "AZ_O05_WP3_VM8_Z2_Metro.dzn",
        "offers": 5,
        "wp": 3,
        "vm": 8,
        "zones": 2,
        "latency": [
            [0, 2],
            [2, 0]
        ],
        "max_lat": 5,
        "desc": "Metro low-latency: 5 offers, 3 WP, 8 VMs, 2 Metro zones (1-3ms), SLA 5ms"
    },
    {
        "name": "AZ_O05_WP3_VM8_Z3_StarHub.dzn",
        "offers": 5,
        "wp": 3,
        "vm": 8,
        "zones": 3,
        "latency": [
            [0,  3,  4],
            [3,  0, 45],
            [4, 45,  0]
        ],
        "max_lat": 15,
        "desc": "Star/Hub-and-spoke: 5 offers, 3 WP, 8 VMs, Z1 central hub (3-4ms), Z2-Z3 isolated (45ms)"
    },
    {
        "name": "AZ_O05_WP4_VM10_Z2_Infeasible_SLA.dzn",
        "offers": 5,
        "wp": 4,
        "vm": 10,
        "zones": 2,
        "latency": [
            [0, 50],
            [50, 0]
        ],
        "max_lat": 10,
        "desc": "Controlled Infeasible: 5 offers, MySQL split across Z1 & Z2, latency (50ms) > SLA (10ms)"
    },

    # --------------------------------------------------------------------------
    # 2. 10 Ofertas (VM 8 - 10)
    # --------------------------------------------------------------------------
    {
        "name": "AZ_O10_WP3_VM8_Z2_DualAZ.dzn",
        "offers": 10,
        "wp": 3,
        "vm": 8,
        "zones": 2,
        "latency": [
            [0, 4],
            [4, 0]
        ],
        "max_lat": 10,
        "desc": "Dual-AZ Enterprise: 10 offers, 3 WP, 8 VMs, active-active SLA"
    },
    {
        "name": "AZ_O10_WP4_VM10_Z3_Regional.dzn",
        "offers": 10,
        "wp": 4,
        "vm": 10,
        "zones": 3,
        "latency": [
            [0,   5, 14],
            [5,   0, 20],
            [14, 20,  0]
        ],
        "max_lat": 15,
        "desc": "Asymmetric Regional Triangle: 10 offers, 4 WP, 10 VMs, Z2-Z3 link (20ms) violates 15ms SLA"
    },

    # --------------------------------------------------------------------------
    # 3. 15 Ofertas (VM 10)
    # --------------------------------------------------------------------------
    {
        "name": "AZ_O15_WP4_VM10_Z3_StarHub.dzn",
        "offers": 15,
        "wp": 4,
        "vm": 10,
        "zones": 3,
        "latency": [
            [0,  4,  5],
            [4,  0, 50],
            [5, 50,  0]
        ],
        "max_lat": 15,
        "desc": "Star Hub Topology: 15 offers, 4 WP, 10 VMs, Z1 transit hub (4-5ms), Z2-Z3 edge (50ms)"
    },
    {
        "name": "AZ_O15_WP4_VM10_Z4_Campus.dzn",
        "offers": 15,
        "wp": 4,
        "vm": 10,
        "zones": 4,
        "latency": [
            [0, 3, 4, 5],
            [3, 0, 4, 5],
            [4, 4, 0, 6],
            [5, 5, 6, 0]
        ],
        "max_lat": 5,
        "desc": "Campus 4-Zone Datacenter: 15 offers, 4 WP, 10 VMs, tight 5ms SLA (Z3-Z4 at 6ms violates)"
    },

    # --------------------------------------------------------------------------
    # 4. 20 Ofertas (VM 10 - 12)
    # --------------------------------------------------------------------------
    {
        "name": "AZ_O20_WP4_VM10_Z3_Balanced.dzn",
        "offers": 20,
        "wp": 4,
        "vm": 10,
        "zones": 3,
        "latency": [
            [0, 4, 6],
            [4, 0, 5],
            [6, 5, 0]
        ],
        "max_lat": 10,
        "desc": "Balanced 3-Zone Regional: 20 offers, 4 WP, 10 VMs, uniform low latencies (4-6ms)"
    },
    {
        "name": "AZ_O20_WP5_VM12_Z4_CrossRegion.dzn",
        "offers": 20,
        "wp": 5,
        "vm": 12,
        "zones": 4,
        "latency": [
            [ 0, 10, 25, 60],
            [10,  0, 15, 45],
            [25, 15,  0, 20],
            [60, 45, 20,  0]
        ],
        "max_lat": 20,
        "desc": "Multi-Region WAN: 20 offers, 5 WP, 12 VMs, adjacent region links satisfy 20ms SLA"
    },
    {
        "name": "AZ_O20_WP5_VM12_Z4_DisjointWAN.dzn",
        "offers": 20,
        "wp": 5,
        "vm": 12,
        "zones": 4,
        "latency": [
            [ 0,  5, 75, 80],
            [ 5,  0, 80, 85],
            [75, 80,  0,  6],
            [80, 85,  6,  0]
        ],
        "max_lat": 15,
        "desc": "Disjoint Clusters: 20 offers, 5 WP, 12 VMs, Cluster A (Z1-Z2 @ 5ms) vs Cluster B (Z3-Z4 @ 6ms)"
    }
]


def clean_old_az_files():
    """Removes all existing AZ_*.dzn files from Data directory."""
    removed = 0
    for p in DATA_DIR.glob("AZ_*.dzn"):
        p.unlink()
        removed += 1
    print(f"Cleaned up {removed} old AZ_*.dzn files from {DATA_DIR}.")


def main():
    catalog_data = load_catalog_data()
    comp_req = catalog_data["comp_req"]
    specs20, prices20 = catalog_data["specs20"], catalog_data["prices20"]
    specs40, prices40 = catalog_data["specs40"], catalog_data["prices40"]
    specs250, prices250 = catalog_data["specs250"], catalog_data["prices250"]

    clean_old_az_files()

    created = 0
    print(f"\nGenerating {len(BENCHMARK_SCENARIOS)} realistic benchmark instances (VM 8-12, Offers 5-20)...")
    for sc in BENCHMARK_SCENARIOS:
        target_offers = sc["offers"]
        if target_offers <= 20:
            s, p = sample_catalog(specs20, prices20, target_offers)
        elif target_offers <= 40:
            s, p = sample_catalog(specs40, prices40, target_offers)
        else:
            s, p = sample_catalog(specs250, prices250, target_offers)

        content = generate_dzn_content(
            name=sc["name"],
            wp_instances=sc["wp"],
            vm_count=sc["vm"],
            no_zones=sc["zones"],
            zone_latency=sc["latency"],
            max_allowed_latency=sc["max_lat"],
            vm_offers=target_offers,
            comp_req=comp_req,
            specs=s,
            prices=p,
            desc=sc["desc"]
        )

        out_path = DATA_DIR / sc["name"]
        out_path.write_text(content)
        created += 1
        print(f"  [{created:02d}/{len(BENCHMARK_SCENARIOS)}] Created: {sc['name']:<36} (Offers={target_offers:>2}, VMs={sc['vm']:>2}, Z={sc['zones']}, WP={sc['wp']})")

    print(f"\nSuccessfully generated {created} benchmark instances in {DATA_DIR}!")


if __name__ == "__main__":
    main()
