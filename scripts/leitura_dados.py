import pandas as pd

def carregar_dados():
    """Lê os dados a partir do Google Drive e trata a coluna de data de abertura."""
    url = "https://drive.google.com/uc?export=download&id=1nwiU-O9DNjWGJ2C5PMp65uG2YBVoZnxM"
    df = pd.read_excel(url)
    df.columns = df.columns.str.strip()  # Remove espaços dos nomes das colunas
    df['Abertura'] = pd.to_datetime(df['Abertura'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Abertura'])  # Remove linhas com data inválida
    return df


