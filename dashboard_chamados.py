import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit_plotly_events import plotly_events
from datetime import datetime, date, timedelta
import os
import numpy as np

# Configuração do dashboard
st.set_page_config(page_title="Dashboard de Chamados Técnicos - HMSI", layout="wide")

# Sistema de Login
def check_login():
    # Verificar se já está logado
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h1>🔐 Dashboard HMSI - Login</h1>
            <p style="font-size: 18px; color: #666;">Acesso restrito a usuários autorizados</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Container centralizado para o login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.subheader("🔑 Autenticação")
                username = st.text_input("👤 Usuário")
                password = st.text_input("🔒 Senha", type="password")
                submit_button = st.form_submit_button("🚀 Entrar")
                
                if submit_button:
                    if username == "pedrohenrique" and password == "pedro751248693":
                        st.session_state.logged_in = True
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
                        return False
        
        # Botão para sair (só aparece se estiver logado)
        if st.session_state.logged_in:
            if st.button("🚪 Sair"):
                st.session_state.logged_in = False
                st.rerun()
        
        return False
    
    return True

# Verificar login antes de continuar
if not check_login():
    st.stop()

# Mostrar botão de logout na sidebar
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Carregar dados
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
            return pd.DataFrame()
    else:
        # Tentar carregar arquivo local (para desenvolvimento)
        file_path = "s.xlsx"
        try:
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
            else:
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return pd.DataFrame()
    
    # Converter colunas de data
    date_cols = ['Data de abertura', 'Última atualização', 'Tempo para solução + Progresso']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calcular tempo de resolução em horas
    if 'Data de abertura' in df.columns and 'Última atualização' in df.columns:
        df['Tempo Resolução (h)'] = (df['Última atualização'] - df['Data de abertura']).dt.total_seconds() / 3600
    
    # Limpar e padronizar categorias
    if 'Categoria' in df.columns:
        df['Categoria Limpa'] = df['Categoria'].str.replace('SETOR DE INFORMATICA > ', '').str.replace('SETOR DE INFORMATICA', 'OUTROS')
    
    return df

# Interface de upload
st.sidebar.header("📁 Upload de Dados")
uploaded_file = st.sidebar.file_uploader(
    "Carregar planilha Excel", 
    type=['xlsx', 'xls'],
    help="Selecione um arquivo Excel com os dados dos chamados técnicos"
)

# Carregar dados
df = load_data(uploaded_file)

# Inicializar variáveis de sessão para filtros interativos
if 'filtro_status' not in st.session_state:
    st.session_state.filtro_status = None
if 'filtro_categoria' not in st.session_state:
    st.session_state.filtro_categoria = None
if 'filtro_tecnico' not in st.session_state:
    st.session_state.filtro_tecnico = None
if 'filtro_prioridade' not in st.session_state:
    st.session_state.filtro_prioridade = None

