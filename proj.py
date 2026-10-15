import os
import sys
from pathlib import Path
from minizinc import Model, Instance, Solver
from datetime import timedelta
import time
import re

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"

MODELO_MZN = BASE_DIR / "Wordpress.mzn"
SOLVER_NAME = "gecode"


def list_dzn_files():
    """Finds and sorts all .dzn files in the Data directory."""
    files = sorted(DATA_DIR.glob("*.dzn"))
    return files


def select_dzn_file(files):
    """Displays the menu and returns the user's choice."""
    if not files:
        print(f"No '.dzn' files found in: {DATA_DIR}")
        sys.exit(1)

    print("\n--- INPUT DATASET (.dzn) ---")

    for i, file in enumerate(files, 1):
        print(f"[{i:02d}] {file.name}")

    print("---------------------------------------")

    while True:
        try:
            choice = int(input("Select the input file: "))

            if 1 <= choice <= len(files):
                return files[choice - 1]

            print(f"Please choose a number between 1 and {len(files)}.")

        except ValueError:
            print("Invalid input. Please enter an integer.")


def solve(modelo_path, ficheiro_dzn, solver_name="gecode"):
    """Loads the model and data, and executes the solver."""

    if not modelo_path.is_file():
        print(f"Error: model file not found: {modelo_path}")
        sys.exit(1)

    print(f"\nModel : {modelo_path.name}")
    print(f"Data  : {ficheiro_dzn.name}")
    print(f"Solver: {solver_name}")

    # Load main model
    modelo = Model(str(modelo_path))

    # Add dataset file
    modelo.add_file(str(ficheiro_dzn))

    # Solver lookup
    solver = Solver.lookup(solver_name)

    instancia = Instance(solver, modelo)
    dzn_text = ficheiro_dzn.read_text()

    print("\nSolving (timeout: 600 seconds)...", flush=True)

    start_time = time.perf_counter()
    resultado = instancia.solve(time_limit=timedelta(seconds=600), verbose=True)
    end_time = time.perf_counter()

    # Display results
    print("\n" + "=" * 65)
    print("                 RESULTS")
    print("=" * 65)

    print(f"Solution status   : {resultado.status}")
    print(f"Objective (Price) : {resultado.objective}")
    print(f"Execution time    : {end_time - start_time:.2f} seconds")

    if resultado.solution is not None:
        sol = resultado.solution

        # 1. Virtual Machine Configuration
        print("\n" + "-" * 75)
        print("VIRTUAL MACHINE CONFIGURATION")
        print("-" * 75)

        # Retrieve VMZone from solver decision variable
        vm_zones = list(sol.VMZone) if hasattr(sol, "VMZone") and sol.VMZone is not None else None

        if vm_zones:
            print(
                f"{'VM':>4} {'Zone':>6} {'Type':>6} {'CPU':>6} "
                f"{'Memory':>10} {'Storage':>10} {'Price':>8}"
            )
            print("-" * 60)
            for i in range(len(sol.VMType)):
                z_str = f"Z{vm_zones[i]}" if i < len(vm_zones) else "-"
                print(
                    f"{i + 1:>4} "
                    f"{z_str:>6} "
                    f"{sol.VMType[i]:>6} "
                    f"{sol.CPU[i]:>6} "
                    f"{sol.Memory[i]:>10} "
                    f"{sol.Storage[i]:>10} "
                    f"{sol.Price[i]:>8}"
                )
        else:
            print(
                f"{'VM':>4} {'Type':>6} {'CPU':>6} "
                f"{'Memory':>10} {'Storage':>10} {'Price':>8}"
            )
            print("-" * 50)
            for i in range(len(sol.VMType)):
                print(
                    f"{i + 1:>4} "
                    f"{sol.VMType[i]:>6} "
                    f"{sol.CPU[i]:>6} "
                    f"{sol.Memory[i]:>10} "
                    f"{sol.Storage[i]:>10} "
                    f"{sol.Price[i]:>8}"
                )

        # 2. Assignment Matrix
        print("\n" + "-" * 65)
        print("ASSIGNMENT MATRIX")
        print("-" * 65)

        matriz = sol.AssignmentMatrix
        comp_labels = ["WordPress", "MySQL", "DNS_LB", "HTTP_LB", "Varnish"]

        # Build column header with VM and Zone (e.g. VM 1 (Z1))
        col_headers = []
        for j in range(len(matriz[0])):
            if vm_zones and j < len(vm_zones):
                col_headers.append(f"VM {j+1}(Z{vm_zones[j]})")
            else:
                col_headers.append(f"VM {j+1}")

        header_str = "              " + "".join(f"{h:>11}" for h in col_headers)
        print(header_str)
        print("              " + "-" * (len(header_str) - 14))

        for i, linha in enumerate(matriz):
            c_name = comp_labels[i] if i < len(comp_labels) else f"Comp {i+1}"
            valores = "".join(f"{valor:>11}" for valor in linha)
            print(f"{c_name:<14}{valores}")

        # 3. Latency SLA Verification (WordPress <-> MySQL)
        match_max_lat = re.search(r"MaxAllowedLatency\s*=\s*(\d+);", dzn_text)
        lat_match = re.search(r"ZoneLatency\s*=\s*\[\|([\s\S]*?)\|\];", dzn_text)
        if match_max_lat and lat_match:
            max_sla = int(match_max_lat.group(1))
            lat_rows = [
                [int(x.strip()) for x in row.split(",") if x.strip()]
                for row in lat_match.group(1).split("|")
                if row.strip()
            ]
            print("\n" + "-" * 75)
            print("NETWORK LATENCY SLA VERIFICATION (WordPress <-> MySQL)")
            print("-" * 75)
            print(f"Maximum Allowed SLA: {max_sla} ms")
            wp_vms = [j for j in range(len(matriz[0])) if matriz[0][j] == 1]
            db_vms = [j for j in range(len(matriz[1])) if matriz[1][j] == 1]
            if wp_vms and db_vms and vm_zones:
                print(f"{'WordPress':>16} {'MySQL':>16} {'Latency':>12} {'SLA Status':>16}")
                print("-" * 65)
                all_ok = True
                for wp_idx in wp_vms:
                    for db_idx in db_vms:
                        z_wp = vm_zones[wp_idx]
                        z_db = vm_zones[db_idx]
                        lat = lat_rows[z_wp - 1][z_db - 1]
                        ok = lat <= max_sla
                        if not ok:
                            all_ok = False
                        status_str = f"PASS (<= {max_sla}ms)" if ok else f"FAIL (> {max_sla}ms)"
                        print(f"VM {wp_idx+1} (Z{z_wp}){'':>7} VM {db_idx+1} (Z{z_db}){'':>7} {lat:>4} ms {'':>4} {status_str}")
                if all_ok:
                    print(f"\n[OK] All WordPress <-> MySQL pairs comply with the {max_sla} ms SLA!")

    else:
        print("\nNo solution found.")

    # 4. Statistics
    print("\n" + "-" * 65)
    print("EXECUTION STATISTICS")
    print("-" * 65)

    estatisticas = resultado.statistics

    for chave in sorted(estatisticas):
        valor = estatisticas[chave]

        if isinstance(valor, timedelta):
            valor = f"{valor.total_seconds():.4f} s"

        print(f"{chave:<35} : {valor}")

    print("=" * 65)


if __name__ == "__main__":
    files = list_dzn_files()
    chosen_dzn = select_dzn_file(files)

    solve(
        modelo_path=MODELO_MZN,
        ficheiro_dzn=chosen_dzn,
        solver_name=SOLVER_NAME
    )
