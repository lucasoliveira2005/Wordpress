import os
import sys
from pathlib import Path
from minizinc import Model, Instance, Solver

from datetime import timedelta
import time


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
        print("\n" + "-" * 65)
        print("CONFIGURACAO DAS MAQUINAS VIRTUAIS")
        print("-" * 65)

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
        cabecalho = "     " + "".join(
            f"{'VM ' + str(j + 1):>6}"
            for j in range(len(matriz[0]))
        )
        print(cabecalho)

        for i, linha in enumerate(matriz):
            valores = "".join(f"{valor:>6}" for valor in linha)
            print(f"{'C' + str(i + 1):>4} {valores}")

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
