import pandas as pd

# lideres = [
#     {"Almoxarifado": "Almox Corte e Estamparia", "Setor": "MP", "Líder": "ALEX"},
#     {"Almoxarifado": "Almox Corte e Estamparia", "Setor": "PEÇA", "Líder": "ALEX"},
#     {"Almoxarifado": "Almox Pintura - Embalagem", "Setor": "COMPONENTES", "Líder": "ERICA"},
#     {"Almoxarifado": "Almox Pintura - Embalagem", "Setor": "CONJ", "Líder": "ERICA"},
#     {"Almoxarifado": "Almox Pintura - Embalagem", "Setor": "PEÇA", "Líder": "ERICA"},
#     {"Almoxarifado": "Almox Pintura - Embalagem", "Setor": "PEÇAS", "Líder": "ERICA"},
#     {"Almoxarifado": "Almox Prod Especiais", "Setor": "MP", "Líder": "VICTOR"},
#     {"Almoxarifado": "Almox Prod Especiais", "Setor": "PEÇA", "Líder": "VICTOR"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - COR", "Líder": "ERIC"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - GAV", "Líder": "EVANDRO"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - SL1", "Líder": "ERIC"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - EST", "Líder": "EVANDRO"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - SL2", "Líder": "MAYLSON"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - AM", "Líder": "MAYLSON"},
#     {"Almoxarifado": "Central", "Setor": "AL07 - SALA", "Líder": "EVANDRO"},
#     {"Almoxarifado": "Central", "Setor": "AL03 - INFLAMÁVEIS", "Líder": "EVANDRO"},
#     {"Almoxarifado": "Central", "Setor": "AL02 - GALPÃO", "Líder": "MAYLSON"},
#     {"Almoxarifado": "Central", "Setor": "AL08 - PROJETOS", "Líder": "ERIC"},
#     {"Almoxarifado": "Central", "Setor": "AL06 - CARPINTARIA", "Líder": "MAYLSON"},
#     {"Almoxarifado": "Central", "Setor": "AL05 - BORRACHARIA", "Líder": "MAYLSON"},
#     {"Almoxarifado": "Central", "Setor": "AL10 - GASES", "Líder": "ERIC"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - EPI", "Líder": "SESMT"},
#     {"Almoxarifado": "Central", "Setor": "AL09 - SALA", "Líder": "MAYLSON"},
#     {"Almoxarifado": "Central", "Setor": "AL04 - CHA", "Líder": "PCP"},
#     {"Almoxarifado": "Central", "Setor": "AL04 - SER", "Líder": "PCP"},
#     {"Almoxarifado": "Central", "Setor": "NÃO EXISTE - NÃO EXISTE", "Líder": "EVANDRO"},
#     {"Almoxarifado": "Central", "Setor": "MANUTENÇÃO - MANUTENÇÃO", "Líder": "MANUTENÇÃO"},
#     {"Almoxarifado": "Central", "Setor": "AL01 - ACESS", "Líder": "MAYLSON"},
# ]

planilha_lideres_path = "app/planilha_para_lideres/2025.csv"

# Função para carregar os dados da planilha de líderes
def carregar_lideres(almoxarifado, setor):
    # Lê a planilha Excel para um DataFrame
    # df = pd.read_excel(planilha_lideres_path)
    df = pd.read_csv(planilha_lideres_path)

    df = df[df['ID LISTA'].notna()]  # Remove NaN
    df = df[df['ID LISTA'] != ""]  # Remove valores vazios
    df = df[['ID LISTA', 'Almox', 'LÍDER']]

    # Percorre as linhas da planilha
    for _, row in df.iterrows():
        # Compara almoxarifado e setor com as colunas correspondentes
        if row['Almox'] == almoxarifado and row['ID LISTA'] == setor:
            # Se encontrar, retorna o líder
            return row['LÍDER']
    
    # Se não encontrar nenhuma correspondência, retorna uma mensagem padrão
    return "Líder não definido"