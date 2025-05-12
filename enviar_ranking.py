import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pdfkit
import os
from datetime import datetime
import locale
import sys
import shutil

# Adiciona o diretório 'scripts' ao path do sistema para importar leitura_dados.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from leitura_dados import carregar_dados

# Definir localidade para português do Brasil
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '')


# Caminho do executável wkhtmltopdf

path_wkhtmltopdf = shutil.which("wkhtmltopdf")
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)


# 🔹 Leitura do banco de dados online
df = carregar_dados()

# 🔹 Filtros iniciais
df = df[df['CLIENTE'].notna() & (df['CLIENTE'].str.strip() != "-")]

# 🔹 Filtra por tipo desejado
tipos_validos = ['calibração', 'preventiva', 'tse', 'qualificação']
df = df[df['TIPO DE MANUTENÇÃO2'].str.lower().isin(tipos_validos)]

# 🔹 Criar colunas auxiliares para o mês de abertura e fechamento
df['Mes_Abertura'] = df['Abertura'].dt.to_period('M').astype(str)
df['Mes_Fechamento'] = df['Fechamento'].dt.to_period('M').astype(str)

# 🔹 Considerar somente OS válidas
df_validas = df[df['SITUAÇÃO OS'].isin(['Aberta', 'Pendente', 'Fechada'])].copy()

# 🔹 Filtrar apenas OS cujo mês de abertura é o mês atual
mes_atual = datetime.now().strftime('%Y-%m')
df_validas_mes_atual = df_validas[df_validas['Mes_Abertura'] == mes_atual]

# 🔹 Total e fechadas no mesmo mês (Ranking por Cliente)
total_os = df_validas_mes_atual.groupby('CLIENTE')['OS'].count().reset_index(name='Abertas')
fechadas_mesmo_mes = df_validas_mes_atual[
    (df_validas_mes_atual['SITUAÇÃO OS'] == 'Fechada') &
    (df_validas_mes_atual['Mes_Abertura'] == df_validas_mes_atual['Mes_Fechamento'])
]
fechadas = fechadas_mesmo_mes.groupby('CLIENTE')['OS'].count().reset_index(name='Fechadas')

ranking = pd.merge(total_os, fechadas, on='CLIENTE', how='left').fillna(0)
ranking['% Conclusão'] = (ranking['Fechadas'] / ranking['Abertas']) * 100
ranking = ranking.sort_values(by='% Conclusão', ascending=False).reset_index(drop=True)
ranking['Classificação'] = ranking.index + 1

# 🔹 Totais para os cards
total_abertas = len(df_validas_mes_atual)
total_fechadas_mesmo_mes = len(fechadas_mesmo_mes)
porcentagem_conclusao = (total_fechadas_mesmo_mes / total_abertas * 100) if total_abertas > 0 else 0

# 🔹 Gerar HTML dos cards e tabela
from datetime import datetime

meses_pt = {
    1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
    5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
    9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
}

agora = datetime.now()
data_ref = f"{meses_pt[agora.month].capitalize()} de {agora.year}"

html_cards = f"""
<div style="font-family:'Segoe UI', Tahoma, sans-serif; margin-bottom:30px;">
  <h2 style="color:#1B556B; font-size:22px;">Relatório Institucional - Desempenho Operacional ({data_ref})</h2>
  <p style="font-size:15px; color:#333; margin-bottom:20px;">
    Este relatório apresenta os indicadores de desempenho relacionados às <strong>ordens de serviço abertas e finalizadas no mês atual</strong>, abrangendo as categorias de manutenção <strong>Calibração</strong>, <strong>Preventiva</strong>, <strong>TSE</strong> e <strong>Qualificação</strong>.
  </p>
  <p style="font-size:14px; color:#555; font-style:italic;">Departamento de Operações · Orbis Engenharia Clínica</p>
  <div style="display:flex; gap:15px; flex-wrap:wrap;">
    <div style="flex:1; min-width:150px; background:#E8F0FE; padding:20px; border-radius:12px; border-left:5px solid #1B556B;">
      <p style="margin:0; font-size:13px;">Total de OS Abertas</p>
      <h3 style="margin:0; font-size:22px;">{total_abertas}</h3>
    </div>
    <div style="flex:1; min-width:150px; background:#D4EDDA; padding:20px; border-radius:12px; border-left:5px solid #28A745;">
      <p style="margin:0; font-size:13px;">Fechadas no mesmo mês</p>
      <h3 style="margin:0; font-size:22px;">{total_fechadas_mesmo_mes}</h3>
    </div>
    <div style="flex:1; min-width:150px; background:#FFF3CD; padding:20px; border-radius:12px; border-left:5px solid #FFC107;">
      <p style="margin:0; font-size:13px;">% Conclusão</p>
      <h3 style="margin:0; font-size:22px;">{porcentagem_conclusao:.1f}%</h3>
    </div>
  </div>
</div>
"""

