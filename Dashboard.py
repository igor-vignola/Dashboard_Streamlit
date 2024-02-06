import plotly.express as px
import streamlit as st
import pandas as pd
import requests 

st.set_page_config(layout='wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f"{prefixo} {valor:.2f} {unidade}"
        valor /= 1000
    return f"{prefixo} {valor:.2f} milhões"


st.title("DASHBOARD DE VENDAS :shopping_trolley:")

url = 'https://labdados.com/produtos'

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}
response = requests.get(url, params= query_string)

dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] =  pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas 
### Tabela de Receitas
receita_estados = dados.groupby(by = 'Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending = False)
receita_categoria = dados.groupby(by = 'Categoria do Produto')[['Preço']].sum().sort_values(by = 'Preço', ascending=False)


receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))[['Preço']].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

### Tabela de Quantidade de Vendas
quantidade_estados = dados['Local da compra'].value_counts()
quantidade_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(quantidade_estados, left_on='Local da compra', right_index=True).reset_index(drop=True)

quantidade_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))[['Preço']].count().reset_index()
quantidade_mensal['Ano'] = quantidade_mensal['Data da Compra'].dt.year
quantidade_mensal['Mes'] = quantidade_mensal['Data da Compra'].dt.month_name()

quantidade_estados_vendas = quantidade_estados.sort_values('count', ascending = False).head(5)

qtde_venda_categoria = dados['Categoria do Produto'].value_counts()

### Tabela de Vendedores
vendedores = pd.DataFrame(dados.groupby(by = 'Vendedor')['Preço'].agg(['sum','count']))

## Gráficos
mapa_receita = px.scatter_geo(receita_estados, 
                              lat = 'lat', 
                              lon = 'lon', 
                              size='Preço', 
                              scope = 'south america', 
                              template = 'seaborn', 
                              hover_name = 'Local da compra', 
                              hover_data = {'lat': False, 'lon': False}, 
                              title = 'Receita por estado')

grafico_receita_mensal = px.line(data_frame = receita_mensal, 
                                 x = 'Mes', 
                                 y = 'Preço',
                                 markers = True,
                                 range_y = (0, receita_mensal.max()),
                                 color = 'Ano',
                                 line_dash = 'Ano',
                                 title = 'Receita Mensal')
grafico_receita_mensal.update_layout(yaxis_title = "Receita")

grafico_barra_estado = px.bar(data_frame=receita_estados.head(), x = 'Local da compra', y = 'Preço', text_auto=True, title='Top estados (receita)')
grafico_barra_estado.update_layout(yaxis_title = "Receita")

grafico_barra_categoria = px.bar(data_frame = receita_categoria, text_auto=True, title = 'Receita por Categoria')
grafico_barra_categoria.update_layout(yaxis_title = "Receita")

linha_quantidade_mensal = px.line(data_frame=quantidade_mensal,
                                   x = 'Mes',
                                   y = 'Preço',
                                   markers = True,                
                                   color = 'Ano',
                                   line_dash='Ano',
                                   title = 'Quantidade de Vendas por Mês')
linha_quantidade_mensal.update_layout(yaxis_title = "Quantidade de Vendas")

mapa_vendas_estado = px.scatter_geo(quantidade_estados,
                                    lat = 'lat',
                                    lon = 'lon',
                                    size = 'count',
                                    scope = 'south america',
                                    template='seaborn',
                                    hover_name='Local da compra',
                                    hover_data={'lat':False, 'lon':False},
                                    title = 'Quantidade de Vendas por Estado', 
                                    size_max=20)

top_estados_quantidade_venda = px.bar(data_frame=quantidade_estados_vendas,
                                      x = 'Local da compra',
                                      y = 'count',
                                      text_auto=True,
                                      title = 'Estados com maior Qtde. de Vendas')
grafico_barra_categoria.update_layout(yaxis_title = "Qtde. de Vendas")
grafico_barra_categoria.update_layout(yaxis_title = "Estado")

grafico_qtde_vendas_categoria = px.bar(data_frame=qtde_venda_categoria,
                                       x = 'count',
                                       y = qtde_venda_categoria.index,
                                       text_auto=True,
                                       title = 'Qtde de Vendas por Categoria')

## Visualização no Streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita Total", formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(mapa_receita, use_container_width=True)
        st.plotly_chart(grafico_barra_estado, use_container_width=True)
        
    with coluna2:
        st.metric("Quantidade Vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(grafico_receita_mensal, use_container_width=True)
        st.plotly_chart(grafico_barra_categoria, use_container_width=True)
    st.dataframe(dados)


with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita Total", formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(mapa_vendas_estado, use_container_width=True)
        st.plotly_chart(top_estados_quantidade_venda)

    with coluna2:
        st.metric("Quantidade Vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(linha_quantidade_mensal)
        st.plotly_chart(grafico_qtde_vendas_categoria)
        

with aba3:
    qtd_vendedores = st.number_input('Quantidade de Vendedores', min_value=2, max_value=10, value=5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita Total", formata_numero(dados['Preço'].sum(), 'R$'))
        receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                    x = 'sum',
                                    y = vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                    text_auto=True,
                                    title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(receita_vendedores)
    with coluna2:
        st.metric("Quantidade Vendas", formata_numero(dados.shape[0]))
        vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                    x = 'count',
                                    y = vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                    text_auto=True,
                                    title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(vendas_vendedores) 