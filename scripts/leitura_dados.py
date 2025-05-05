import pandas as pd

def carregar_dados():
    import gdown

    # Link do seu Google Drive com download direto
    url = "https://drive.google.com/uc?export=download&id=1nwiU-O9DNjWGJ2C5PMp65uG2YBVoZnxM"
    output = "dados.xlsx"
    gdown.download(url, output, quiet=False)

    df = pd.read_excel(output)

    df.columns = df.columns.str.strip()
    df['Abertura'] = pd.to_datetime(df['Abertura'], errors='coerce', dayfirst=True)
    df['Fechamento'] = pd.to_datetime(df['Fechamento'], errors='coerce', dayfirst=True)  # ✅ necessário

    df = df.dropna(subset=['Abertura'])
    return df