html_tabela = """
<h3 style='color:#1B556B;'>🏅 Ranking de Conclusão por Cliente</h3>
<table style="width:100%; border-collapse: separate; border-spacing: 0; font-family: 'Segoe UI', Tahoma, sans-serif;">
    <thead style="background-color:#1B556B; color:white;">
        <tr>
            <th style="padding:12px; border:1px solid #ccc; border-top-left-radius: 10px;">Classificação</th>
            <th style="padding:12px; border:1px solid #ccc;">Cliente</th>
            <th style="padding:12px; border:1px solid #ccc;">Abertas</th>
            <th style="padding:12px; border:1px solid #ccc;">Fechadas</th>
            <th style="padding:12px; border:1px solid #ccc; border-top-right-radius: 10px;">% Conclusão</th>
        </tr>
    </thead>
    <tbody>
"""

for _, row in ranking.iterrows():
    texto = f"<span style='color:#155724;'>✅ {row['% Conclusão']:.1f}%</span>" if row['% Conclusão'] >= 90 else f"<span style='color:#721c24;'>❌ {row['% Conclusão']:.1f}%</span>"
    html_tabela += f"""
    <tr style="font-size:14px;">
        <td style="padding:10px; border:1px solid #ccc; text-align:center;">{int(row['Classificação'])}</td>
        <td style="padding:10px; border:1px solid #ccc;">{row['CLIENTE']}</td>
        <td style="padding:10px; border:1px solid #ccc; text-align:center;">{int(row['Abertas'])}</td>
        <td style="padding:10px; border:1px solid #ccc; text-align:center;">{int(row['Fechadas'])}</td>
        <td style="padding:10px; border:1px solid #ccc; text-align:center;">{texto}</td>
    </tr>
    """

html_tabela += "</tbody></table>"

html_completo = f"""
<html>
  <head><meta charset="utf-8"></head>
  <body style="font-family:'Segoe UI', Tahoma, sans-serif;">
    {html_cards}
    {html_tabela}
    <div style="text-align:center; margin:30px 0;">
  <a href="https://dashbordoperacional.streamlit.app/" target="_blank" style="background-color:#1B556B; color:white; padding:12px 24px; border-radius:8px; text-decoration:none; font-size:15px; font-weight:bold; font-family:'Segoe UI', sans-serif;">
    📊 Acessar Dashboard
  </a>
</div>

<div style="margin-top:40px; font-size:12px; color:#999; text-align:center;">
  Desenvolvido por Matheus Pires · Mensagem automática do sistema
</div>
  </body>
</html>
"""

# 🔹 Gerar PDF
pdf_path = r"C:\Users\matheus.pires\Desktop\ranking_OS.pdf"
pdfkit.from_string(html_completo, pdf_path, configuration=config)

# 🔹 Enviar E-mail
from email.utils import COMMASPACE

destinatarios = [
    "supervisores.clinica@orbisengenharia.com.br",
    "coordenadores.engenharia@orbisengenharia.com.br",
    "ricardo.maranhao@orbisengenharia.com.br",
    "qualidade@orbisengenharia.com.br",
    "guilherme.braz@orbisengenharia.com.br",
    "manutencao@orbisengenharia.com.br",
    "metrologia@orbisengenharia.com.br"
]

email = MIMEMultipart()
email['From'] = "matheus.pires@orbisengenharia.com.br"
email['To'] = COMMASPACE.join(destinatarios)
email['Subject'] = f"📊 Departamento de Operações - Relatório de Conclusão de OS ({data_ref})"

email.attach(MIMEText(html_completo, 'html'))

# Anexo
with open(pdf_path, "rb") as f:
    anexo = MIMEBase('application', 'pdf')
    anexo.set_payload(f.read())
    encoders.encode_base64(anexo)
    anexo.add_header('Content-Disposition', 'attachment', filename='Ranking_OS_Departamento_Operacoes.pdf')
    email.attach(anexo)

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    senha = os.environ.get("EMAIL_SENHA")
    server.login("matheus.pires@orbisengenharia.com.br", senha)
    server.send_message(email, to_addrs=destinatarios)

print("✅ E-mail enviado com sucesso.")

