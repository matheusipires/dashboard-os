import pandas as pd
import gdown

def carregar_dados():
    """Baixa o arquivo do Google Drive com gdown e carrega o Excel."""
    url = "https://drive.google.com/uc?export=download&id=1nwiU-O9DNjWGJ2C5PMp65uG2YBVoZnxM"
    output = "/tmp/dados.xlsx"
    gdown.download(url, output, quiet=False)
    df = pd.read_excel(output)
    df.columns = df.columns.str.strip()
    df['Abertura'] = pd.to_datetime(df['Abertura'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Abertura'])
    return df