# Sidebar - Filtros
st.sidebar.header("🔍 Filtros de Análise")
if not df.empty:
    # Filtro por período
    if 'Data de abertura' in df.columns:
        min_date = df['Data de abertura'].min().date()
        max_date = df['Data de abertura'].max().date()
        
        # Definir período padrão baseado nos dados disponíveis
        hoje = date.today()
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        ultimo_dia_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        
        # Verificar se o mês atual está dentro do range dos dados
        if primeiro_dia_mes >= min_date and ultimo_dia_mes <= max_date:
            # Usar mês atual como padrão
            periodo_padrao = [primeiro_dia_mes, ultimo_dia_mes]
        else:
            # Usar último mês disponível como padrão
            if max_date.month == 1:
                ultimo_mes = date(max_date.year - 1, 12, 1)
            else:
                ultimo_mes = date(max_date.year, max_date.month - 1, 1)
            
            if ultimo_mes.month == 12:
                ultimo_dia_ultimo_mes = date(ultimo_mes.year + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo_dia_ultimo_mes = date(ultimo_mes.year, ultimo_mes.month + 1, 1) - timedelta(days=1)
            
            periodo_padrao = [ultimo_mes, ultimo_dia_ultimo_mes]
        
        # Usar período padrão, mas permitir alteração
        date_range = st.sidebar.date_input(
            "📅 Período de análise",
            periodo_padrao,
            min_value=min_date,
            max_value=max_date,
            help="Período padrão baseado nos dados disponíveis. Clique para alterar se necessário."
        )
    
    # Filtro por técnico
    tecnicos = ['Todos'] + sorted(df['Atribuído - Técnico'].dropna().unique().tolist())
    tecnico_selecionado = st.sidebar.selectbox("👨‍💻 Técnico", tecnicos)
    
    # Filtro por status
    status_options = ['Todos'] + sorted(df['Status'].dropna().unique().tolist())
    status_selecionado = st.sidebar.selectbox("📊 Status", status_options)
    
    # Filtro por prioridade
    prioridade_options = ['Todas'] + sorted(df['Prioridade'].dropna().unique().tolist())
    prioridade_selecionada = st.sidebar.selectbox("⚡ Prioridade", prioridade_options)
    
    # Filtro por categoria
    if 'Categoria Limpa' in df.columns:
        categorias = ['Todas'] + sorted(df['Categoria Limpa'].dropna().unique().tolist())
        categoria_selecionada = st.sidebar.selectbox("🏷️ Categoria", categorias)
    
    # Botão para limpar filtros interativos
    if st.sidebar.button("🔄 Limpar Filtros Interativos"):
        st.session_state.filtro_status = None
        st.session_state.filtro_categoria = None
        st.session_state.filtro_tecnico = None
        st.session_state.filtro_prioridade = None
        st.rerun()
    
    # Aplicar filtros
    if len(date_range) == 2:
        mask = (df['Data de abertura'].dt.date >= date_range[0]) & (df['Data de abertura'].dt.date <= date_range[1])
        df_filtered = df[mask]
    else:
        df_filtered = df.copy()
    
    if tecnico_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['Atribuído - Técnico'] == tecnico_selecionado]
    
    if status_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['Status'] == status_selecionado]
    
    if prioridade_selecionada != 'Todas':
        df_filtered = df_filtered[df_filtered['Prioridade'] == prioridade_selecionada]
    
    if 'Categoria Limpa' in df.columns and categoria_selecionada != 'Todas':
        df_filtered = df_filtered[df_filtered['Categoria Limpa'] == categoria_selecionada]
    
    # Aplicar filtros interativos
    if st.session_state.filtro_status is not None:
        df_filtered = df_filtered[df_filtered['Status'] == st.session_state.filtro_status]
    
    if st.session_state.filtro_categoria is not None:
        df_filtered = df_filtered[df_filtered['Categoria Limpa'] == st.session_state.filtro_categoria]
    
    if st.session_state.filtro_tecnico is not None:
        df_filtered = df_filtered[df_filtered['Atribuído - Técnico'] == st.session_state.filtro_tecnico]
    
    if st.session_state.filtro_prioridade is not None:
        df_filtered = df_filtered[df_filtered['Prioridade'] == st.session_state.filtro_prioridade]

# Página principal
st.title("📊 Dashboard de Análise de Chamados Técnicos - HMSI")

if uploaded_file is not None:
    st.markdown(f"**Arquivo carregado:** {uploaded_file.name}")
    if not df.empty:
        st.markdown(f"**Total de registros:** {len(df):,} chamados")
        if 'Data de abertura' in df.columns:
            min_date = df['Data de abertura'].min().date()
            max_date = df['Data de abertura'].max().date()
            st.markdown(f"**Período:** {min_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')}")
