COMO USAR:

1. Dentro da pasta excel_dados_inventario jogue os arquivos em csv que serão usados para base de contagem
1.1. Deverá obrigatoriamente conter as colunas (SETOR,LOCALIZACAO,CÓDIGO,QTD,ALMOXARIFADO)

2. Rodar no console: python
2.1. Depois: 
from app import create_app
from app.management.planilha_dados_inventario import carregar_dados_csv

app = create_app()
caminho = r"excel_dados_inventario\MAPEAMENTO_MONT_CARRETAS2.csv"

with app.app_context():
    carregar_dados_csv(caminho)

2.2. Caso queira subir todas as listas de uma so vez, deverá ser preenchido a lista: caminhos_csv dentro de planilha_dados_inventario
2.3. Depois deverá chamar a função: carregar_varios_csv dentro de planilha_dados_inventario.# inventario2025
# inventario2025
