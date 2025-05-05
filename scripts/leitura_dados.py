# scripts/leitura_dados.py

import pandas as pd
from config.paths import EXCEL_PATH, SHEET_NAME

def carregar_dados():
    """Lê o arquivo Excel e trata a coluna de data de abertura."""
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    df.columns = df.columns.str.strip()  # Remove espaços extras dos nomes das colunas
    df['Abertura'] = pd.to_datetime(df['Abertura'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Abertura'])  # Remove linhas com data inválida
    return df