else:
    st.markdown("**📁 Faça upload de uma planilha Excel para começar a análise**")
    st.info("💡 Use o painel lateral para carregar sua planilha de chamados técnicos")
    st.markdown("**Formato esperado:** Arquivo Excel (.xlsx) com colunas: ID, Título, Status, Prioridade, Categoria, Técnico, Datas, etc.")

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado ou erro ao carregar o arquivo.")
else:
    # Métricas principais (atualizadas dinamicamente)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_chamados = len(df_filtered)
        st.metric("📞 Total de Chamados", f"{total_chamados:,}")
    with col2:
        tempo_medio = df_filtered['Tempo Resolução (h)'].mean()
        st.metric("⏱️ Tempo Médio (h)", f"{tempo_medio:.1f}" if not pd.isna(tempo_medio) else "N/A")
    with col3:
        dentro_sla = len(df_filtered[df_filtered['Tempo Resolução (h)'] <= 8]) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
        st.metric("✅ Dentro do SLA (8h)", f"{dentro_sla:.1f}%" if not pd.isna(dentro_sla) else "N/A")
    with col4:
        chamados_por_tecnico = len(df_filtered) / df_filtered['Atribuído - Técnico'].nunique() if df_filtered['Atribuído - Técnico'].nunique() > 0 else 0
        st.metric("👥 Chamados/Técnico", f"{chamados_por_tecnico:.1f}")

    # Gráficos interativos
    st.subheader("📈 Análise Temporal dos Chamados")
    col5, col6 = st.columns(2)
    
    with col5:
        # Gráfico de chamados por mês (interativo)
        if not df_filtered.empty:
            df_mensal = df_filtered.groupby(df_filtered['Data de abertura'].dt.to_period('M'))['ID'].count().reset_index()
            df_mensal['Data de abertura'] = df_mensal['Data de abertura'].astype(str)
            
            fig1 = px.bar(df_mensal, x='Data de abertura', y='ID', 
                         title="Chamados por Mês",
                         labels={'ID': 'Número de Chamados', 'Data de abertura': 'Mês'},
                         color='ID',
                         color_continuous_scale='Blues')
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
    
    with col6:
        # Gráfico de chamados por dia da semana (interativo)
        if not df_filtered.empty:
            df_diario = df_filtered.groupby(df_filtered['Data de abertura'].dt.day_name())['ID'].count().reset_index()
            dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df_diario['Data de abertura'] = pd.Categorical(df_diario['Data de abertura'], categories=dias_ordem, ordered=True)
            df_diario = df_diario.sort_values('Data de abertura')
            
            fig2 = px.bar(df_diario, x='Data de abertura', y='ID',
                         title="Chamados por Dia da Semana",
                         labels={'ID': 'Número de Chamados', 'Data de abertura': 'Dia da Semana'},
                         color='ID',
                         color_continuous_scale='Reds')
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Análise por Status e Prioridade (interativos)
    st.subheader("📊 Análise por Status e Prioridade")
    col7, col8 = st.columns(2)
    
    with col7:
        # Gráfico de pizza - Status (interativo)
        if not df_filtered.empty:
            status_counts = df_filtered['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Quantidade']
            
            fig3 = px.pie(status_counts, values='Quantidade', names='Status',
                         title="Distribuição por Status",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig3.update_traces(textposition='inside', textinfo='percent+label')
            
            # Tornar o gráfico interativo para filtros
            selected_points = plotly_events(fig3, key="status_chart", click_event=True)
            if selected_points and len(selected_points) > 0:
                if 'label' in selected_points[0]:
                    status_clicado = selected_points[0]['label']
                    st.session_state.filtro_status = status_clicado
                    st.rerun()
            
            st.plotly_chart(fig3, use_container_width=True)
    
    with col8:
        # Gráfico de barras - Prioridade (interativo)
        if not df_filtered.empty:
            prioridade_counts = df_filtered['Prioridade'].value_counts().reset_index()
            prioridade_counts.columns = ['Prioridade', 'Quantidade']
            
            fig4 = px.bar(prioridade_counts, x='Prioridade', y='Quantidade',
                         title="Distribuição por Prioridade",
                         color='Quantidade',
                         color_continuous_scale='Viridis')
            fig4.update_layout(showlegend=False)
            
            # Tornar o gráfico interativo para filtros
            selected_points = plotly_events(fig4, key="prioridade_chart", click_event=True)
            if selected_points and len(selected_points) > 0:
                if 'x' in selected_points[0]:
                    prioridade_clicada = selected_points[0]['x']
                    st.session_state.filtro_prioridade = prioridade_clicada
                    st.rerun()
            
            st.plotly_chart(fig4, use_container_width=True)

    # Análise por Categoria (interativa)
    st.subheader("🏷️ Análise por Categoria")
    if 'Categoria Limpa' in df.columns:
        col9, col10 = st.columns(2)
        
        with col9:
            # Top 10 categorias (interativo)
            if not df_filtered.empty:
                top_categorias = df_filtered['Categoria Limpa'].value_counts().head(10).reset_index()
                top_categorias.columns = ['Categoria', 'Quantidade']
                
                fig5 = px.bar(top_categorias, x='Quantidade', y='Categoria',
                             title="Top 10 Categorias",
                             orientation='h',
                             color='Quantidade',
                             color_continuous_scale='Greens')
                fig5.update_layout(showlegend=False)
                
                # Tornar o gráfico interativo para filtros
                selected_points = plotly_events(fig5, key="categoria_chart", click_event=True)
                if selected_points and len(selected_points) > 0:
                    if 'y' in selected_points[0]:
                        categoria_clicada = selected_points[0]['y']
                        st.session_state.filtro_categoria = categoria_clicada
                        st.rerun()
                
                st.plotly_chart(fig5, use_container_width=True)
        
        with col10:
            # Gráfico de pizza - Categorias principais (interativo)
            if not df_filtered.empty:
                cat_counts = df_filtered['Categoria Limpa'].value_counts()
                if len(cat_counts) > 8:
                    top_cats = cat_counts.head(7)
                    outros = cat_counts.iloc[7:].sum()
                    cat_counts = pd.concat([top_cats, pd.Series([outros], index=['Outros'])])
                
                cat_counts_df = cat_counts.reset_index()
                cat_counts_df.columns = ['Categoria', 'Quantidade']
                
                fig6 = px.pie(cat_counts_df, values='Quantidade', names='Categoria',
                             title="Distribuição por Categoria",
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig6.update_traces(textposition='inside', textinfo='percent+label')
                
                # Tornar o gráfico interativo para filtros
                selected_points = plotly_events(fig6, key="categoria_pie_chart", click_event=True)
                if selected_points and len(selected_points) > 0:
                    if 'label' in selected_points[0]:
                        categoria_clicada = selected_points[0]['label']
                        if categoria_clicada != 'Outros':
                            st.session_state.filtro_categoria = categoria_clicada
                            st.rerun()
                
                st.plotly_chart(fig6, use_container_width=True)

    # Análise por Técnico (interativa)
    st.subheader("👨‍💻 Análise por Técnico")
    col11, col12 = st.columns(2)
    
    with col11:
        # Eficiência por técnico (interativo)
        if not df_filtered.empty and 'Atribuído - Técnico' in df_filtered.columns:
            df_tecnicos = df_filtered.groupby('Atribuído - Técnico').agg({
                'ID': 'count',
                'Tempo Resolução (h)': 'mean'
            }).reset_index()
            df_tecnicos['Eficiência'] = df_tecnicos['ID'] / df_tecnicos['Tempo Resolução (h)']
            df_tecnicos = df_tecnicos.sort_values('Eficiência', ascending=False)
            
            fig7 = px.bar(df_tecnicos, x='Atribuído - Técnico', y='Eficiência',
                         title="Eficiência por Técnico",
                         color='Eficiência',
                         color_continuous_scale='Blues')
            fig7.update_layout(showlegend=False, xaxis_tickangle=-45)
            
            # Tornar o gráfico interativo para filtros
            selected_points = plotly_events(fig7, key="eficiencia_chart", click_event=True)
            if selected_points and len(selected_points) > 0:
                if 'x' in selected_points[0]:
                    tecnico_clicado = selected_points[0]['x']
                    st.session_state.filtro_tecnico = tecnico_clicado
                    st.rerun()
            
            st.plotly_chart(fig7, use_container_width=True)
    
    with col12:
        # Chamados por técnico (interativo)
        if not df_filtered.empty and 'Atribuído - Técnico' in df_filtered.columns:
            tecnicos_counts = df_filtered['Atribuído - Técnico'].value_counts().head(10).reset_index()
            tecnicos_counts.columns = ['Técnico', 'Quantidade']
            
            fig8 = px.bar(tecnicos_counts, x='Técnico', y='Quantidade',
                         title="Chamados por Técnico (Top 10)",
                         color='Quantidade',
                         color_continuous_scale='Reds')
            fig8.update_layout(showlegend=False, xaxis_tickangle=-45)
            
            # Tornar o gráfico interativo para filtros
            selected_points = plotly_events(fig8, key="tecnico_chart", click_event=True)
            if selected_points and len(selected_points) > 0:
                if 'x' in selected_points[0]:
                    tecnico_clicado = selected_points[0]['x']
                    st.session_state.filtro_tecnico = tecnico_clicado
                    st.rerun()
            
            st.plotly_chart(fig8, use_container_width=True)

    # Tabela detalhada
    st.subheader("📋 Detalhes dos Chamados")
    if not df_filtered.empty:
        # Selecionar colunas relevantes para exibição
        colunas_exibicao = ['ID', 'Título', 'Status', 'Prioridade', 'Categoria Limpa', 
                           'Atribuído - Técnico', 'Data de abertura', 'Tempo Resolução (h)']
        colunas_disponiveis = [col for col in colunas_exibicao if col in df_filtered.columns]
        
        df_exibicao = df_filtered[colunas_disponiveis].sort_values('Data de abertura', ascending=False)
        st.dataframe(df_exibicao, height=400, use_container_width=True)
    else:
        st.info("Nenhum chamado encontrado com os filtros aplicados.")

# Rodapé
st.markdown("---")
st.markdown("**Dashboard desenvolvido Pedro Henrique (Analista de Sistema Pleno)** | Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
st.markdown("**Fonte:** Sistema de Chamados Técnicos HMSI")