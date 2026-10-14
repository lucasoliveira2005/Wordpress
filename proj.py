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
    """Procura e ordena os ficheiros .dzn na pasta Data."""
    ficheiros = sorted(DATA_DIR.glob("*.dzn"))
    return ficheiros


def select_dzn_file(ficheiros):
    """Apresenta o menu e obtém a escolha do utilizador."""
    if not ficheiros:
        print(f"Nenhum ficheiro '.dzn' encontrado em: {DATA_DIR}")
        sys.exit(1)

    print("\n--- INPUT DATASET (.dzn) ---")

    for i, ficheiro in enumerate(ficheiros, 1):
        print(f"[{i}] {ficheiro.name}")

    print("---------------------------------------")

    while True:
        try:
            escolha = int(
                input("Selecione o ficheiro de input: ")
            )

            if 1 <= escolha <= len(ficheiros):
                return ficheiros[escolha - 1]

            print(f"Escolha um número entre 1 e {len(ficheiros)}.")

        except ValueError:
            print("Entrada inválida. Introduza um número inteiro.")


def solve(modelo_path, ficheiro_dzn, solver_name="gecode"):
    """Carrega o modelo e os dados e executa o solver."""

    if not modelo_path.is_file():
        print(f"Erro: modelo não encontrado: {modelo_path}")
        sys.exit(1)

    print(f"\nModelo: {modelo_path.name}")
    print(f"Dados:  {ficheiro_dzn.name}")
    print(f"Solver: {solver_name}")

    # Carregar o modelo principal
    modelo = Model(str(modelo_path))

    # Associar o ficheiro de dados
    modelo.add_file(str(ficheiro_dzn))

    # Solver
    solver = Solver.lookup(solver_name)

    instancia = Instance(solver, modelo)

    # Check if the .dzn has AZ parameters (legacy fallback)
    dzn_text = ficheiro_dzn.read_text()
    if "NoZones" not in dzn_text:
        instancia["NoZones"] = 1

    if "MaxAllowedLatency" not in dzn_text:
        match_zones = re.search(r"NoZones\s*=\s*(\d+);", dzn_text)
        no_zones = int(match_zones.group(1)) if match_zones else 1
        instancia["MaxAllowedLatency"] = 999999
        instancia["ZoneLatency"] = [[0] * no_zones for _ in range(no_zones)]
    print("\nSolving (limite: 600 segundos)...", flush=True)
    
    inicio = time.perf_counter()
    #resultado = instancia.solve()
    resultado = instancia.solve(time_limit=timedelta(seconds=600), verbose=True)
    fim = time.perf_counter()

    '''
    # 5. Apresentar os resultados
    print("\n--- RESULTADO ---")

    if resultado.solution is not None:
        print(resultado.solution)
    else:
        print("Nenhuma solução encontrada.")


    print(f"Tempo de execução: {fim - inicio:.2f} segundos")
    print(f"\nEstado da resolução: {resultado.status}")
    print("Objetivo:", resultado.objective)
    print("Estatísticas:", resultado.statistics)
    '''

    # Apresentar os resultados
    print("\n" + "=" * 65)
    print("                 RESULTADOS")
    print("=" * 65)

    print(f"Solução             : {resultado.status}")
    print(f"Objetivo            : {resultado.objective}")
    print(f"Tempo de execucao   : {fim - inicio:.2f} segundos")

    if resultado.solution is not None:
        sol = resultado.solution

        # 1. Configuracao das VMs
        print("\n" + "-" * 75)
        print("CONFIGURACAO DAS MAQUINAS VIRTUAIS")
        print("-" * 75)

        # Retrieve VMZone: first from solver decision variable (sol.VMZone)
        vm_zones = None
        if hasattr(sol, "VMZone") and sol.VMZone is not None:
            vm_zones = list(sol.VMZone)
        else:
            try:
                vm_zones = list(instancia["VMZone"])
            except Exception:
                pass
            if not vm_zones:
                match_vz = re.search(r"VMZone\s*=\s*\[([\s\S]*?)\];", dzn_text)
                if match_vz:
                    raw_vz = re.sub(r"\s+", "", match_vz.group(1))
                    vm_zones = [int(x) for x in raw_vz.split(",") if x]

        if vm_zones:
            print(
                f"{'VM':>4} {'Zona':>6} {'Tipo':>6} {'CPU':>6} "
                f"{'Memoria':>10} {'Storage':>10} {'Preco':>8}"
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
                f"{'VM':>4} {'Tipo':>6} {'CPU':>6} "
                f"{'Memoria':>10} {'Storage':>10} {'Preco':>8}"
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

        # 2. Matriz de atribuicao
        print("\n" + "-" * 65)
        print("MATRIZ DE ATRIBUICAO")
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



        # 3. Verificacao de Latencia SLA (se aplicavel)
        match_max_lat = re.search(r"MaxAllowedLatency\s*=\s*(\d+);", dzn_text)
        lat_match = re.search(r"ZoneLatency\s*=\s*\[\|([\s\S]*?)\|\];", dzn_text)
        if match_max_lat and lat_match and int(match_max_lat.group(1)) < 999999:
            max_sla = int(match_max_lat.group(1))
            lat_rows = [
                [int(x.strip()) for x in row.split(",") if x.strip()]
                for row in lat_match.group(1).split("|")
                if row.strip()
            ]
            print("\n" + "-" * 75)
            print("VERIFICACAO DE LATENCIA SLA (WordPress <-> MySQL)")
            print("-" * 75)
            print(f"SLA Maximo Permitido: {max_sla} ms")
            wp_vms = [j for j in range(len(matriz[0])) if matriz[0][j] == 1]
            db_vms = [j for j in range(len(matriz[1])) if matriz[1][j] == 1]
            if wp_vms and db_vms and vm_zones:
                print(f"{'WordPress':>16} {'MySQL':>16} {'Latencia':>12} {'SLA Status':>16}")
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
                    print(f"\n[OK] Todos os pares WordPress <-> MySQL cumprem o SLA de {max_sla} ms!")

    else:
        print("\nNenhuma solucao encontrada.")

    # 3. Estatisticas
    print("\n" + "-" * 65)
    print("ESTATISTICAS DA EXECUCAO")
    print("-" * 65)

    estatisticas = resultado.statistics

    for chave in sorted(estatisticas):
        valor = estatisticas[chave]

        if isinstance(valor, timedelta):
            valor = f"{valor.total_seconds():.4f} s"

        print(f"{chave:<35} : {valor}")

    print("=" * 65)


if __name__ == "__main__":
    ficheiros = list_dzn_files()
    dzn_escolhido = select_dzn_file(ficheiros)

    solve(
        modelo_path=MODELO_MZN,
        ficheiro_dzn=dzn_escolhido,
        solver_name=SOLVER_NAME
    )