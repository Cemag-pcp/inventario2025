from app import db
import os
import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv('.env')

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

def carregar_dados_csv(caminho_csv):
    # Ler o arquivo CSV ignorando colunas indesejadas
    df = pd.read_csv(caminho_csv, dtype={'CÓDIGO': str})

    # Remover registros com campos obrigatórios nulos
    df = df.dropna(subset=['CÓDIGO', 'SETOR'])

    connection = db.engine.connect()  # Obter conexão direta com o banco
    trans = connection.begin()  # Iniciar transação

    try:
        # Iterar sobre as linhas do DataFrame
        for _, row in df.iterrows():
            try:
                # Extrair valores das colunas
                local_nome = row['SETOR'].replace('/', '-')
                estante = row['LOCALIZAÇÃO'] if pd.notna(row['LOCALIZAÇÃO']) else ''
                almoxarifado = row['ALMOXARIFADO']
                
                # Verificar se o Local já existe
                local_query = text("""
                    SELECT id FROM inventario_2025.locais WHERE nome = :nome AND estante = :estante AND almoxarifado = :almoxarifado
                """)
                local_result = connection.execute(local_query, {
                    'nome': local_nome,
                    'estante': estante,
                    'almoxarifado': almoxarifado
                }).fetchone()

                if local_result is None:
                    local_insert = text("""
                        INSERT INTO inventario_2025.locais (nome, estante, almoxarifado) 
                        VALUES (:nome, :estante, :almoxarifado)
                        RETURNING id
                    """)
                    local_id = connection.execute(local_insert, {
                        'nome': local_nome,
                        'estante': estante,
                        'almoxarifado': almoxarifado
                    }).scalar()
                    print(f"Local criado: {local_nome}")
                else:
                    local_id = local_result[0]

                # Criar a peça
                codigo = str(row['CÓDIGO']).strip()
                descricao = row['DESCRIÇÃO'] if pd.notna(row['DESCRIÇÃO']) else ''
                quantidade_sistema = (
                    float(row['QTD'].replace('.', '').replace(',', '.')) 
                    if pd.notna(row['QTD']) and isinstance(row['QTD'], str) 
                    else float(row['QTD']) 
                    if pd.notna(row['QTD']) 
                    else 0.0
                )
                peca_fora_lista = False

                # Verificar se a peça já existe
                peca_query = text("""
                    SELECT id FROM inventario_2025.pecas WHERE codigo = :codigo AND local_id = :local_id
                """)
                peca_result = connection.execute(peca_query, {
                    'codigo': codigo,
                    'local_id': local_id
                }).fetchone()

                if peca_result is not None:
                    print(f"Peça já existe: {codigo}")
                    continue  # Ignorar e passar para a próxima linha

                peca_insert = text("""
                    INSERT INTO inventario_2025.pecas (codigo, descricao, local_id, quantidade_sistema, peca_fora_lista)
                    VALUES (:codigo, :descricao, :local_id, :quantidade_sistema, :peca_fora_lista)
                """)
                connection.execute(peca_insert, {
                    'codigo': codigo,
                    'descricao': descricao,
                    'local_id': local_id,
                    'quantidade_sistema': quantidade_sistema,
                    'peca_fora_lista': peca_fora_lista
                })
                print(f"Peça criada: {codigo}")

            except Exception as e:
                print(f"Erro ao processar a linha: {row.to_dict()} - Erro: {e}")

        # Commit final para salvar as transações no banco
        trans.commit()

    except Exception as e:
        trans.rollback()  # Reverter transações em caso de erro
        print(f"Erro ao processar o arquivo: {caminho_csv} - Erro: {e}")

    finally:
        connection.close()  # Garantir que a conexão seja fechada
        print("Conexão encerrada.")

    print("Dados carregados com sucesso!")

def carregar_varios_csv(lista_caminhos_csv):
    for caminho_csv in lista_caminhos_csv:
        print(f"Iniciando processamento do arquivo: {caminho_csv}")
        carregar_dados_csv(caminho_csv)
        print(f"Finalizado processamento do arquivo: {caminho_csv}")

caminhos_csv = [
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Corte e Estamparia.csv',
    'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Mont Carretas.csv',
    # 'excel_dados_inventario\MODELO BASE INVENTÁRIO 2024 - Almox Carpintaria.csv',
    # 'excel_dados_inventario\MODELO BASE INVENTÁRIO 2024 - Almox Expedição.csv',
    # 'excel_dados_inventario\MODELO BASE INVENTÁRIO 2024 - Almox Cx Acessórios.csv',
    # 'excel_dados_inventario\MODELO BASE INVENTÁRIO 2024 - Almox Devol Vendas.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Forjaria.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Marketing.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Peças Reposição.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Pintura - Embalagem.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Central.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Prod Especiais.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Almox Qualidade.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Serra.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Usinagem.csv',
    # 'excel_dados_inventario/MODELO BASE INVENTÁRIO 2024 - Almox Manutenção.csv',
]
