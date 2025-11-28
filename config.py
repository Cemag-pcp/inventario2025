import os
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env (se existir)
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# Obter as variáveis de ambiente
DB_HOST = os.getenv('DB_HOST', 'database-1.cdcogkfzajf0.us-east-1.rds.amazonaws.com')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', '15512332')

class Config:
    # Configuração do banco de dados PostgreSQL
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_SCHEMA = 'inventario_2024'  # Definindo o schema do banco de dados
