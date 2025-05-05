import pandas as pd

def carregar_dados():
    """
    Lê os dados da planilha pública do Google Sheets (.xlsx) e trata a coluna de data de abertura.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSjEallKbR3wVYefBHDbboAmYCktNQ2x9AfI-6tEISq99I1QrZZVmBUYzBIhbmdTATnUkUyqOXR0ZcR/pub?output=xlsx"

    df = pd.read_excel(url)
    df.columns = df.columns.str.strip()  # Remove espaços dos nomes de colunas

    if 'Abertura' in df.columns:
        df['Abertura'] = pd.to_datetime(df['Abertura'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['Abertura'])  # Remove linhas com datas inválidas

    return df

