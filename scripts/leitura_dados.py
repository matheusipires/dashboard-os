# scripts/leitura_dados.py

import pandas as pd

def carregar_dados():
    """
    Lê os dados de uma planilha pública do Google Sheets e trata a coluna de data de abertura.
    """
    url = "https://docs.google.com/spreadsheets/d/1Q2RfzoTasS-PDK6H1PC73p0uSalQQRlEyvV26rw2sKc/export?format=csv"
    
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()  # Remove espaços extras dos nomes das colunas

    if 'Abertura' in df.columns:
        df['Abertura'] = pd.to_datetime(df['Abertura'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['Abertura'])  # Remove linhas com data inválida
    
    return df
