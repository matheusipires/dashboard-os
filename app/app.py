import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scripts.leitura_dados import carregar_dados
import base64

# ✅ Precisa ser o primeiro comando do Streamlit
st.set_page_config(page_title="Dashboard OS", layout="wide")

# ✅ Gera logo em base64
def get_logo_base64():
    with open("app/assets/logo.png", "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"

logo_base64 = get_logo_base64()

# ✅ Carrega e injeta HTML do cabeçalho com logo embutido
with open("app/styles/components.html", encoding="utf-8") as f:
    html = f.read().format(logo_base64=logo_base64)
    st.markdown(html, unsafe_allow_html=True)

# ✅ Carrega o CSS externo
with open("app/styles/layout.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# (continue com o restante do seu código aqui...)

COR_AZUL = '#1B556B'
COR_LARANJA = '#E98C5F'
COR_VERDE = '#32AF9D'

with st.spinner("Carregando dados..."):
    df = carregar_dados()

df = df[df['CLIENTE'].notna() & (df['CLIENTE'].str.strip() != "-")]

# Criando colunas auxiliares
df['Mês_Abertura'] = df['Abertura'].dt.to_period('M').astype(str)
df['Mês_Fechamento'] = df['Fechamento'].dt.to_period('M').astype(str)

with st.sidebar:
    st.header("🔎 Filtros")
    with st.expander("🎯 Selecione os filtros"):
        clientes = sorted(df['CLIENTE'].unique())
        todos_clientes = st.checkbox("Selecionar todos os clientes", value=True)
        clientes_selecionados = clientes if todos_clientes else st.multiselect("Unidade", clientes)

        tipos = sorted(df['TIPO DE MANUTENÇÃO2'].dropna().unique())
        todos_tipos = st.checkbox("Selecionar todos os tipos de manutenção", value=True)
        tipos_selecionados = tipos if todos_tipos else st.multiselect("Tipo de manutenção", tipos)

    data_min = df['Abertura'].min().date()
    data_max = df['Abertura'].max().date()
    data_inicio, data_fim = st.date_input("Período de abertura:", [data_min, data_max], min_value=data_min, max_value=data_max)

df_filtrado = df[
    (df['CLIENTE'].isin(clientes_selecionados)) &
    (df['TIPO DE MANUTENÇÃO2'].isin(tipos_selecionados)) &
    (df['Abertura'].dt.date >= data_inicio) &
    (df['Abertura'].dt.date <= data_fim)
].copy()

situacoes = df_filtrado['SITUAÇÃO OS'].str.lower().str.strip()


    # Cards
total_os = len(df_filtrado)
abertas = (situacoes == 'aberta').sum()
pendentes = (situacoes == 'pendente').sum()
fechadas = (situacoes == 'fechada').sum()
taxa = f"{(fechadas / total_os * 100) if total_os > 0 else 0:,.1f}%".replace('.', ',')

st.markdown("---")
# Atualiza valores combinados
pendentes_total = abertas + pendentes

# Cria os cards com botão para painel futuro
st.markdown(f"""
<div style="display:flex; flex-wrap:wrap; gap:1rem;">
    <div style="flex:1; min-width:180px; background-color:#f0f2f6; padding:1rem; border-radius:8px;">
        <h4>🔧 Total de OS</h4>
        <h2>{total_os}</h2>
    </div>
    <div style="flex:1; min-width:180px; background-color:#fff3cd; padding:1rem; border-radius:8px;">
        <h4>⚠️ Pendentes</h4>
        <h2>{pendentes_total}</h2>
        <a href='?aba=pendentes'>
            <button style="margin-top:0.5rem; padding:0.5rem 1rem; border:none; background-color:#1B556B; color:white; border-radius:5px;">Ver detalhes</button>
        </a>
    </div>
    <div style="flex:1; min-width:180px; background-color:#d4edda; padding:1rem; border-radius:8px;">
        <h4>✅ Concluídas</h4>
        <h2>{fechadas}</h2>
    </div>
    <div style="flex:1; min-width:180px; background-color:#e2e3e5; padding:1rem; border-radius:8px;">
        <h4>📈 % Conclusão</h4>
        <h2>{taxa}</h2>
    </div>
    <div style="flex:1; min-width:220px; background-color:#d1ecf1; padding:1rem; border-radius:8px;">
        <h4>📊 Período</h4>
        <h2>{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}</h2>
    </div>
</div>
""", unsafe_allow_html=True)


    # Dados para gráfico KPI
df_total = df_filtrado[df_filtrado['SITUAÇÃO OS'].isin(['Aberta', 'Pendente', 'Fechada'])].copy()
df_total['Mes_Ano'] = df_total['Abertura'].dt.to_period('M').astype(str)

df_fechadas_mesmo_mes = df_filtrado[
        (df_filtrado['SITUAÇÃO OS'] == 'Fechada') &
        (df_filtrado['Fechamento'].notna()) &
        (df_filtrado['Abertura'].dt.to_period('M') == df_filtrado['Fechamento'].dt.to_period('M'))
    ].copy()
df_fechadas_mesmo_mes['Mes_Ano'] = df_fechadas_mesmo_mes['Abertura'].dt.to_period('M').astype(str)

grupo_total = df_total.groupby('Mes_Ano')['OS'].count().reset_index(name='Total')
grupo_fechadas = df_fechadas_mesmo_mes.groupby('Mes_Ano')['OS'].count().reset_index(name='Fechadas')

grupo_mes = grupo_total.merge(grupo_fechadas, on='Mes_Ano', how='left').fillna(0)
grupo_mes['% Conclusão'] = (grupo_mes['Fechadas'] / grupo_mes['Total']) * 100
grupo_final = grupo_mes.copy()
grupo_final['% Conclusão'] = grupo_final['% Conclusão'].round(1)
grupo_final_sorted = grupo_final.sort_values('Mes_Ano').reset_index(drop=True)

    # Gráfico
    # Gráfico KPI Abertas x Fechadas com rótulos e cabeçalho melhorado
fig = go.Figure()
fig.add_trace(go.Bar(
    x=grupo_mes['Mes_Ano'],
    y=grupo_mes['Total'],
    name='Total de OS Abertas',
    marker_color=COR_AZUL,
    text=grupo_mes['Total'],
    textposition='auto'
))
fig.add_trace(go.Bar(
    x=grupo_mes['Mes_Ano'],
    y=grupo_mes['Fechadas'],
    name='Fechadas no mesmo mês',
    marker_color=COR_VERDE,
    text=grupo_mes['Fechadas'],
    textposition='auto'
))
fig.add_trace(go.Scatter(
    x=grupo_mes['Mes_Ano'],
    y=grupo_mes['% Conclusão'],
    name='% Conclusão',
    mode='lines+markers+text',
    line=dict(color=COR_LARANJA, dash='dash'),
    text=[f"{x:.1f}%" for x in grupo_mes['% Conclusão']],
    textposition="top center",
    yaxis='y2'
))

# Cabeçalho padronizado
st.markdown("### 📊 KPI - Acompanhamento de Abertura e Fechamento de OS por Mês")

fig.update_layout(
    xaxis_title='Mês',
    yaxis=dict(title='Quantidade de OS'),
    yaxis2=dict(title='% Conclusão', overlaying='y', side='right', range=[0, 100]),
    barmode='group',
    legend=dict(orientation='h', y=-0.25),
    height=480
)

st.plotly_chart(fig, use_container_width=True)

# 📈 Criando o gráfico de linha com rótulos de dados
fig_evolucao = go.Figure()

# Linha de % Conclusão
fig_evolucao.add_trace(go.Scatter(
    x=grupo_final_sorted['Mes_Ano'],
    y=grupo_final_sorted['% Conclusão'],
    mode='lines+markers+text',
    name='% Conclusão',
    text=[f'{v:.1f}%' for v in grupo_final_sorted['% Conclusão']],
    textposition='top center',
    line=dict(color='#1B556B')
))

# Linha de Meta (90%)
fig_evolucao.add_trace(go.Scatter(
    x=grupo_final_sorted['Mes_Ano'],
    y=[90] * len(grupo_final_sorted),
    mode='lines',
    name='Meta (90%)',
    line=dict(color='#E98C5F', dash='dash')
))

# Layout do gráfico
fig_evolucao.update_layout(
    title='📈 Evolução Mensal da % Conclusão',
    xaxis_title='Mês',
    yaxis_title='% Conclusão',
    yaxis=dict(range=[0, 100]),
    height=400,
    legend=dict(orientation='h', y=-0.2),
    margin=dict(l=40, r=40, t=80, b=40)
    
)
st.plotly_chart(fig_evolucao, use_container_width=True)

st.markdown("### 🛠️ Ranking de % Conclusão por Tipo de Manutenção")

# Garantir colunas auxiliares
df_filtrado['Mes_Abertura'] = df_filtrado['Abertura'].dt.to_period('M').astype(str)
df_filtrado['Mes_Fechamento'] = df_filtrado['Fechamento'].dt.to_period('M').astype(str)

# Filtrar OS válidas
df_validas_tipo = df_filtrado[df_filtrado['SITUAÇÃO OS'].isin(['Aberta', 'Pendente', 'Fechada'])].copy()

# Total por tipo de manutenção
total_tipo = df_validas_tipo.groupby('TIPO DE MANUTENÇÃO2')['OS'].count().reset_index(name='Total_OS')

# Fechadas dentro do mesmo mês de abertura
df_fechadas_mesmo_mes_tipo = df_validas_tipo[
    (df_validas_tipo['SITUAÇÃO OS'] == 'Fechada') &
    (df_validas_tipo['Mes_Abertura'] == df_validas_tipo['Mes_Fechamento'])
]
fechadas_tipo = df_fechadas_mesmo_mes_tipo.groupby('TIPO DE MANUTENÇÃO2')['OS'].count().reset_index(name='Fechadas_no_Mes')

# Juntar e calcular
ranking_tipo = pd.merge(total_tipo, fechadas_tipo, on='TIPO DE MANUTENÇÃO2', how='left').fillna(0)
ranking_tipo['% Conclusão'] = (ranking_tipo['Fechadas_no_Mes'] / ranking_tipo['Total_OS']) * 100

ranking_tipo = ranking_tipo.sort_values(by='% Conclusão', ascending=False).reset_index(drop=True)
ranking_tipo['Classificação'] = ranking_tipo.index + 1
ranking_tipo['% Conclusão'] = ranking_tipo['% Conclusão'].map("{:.1f}%".format)

# Mostrar tabela
st.dataframe(
    ranking_tipo[['Classificação', 'TIPO DE MANUTENÇÃO2', '% Conclusão']],
    use_container_width=True
)
    
# Criação das colunas auxiliares no DataFrame filtrado
df_filtrado['Mês_Abertura'] = df_filtrado['Abertura'].dt.to_period('M').astype(str)
df_filtrado['Mês_Fechamento'] = df_filtrado['Fechamento'].dt.to_period('M').astype(str)

# RANKING % CONCLUSÃO POR CLIENTE (baseado em fechamento no mesmo mês da abertura)
st.markdown("### 🏆 Ranking de % Conclusão por CLIENTE")

df_filtrado['Mes_Abertura'] = df_filtrado['Abertura'].dt.to_period('M').astype(str)
df_filtrado['Mes_Fechamento'] = df_filtrado['Fechamento'].dt.to_period('M').astype(str)

# Filtra OS válidas
df_validas = df_filtrado[df_filtrado['SITUAÇÃO OS'].isin(['Aberta', 'Pendente', 'Fechada'])].copy()

# Total de OS por CLIENTE
total_os = df_validas.groupby('CLIENTE')['OS'].count().reset_index(name='Total_OS')

# Fechadas no mesmo mês da abertura
df_fechadas_mesmo_mes = df_validas[
    (df_validas['SITUAÇÃO OS'] == 'Fechada') &
    (df_validas['Mes_Abertura'] == df_validas['Mes_Fechamento'])
]
fechadas_mesmo_mes = df_fechadas_mesmo_mes.groupby('CLIENTE')['OS'].count().reset_index(name='Fechadas_no_Mes')

# Merge e cálculo da % conclusão
ranking = pd.merge(total_os, fechadas_mesmo_mes, on='CLIENTE', how='left').fillna(0)
ranking['% Conclusão'] = (ranking['Fechadas_no_Mes'] / ranking['Total_OS']) * 100

ranking = ranking.sort_values(by='% Conclusão', ascending=False).reset_index(drop=True)
ranking['Classificação'] = ranking.index + 1
ranking['% Conclusão'] = ranking['% Conclusão'].map("{:.1f}%".format)

# Exibe a tabela
st.dataframe(
    ranking[['Classificação', 'CLIENTE', '% Conclusão']],
    use_container_width=True
)
