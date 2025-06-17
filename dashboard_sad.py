import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

# --- 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
# Constrói o caminho absoluto para o arquivo de dados
# Isso garante que o servidor sempre encontre o arquivo, não importa de onde o script é executado.
caminho_script = os.path.dirname(os.path.abspath(__file__))
caminho_csv = os.path.join(caminho_script, 'dados_mercado_imobiliario_consolidados.csv')

try:
    df = pd.read_csv(caminho_csv)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df['Periodo'] = df['DATE'].dt.to_period('Q').astype(str)
except FileNotFoundError:
    # Esta mensagem agora aparecerá no seu log de erros se algo der errado
    print(f"ERRO: O arquivo CSV não foi encontrado no caminho: {caminho_csv}")
    # Não use exit() em um app web, apenas deixe o erro acontecer para podermos vê-lo.

# --- 2. INICIALIZAÇÃO E LAYOUT DO DASHBOARD ---
app = dash.Dash(__name__)
server = app.server

# Listas para os filtros
metricas_disponiveis = df.columns.drop(['DATE', 'Periodo']).tolist()
periodos_disponiveis = sorted(df['Periodo'].unique())

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#f4f4f4'}, children=[
    html.H1("Dashboard de Análise do Mercado Imobiliário", style={'textAlign': 'center', 'color': '#333'}),

    dcc.Tabs(id="tabs-gerais", value='tab-interativa', children=[
        # Aba 1: Análise Interativa
        dcc.Tab(label='Análise Interativa', value='tab-interativa', children=[
            html.Div(style={'padding': '20px'}, children=[
                html.P("Use os filtros abaixo para explorar a relação entre diferentes métricas ao longo do tempo.", style={'textAlign': 'center', 'color': '#666', 'marginTop': '10px'}),
                html.Hr(),
                html.Div(children=[
                    html.Div(children=[
                        html.Label("Selecione uma Métrica:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(id='metric-dropdown', options=[{'label': m, 'value': m} for m in metricas_disponiveis], value=metricas_disponiveis[0], clearable=False, style={'marginTop': '5px'})
                    ], style={'width': '100%', 'marginBottom': '15px'}),
                    html.Div(children=[
                        html.Div(children=[
                            html.Label("Período Inicial:", style={'fontWeight': 'bold'}),
                            dcc.Dropdown(id='start-period-dropdown', options=[{'label': p, 'value': p} for p in periodos_disponiveis], value=periodos_disponiveis[0], clearable=False, style={'marginTop': '5px'})
                        ], style={'width': '48%', 'display': 'inline-block'}),
                        html.Div(children=[
                            html.Label("Período Final:", style={'fontWeight': 'bold'}),
                            dcc.Dropdown(id='end-period-dropdown', options=[{'label': p, 'value': p} for p in periodos_disponiveis], value=periodos_disponiveis[-1], clearable=False, style={'marginTop': '5px'})
                        ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
                    ])
                ], style={'marginBottom': '20px'}),
                dcc.Graph(id='interactive-graph')
            ])
        ]),

        # Aba 2: Indicadores de Alerta
        dcc.Tab(label='Indicadores de Alerta (Crise 2008)', value='tab-indicadores', children=[
            html.Div(id='conteudo-tab-indicadores', style={'padding': '20px'}) # Conteúdo será gerado por callback
        ]),
    ])
])

# --- 3. CALLBACKS ---

# Callback para a aba de Análise Interativa
@app.callback(
    Output('interactive-graph', 'figure'),
    [Input('metric-dropdown', 'value'),
     Input('start-period-dropdown', 'value'),
     Input('end-period-dropdown', 'value')]
)
def update_interactive_graph(selected_metric, start_period, end_period):
    if start_period > end_period:
        start_period = end_period
    
    dff = df[(df['Periodo'] >= start_period) & (df['Periodo'] <= end_period)]
    fig = px.line(dff, x='DATE', y=selected_metric, title=f'{selected_metric} ao Longo do Tempo', template='plotly_white', markers=True)
    fig.update_layout(xaxis_title='Data', yaxis_title=selected_metric, title_x=0.5)
    fig.update_traces(hovertemplate='Data: %{x|%d/%m/%Y}<br>Valor: %{y}')
    return fig

# NOVO Callback para a aba de Indicadores de Alerta
@app.callback(
    Output('conteudo-tab-indicadores', 'children'),
    [Input('tabs-gerais', 'value')]
)
def render_indicadores_tab(tab_selecionada):
    # Esta função só executa quando a aba 'Indicadores de Alerta' é selecionada
    if tab_selecionada == 'tab-indicadores':
        # Filtro corrigido, aplicado no momento em que a aba é renderizada
        df_filtrado = df[df['DATE'] <= '2010-01-01'].copy()

        # Criação da Figura 1
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Scatter(x=df_filtrado['DATE'], y=df_filtrado['Taxa de Juros Hipotecas 30a (%)'], name='Taxa de Juros Hipotecas 30a (%)'), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_filtrado['DATE'], y=df_filtrado['Inadimplência de Hipotecas (%)'], name='Inadimplência de Hipotecas (%)'), secondary_y=True)
        fig1.update_layout(title_text="Indicador 1: Stress no Crédito Imobiliário", template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig1.update_xaxes(title_text="Ano")
        fig1.update_yaxes(title_text="Taxa de Juros (%)", secondary_y=False)
        fig1.update_yaxes(title_text="Taxa de Inadimplência (%)", secondary_y=True)

        # Criação da Figura 2
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_filtrado['DATE'], y=df_filtrado['Índice de Preços de Imóveis (USD)'], name='Índice de Preços de Imóveis (USD)'), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_filtrado['DATE'], y=df_filtrado['Estoque de Imóveis (Meses)'], name='Estoque de Imóveis (Meses)'), secondary_y=True)
        fig2.update_layout(title_text="Indicador 2: Saturação e Desaceleração Imobiliária", template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig2.update_xaxes(title_text="Ano")
        fig2.update_yaxes(title_text="Índice de Preços (USD)", secondary_y=False)
        fig2.update_yaxes(title_text="Estoque (Meses)", secondary_y=True)

        # Retorna o layout completo da aba
        return html.Div([
            html.H3("Indicadores Preditivos da Crise", style={'textAlign': 'center', 'margin-top': '20px'}),
            dcc.Graph(figure=fig1),
            html.P("Análise: Observe como a subida das taxas de juros é seguida por um forte aumento na inadimplência, sinalizando pressão financeira sobre os mutuários.", style={'margin-top': '10px', 'font-style': 'italic', 'textAlign': 'center'}),
            html.Hr(style={'margin-top': '30px', 'margin-bottom': '30px'}),
            dcc.Graph(figure=fig2),
            html.P("Análise: Note que o pico nos preços dos imóveis ocorre quando o estoque de casas à venda já estava crescendo. Isso indica uma saturação do mercado, um sinal clássico de que a bolha estava prestes a estourar.", style={'margin-top': '10px', 'font-style': 'italic', 'textAlign': 'center'})
        ])
    # Se outra aba estiver selecionada, não retorna nada
    return []

# --- 4. EXECUÇÃO DO APLICATIVO ---
if __name__ == '__main__':
    app.run(debug=True)