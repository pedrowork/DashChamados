import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit_plotly_events import plotly_events
from datetime import datetime, date, timedelta
import os
import numpy as np
import io
import calendar

# Carregar variáveis de ambiente do arquivo .env (se disponível)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Configuração do dashboard

st.set_page_config(
    page_title="Dashboard de Chamados Técnicos - HMSI", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# CSS para esconder elementos de carregamento e menu
st.markdown("""
<style>
    /* Esconder spinner de carregamento */
    .stSpinner > div {
        display: none !important;
    }
    
    /* Esconder "Running..." */
    .stApp [data-testid="stStatusWidget"] {
        display: none !important;
    }
    
    /* Esconder menu de 3 pontos */
    #MainMenu {
        visibility: hidden;
    }
    
    /* Esconder footer "Made with Streamlit" */
    footer {
        visibility: hidden;
    }
    
    /* Esconder botão de deploy */
    .stDeployButton {
        display: none !important;
    }
    
    /* Header visível para permitir o toggle da sidebar em telas pequenas */
    /* header { visibility: hidden !important; } */
</style>
""", unsafe_allow_html=True)

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
                    expected_username = os.getenv("STREAMLIT_USERNAME")
                    expected_password = os.getenv("STREAMLIT_PASSWORD")

                    if not expected_username or not expected_password:
                        st.error("⚠️ Variáveis de ambiente STREAMLIT_USERNAME/STREAMLIT_PASSWORD não configuradas.")
                        return False

                    if username == expected_username and password == expected_password:
                        st.session_state.logged_in = True
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
                        return False
        
        # QR abaixo do login (centralizado)
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            try:
                st.image("doação.jpeg", width=120, caption="PIX - Aurora")
            except Exception:
                pass
        
        # QR também na barra lateral
        st.sidebar.markdown("---")
        st.sidebar.subheader("💝 Apoie a Aurora")
        try:
            st.sidebar.image("doação.jpeg", width=120, caption="PIX - Aurora")
        except Exception:
            pass
        
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


# Informações sobre fonte de dados
# st.sidebar.markdown("---")
# st.sidebar.header("📁 Fonte de Dados")
# st.sidebar.info("**Arquivo:** glpi.csv  \n**Localização:** Raiz do projeto")

# Mostrar botão de logout na sidebar
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Carregar dados
@st.cache_data

def load_data(uploaded_bytes=None):
    """
    Carrega dados do GLPI a partir de upload do usuário ou do arquivo local glpi.csv
    """
    # 1) Se o usuário enviou um arquivo, usar o upload
    if uploaded_bytes is not None:
        try:
            df = pd.read_csv(io.StringIO(uploaded_bytes.decode('utf-8-sig')), sep=';')
            
            # Converter colunas de data aceitando '/' ou '-' e dia primeiro
            if 'Data Abertura' in df.columns:
                df['Data Abertura Datetime'] = pd.to_datetime(df['Data Abertura'], dayfirst=True, errors='coerce')
            
            if 'Data Atualização' in df.columns:
                df['Data Atualização Datetime'] = pd.to_datetime(df['Data Atualização'], dayfirst=True, errors='coerce')
            
            if 'Data SLA' in df.columns:
                df['Data SLA Datetime'] = pd.to_datetime(df['Data SLA'], dayfirst=True, errors='coerce')
            
            # Calcular tempo de resolução em horas
            if 'Data Abertura Datetime' in df.columns and 'Data Atualização Datetime' in df.columns:
                df['Tempo Resolução (h)'] = (df['Data Atualização Datetime'] - df['Data Abertura Datetime']).dt.total_seconds() / 3600
            
            # Limpar e padronizar categorias
            if 'Categoria' in df.columns:
                df['Categoria Limpa'] = df['Categoria'].str.replace('SETOR DE INFORMATICA > ', '', regex=False).str.replace('SETOR DE INFORMATICA', 'OUTROS')
            
            return df
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo enviado: {e}")
            return pd.DataFrame()

    # 2) Caso não haja upload, tentar arquivo local
    file_path = "glpi.csv"

    if not os.path.exists(file_path):
        st.error("❌ Nenhum arquivo encontrado. Faça upload do glpi.csv na barra lateral.")
        return pd.DataFrame()

    try:
        # Ler arquivo CSV
        df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
        
        # Converter colunas de data aceitando '/' ou '-' e dia primeiro
        if 'Data Abertura' in df.columns:
            df['Data Abertura Datetime'] = pd.to_datetime(df['Data Abertura'], dayfirst=True, errors='coerce')
        
        if 'Data Atualização' in df.columns:
            df['Data Atualização Datetime'] = pd.to_datetime(df['Data Atualização'], dayfirst=True, errors='coerce')
        
        if 'Data SLA' in df.columns:
            df['Data SLA Datetime'] = pd.to_datetime(df['Data SLA'], dayfirst=True, errors='coerce')
        
        # Calcular tempo de resolução em horas
        if 'Data Abertura Datetime' in df.columns and 'Data Atualização Datetime' in df.columns:
            df['Tempo Resolução (h)'] = (df['Data Atualização Datetime'] - df['Data Abertura Datetime']).dt.total_seconds() / 3600
        
        # Limpar e padronizar categorias
        if 'Categoria' in df.columns:
            df['Categoria Limpa'] = df['Categoria'].str.replace('SETOR DE INFORMATICA > ', '', regex=False).str.replace('SETOR DE INFORMATICA', 'OUTROS')
        
        return df

    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Upload de dados
st.sidebar.markdown("### 📤 Upload de Dados")
uploaded_file = st.sidebar.file_uploader(
    "Carregue o arquivo glpi.csv",
    type=["csv"],
    help="Selecione o CSV exportado do GLPI (separador ';' e codificação UTF-8)."
)

# Carregar dados a partir do upload (ou do arquivo local se nenhum upload for feito)
df = load_data(uploaded_file.getvalue() if uploaded_file is not None else None)

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

    date_range = []
    if 'Data Abertura Datetime' in df.columns:
        datas_validas = df['Data Abertura Datetime'].dropna()
        if not datas_validas.empty:
            min_date = datas_validas.min().date()
            max_date = datas_validas.max().date()
            
            # Definir período padrão baseado nos dados disponíveis
            hoje = date.today()
            primeiro_dia_mes = date(hoje.year, hoje.month, 1)
            ultimo_dia_mes = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
            
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
                
                ultimo_dia_ultimo_mes = date(
                    ultimo_mes.year,
                    ultimo_mes.month,
                    calendar.monthrange(ultimo_mes.year, ultimo_mes.month)[1]
                )
                
                periodo_padrao = [ultimo_mes, ultimo_dia_ultimo_mes]
            
            # Usar período padrão, mas permitir alteração
            date_range = st.sidebar.date_input(
                "📅 Período de análise",
                periodo_padrao,
                min_value=min_date,
                max_value=max_date,
                help="Período padrão baseado nos dados disponíveis. Clique para alterar se necessário."
            )
        else:
            st.sidebar.info("📅 Datas de abertura inválidas ou ausentes. Filtro de período desativado.")
            date_range = []
    else:
        st.sidebar.info("📅 Coluna de data não encontrada. Filtro de período desativado.")
    
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

        mask = (df['Data Abertura Datetime'].dt.date >= date_range[0]) & (df['Data Abertura Datetime'].dt.date <= date_range[1])
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


# Verificar se os dados foram carregados
if df.empty:

    st.error("⚠️ Nenhum dado encontrado! Verifique se o arquivo glpi.csv está na raiz do projeto.")
    st.stop()

# Mostrar informações dos dados
st.markdown(f"**📊 Total de registros:** {len(df):,} chamados")
if 'Data Abertura Datetime' in df.columns:
    datas_validas_info = df['Data Abertura Datetime'].dropna()
    if not datas_validas_info.empty:
        min_date = datas_validas_info.min().date()
        max_date = datas_validas_info.max().date()
        st.markdown(f"**📅 Período:** {min_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')}")
    else:
        st.markdown("**📅 Período:** Dados de data ausentes/invalidos")

# Iniciar visualizações
if True:
    # Métricas principais resumidas
    st.markdown("---")
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


    st.markdown("---")
    
    # ABAS PRINCIPAIS DE ANÁLISE
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "📊 1. KPIs", 
        "⏰ 2. Temporal", 
        "🏷️ 3. Categoria",
        "👨‍💻 4. Técnicos",
        "👥 5. Requerentes",
        "🏥 6. Localização",
        "⚡ 7. Prioridade",
        "📈 8. Status",
        "🔮 9. Preditiva",
        "✅ 10. Qualidade",
        "🖨️ 11. Específicas"
    ])
    
    # ====================================================================
    # ABA 1: INDICADORES DE PERFORMANCE (KPIs)
    # ====================================================================
    with tab1:
        st.header("📊 Indicadores de Performance (KPIs)")
        
        # KPIs principais
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        with col_kpi1:
            st.subheader("✅ Taxa de Resolução")
            status_counts = df_filtered['Status'].value_counts()
            total = len(df_filtered)
            
            # Calcular percentuais
            fechados = status_counts.get('Fechado', 0) / total * 100 if total > 0 else 0
            solucionados = status_counts.get('Solucionado', 0) / total * 100 if total > 0 else 0
            pendentes = status_counts.get('Pendente', 0) / total * 100 if total > 0 else 0
            
            # Gráfico de pizza - Status
            fig_status = px.pie(
                values=[status_counts.get('Fechado', 0), status_counts.get('Solucionado', 0), status_counts.get('Pendente', 0)],
                names=['Fechado', 'Solucionado', 'Pendente'],
                         title="Distribuição por Status",
                color_discrete_sequence=['#28a745', '#17a2b8', '#ffc107'],
                hole=0.4
            )
            fig_status.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_status, use_container_width=True)
            
            st.metric("Fechados", f"{fechados:.1f}%", delta=f"{status_counts.get('Fechado', 0)} chamados")
            st.metric("Solucionados", f"{solucionados:.1f}%", delta=f"{status_counts.get('Solucionado', 0)} chamados")
            st.metric("Pendentes", f"{pendentes:.1f}%", delta=f"{status_counts.get('Pendente', 0)} chamados")
        
        with col_kpi2:
            st.subheader("⏱️ Tempo Médio de Resolução")
            tempo_stats = df_filtered['Tempo Resolução (h)'].describe()
            
            fig_tempo = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = tempo_stats['mean'] if not pd.isna(tempo_stats['mean']) else 0,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Tempo Médio (horas)"},
                delta = {'reference': 24},
                gauge = {
                    'axis': {'range': [None, 72]},
                    'bar': {'color': "#007bff"},
                    'steps' : [
                        {'range': [0, 8], 'color': "#d4edda"},
                        {'range': [8, 24], 'color': "#fff3cd"},
                        {'range': [24, 72], 'color': "#f8d7da"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 24
                    }
                }
            ))
            st.plotly_chart(fig_tempo, use_container_width=True)
            
            st.metric("Média", f"{tempo_stats['mean']:.1f}h" if not pd.isna(tempo_stats['mean']) else "N/A")
            st.metric("Mediana", f"{tempo_stats['50%']:.1f}h" if not pd.isna(tempo_stats['50%']) else "N/A")
            st.metric("Máximo", f"{tempo_stats['max']:.1f}h" if not pd.isna(tempo_stats['max']) else "N/A")
        
        with col_kpi3:
            st.subheader("📈 SLA Compliance")
            
            # Calcular SLA (8h)
            total_resolvidos = len(df_filtered[df_filtered['Status'].isin(['Fechado', 'Solucionado'])])
            dentro_sla_count = len(df_filtered[(df_filtered['Tempo Resolução (h)'] <= 8) & (df_filtered['Status'].isin(['Fechado', 'Solucionado']))])
            fora_sla_count = total_resolvidos - dentro_sla_count
            
            sla_percent = (dentro_sla_count / total_resolvidos * 100) if total_resolvidos > 0 else 0
            
            # Gráfico de SLA
            fig_sla = go.Figure(data=[
                go.Bar(name='Dentro do SLA (≤8h)', x=['SLA'], y=[dentro_sla_count], marker_color='#28a745'),
                go.Bar(name='Fora do SLA (>8h)', x=['SLA'], y=[fora_sla_count], marker_color='#dc3545')
            ])
            fig_sla.update_layout(
                title="Cumprimento do SLA (8 horas)",
                barmode='stack',
                showlegend=True
            )
            st.plotly_chart(fig_sla, use_container_width=True)
            
            st.metric("✅ Dentro do SLA", f"{sla_percent:.1f}%", delta=f"{dentro_sla_count} chamados")
            st.metric("❌ Fora do SLA", f"{100-sla_percent:.1f}%", delta=f"{fora_sla_count} chamados", delta_color="inverse")
        
        st.markdown("---")
        
        # Produtividade por técnico
        st.subheader("🚀 Produtividade por Técnico")
        col_prod1, col_prod2 = st.columns(2)
        
        with col_prod1:
            # Chamados por técnico
            df_tecnicos = df_filtered.groupby('Atribuído - Técnico').agg({
                'ID': 'count',
                'Tempo Resolução (h)': 'mean'
            }).reset_index()
            df_tecnicos.columns = ['Técnico', 'Total Chamados', 'Tempo Médio (h)']
            df_tecnicos = df_tecnicos.sort_values('Total Chamados', ascending=False).head(10)
            
            fig_tec = px.bar(
                df_tecnicos, 
                x='Total Chamados', 
                y='Técnico',
                title="Top 10 Técnicos - Volume de Chamados",
                orientation='h',
                color='Total Chamados',
                color_continuous_scale='Blues',
                text='Total Chamados'
            )
            fig_tec.update_traces(textposition='outside')
            st.plotly_chart(fig_tec, use_container_width=True)
        
        with col_prod2:
            # Eficiência (Chamados/hora)
            df_tecnicos['Eficiência'] = df_tecnicos['Total Chamados'] / df_tecnicos['Tempo Médio (h)']
            df_tecnicos_ef = df_tecnicos.sort_values('Eficiência', ascending=False).head(10)
            
            fig_ef = px.bar(
                df_tecnicos_ef,
                x='Eficiência',
                y='Técnico',
                title="Top 10 Técnicos - Eficiência (Chamados/Hora)",
                orientation='h',
                         color='Eficiência',
                color_continuous_scale='Greens',
                text='Eficiência'
            )
            fig_ef.update_traces(textposition='outside', texttemplate='%{text:.2f}')
            st.plotly_chart(fig_ef, use_container_width=True)

    # ====================================================================
    # ABA 2: ANÁLISE TEMPORAL
    # ====================================================================
    with tab2:
        st.header("⏰ Análise Temporal dos Chamados")
        
        # Volume por período
        st.subheader("📅 Volume por Período")
        col_temp1, col_temp2 = st.columns(2)
        
        with col_temp1:
            # Chamados por mês
            df_mensal = df_filtered.groupby(df_filtered['Data Abertura Datetime'].dt.to_period('M'))['ID'].count().reset_index()
            df_mensal['Mês'] = df_mensal['Data Abertura Datetime'].astype(str)
            
            fig_mes = px.bar(
                df_mensal, 
                x='Mês', 
                y='ID',
                title="📊 Volume de Chamados por Mês",
                labels={'ID': 'Número de Chamados', 'Mês': 'Período'},
                         color='ID',

                color_continuous_scale='Blues',
                text='ID'
            )
            fig_mes.update_traces(textposition='outside')
            fig_mes.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_mes, use_container_width=True)
        
        with col_temp2:
            # Tendência mensal
            df_mensal['Crescimento'] = df_mensal['ID'].pct_change() * 100
            
            fig_trend = px.line(
                df_mensal,
                x='Mês',
                y='ID',
                title="📈 Tendência de Chamados (Crescimento/Queda)",
                labels={'ID': 'Total de Chamados'},
                markers=True
            )
            fig_trend.update_traces(line_color='#17a2b8', line_width=3)
            fig_trend.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        st.markdown("---")
        
        # Horário de pico
        st.subheader("⏰ Horário de Pico")
        col_temp3, col_temp4 = st.columns(2)
        
        with col_temp3:
            # Chamados por hora do dia
            if 'Hora Abertura' in df_filtered.columns:
                df_filtered['Hora'] = df_filtered['Hora Abertura'].str[:2]  # Pega apenas a hora (primeiros 2 caracteres)
                df_hora = df_filtered.groupby('Hora')['ID'].count().reset_index().sort_values('Hora')
                
                fig_hora = px.bar(
                    df_hora,
                    x='Hora',
                    y='ID',
                    title="📊 Distribuição de Chamados por Hora do Dia",
                    labels={'ID': 'Número de Chamados', 'Hora': 'Hora do Dia'},
                    color='ID',
                    color_continuous_scale='Oranges',
                    text='ID'
                )
                fig_hora.update_traces(textposition='outside')
                st.plotly_chart(fig_hora, use_container_width=True)
        
        with col_temp4:
            # Chamados por dia da semana
            df_filtered['Dia Semana'] = df_filtered['Data Abertura Datetime'].dt.day_name()
            dias_pt = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 
                      'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
            df_filtered['Dia Semana PT'] = df_filtered['Dia Semana'].map(dias_pt)
            
            df_dia_semana = df_filtered.groupby('Dia Semana PT')['ID'].count().reset_index()
            ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            df_dia_semana['Dia Semana PT'] = pd.Categorical(df_dia_semana['Dia Semana PT'], categories=ordem_dias, ordered=True)
            df_dia_semana = df_dia_semana.sort_values('Dia Semana PT')
            
            fig_dia = px.bar(
                df_dia_semana,
                x='Dia Semana PT',
                y='ID',
                title="📊 Distribuição por Dia da Semana",
                labels={'ID': 'Número de Chamados', 'Dia Semana PT': 'Dia'},
                color='ID',
                color_continuous_scale='Reds',
                text='ID'
            )
            fig_dia.update_traces(textposition='outside')
            st.plotly_chart(fig_dia, use_container_width=True)
        
        st.markdown("---")
        
        # Velocidade de atendimento
        st.subheader("⚡ Velocidade de Atendimento")
        col_temp5, col_temp6 = st.columns(2)
        
        with col_temp5:
            # Distribuição do tempo de resolução
            fig_dist = px.histogram(
                df_filtered[df_filtered['Tempo Resolução (h)'] < 100],  # Filtrar outliers
                x='Tempo Resolução (h)',
                nbins=30,
                title="📊 Distribuição do Tempo de Resolução",
                labels={'Tempo Resolução (h)': 'Tempo (horas)'},
                color_discrete_sequence=['#6610f2']
            )
            fig_dist.add_vline(x=8, line_dash="dash", line_color="red", annotation_text="SLA (8h)")
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col_temp6:
            # Box plot por status
            fig_box = px.box(
                df_filtered[df_filtered['Tempo Resolução (h)'] < 100],
                x='Status',
                y='Tempo Resolução (h)',
                title="📦 Tempo de Resolução por Status",
                color='Status',
                color_discrete_sequence=['#28a745', '#17a2b8', '#ffc107']
            )
            st.plotly_chart(fig_box, use_container_width=True)
    
    # ====================================================================
    # ABA 3: ANÁLISE POR CATEGORIA
    # ====================================================================
    with tab3:
        st.header("🏷️ Análise por Categoria")
        
        # Top problemas
        st.subheader("🏆 Top Problemas Mais Frequentes")
        col_cat1, col_cat2 = st.columns(2)
        
        with col_cat1:
            # Top 10 categorias
                top_categorias = df_filtered['Categoria Limpa'].value_counts().head(10).reset_index()
                top_categorias.columns = ['Categoria', 'Quantidade']
                

        fig_top_cat = px.bar(
            top_categorias,
            x='Quantidade',
            y='Categoria',
            title="📊 Top 10 Categorias Mais Frequentes",
                             orientation='h',
                             color='Quantidade',

            color_continuous_scale='Greens',
            text='Quantidade'
        )
        fig_top_cat.update_traces(textposition='outside')
        st.plotly_chart(fig_top_cat, use_container_width=True)
        
        with col_cat2:
            # Gráfico de pizza
                cat_counts = df_filtered['Categoria Limpa'].value_counts()

        if len(cat_counts) > 7:
                    top_cats = cat_counts.head(7)
                    outros = cat_counts.iloc[7:].sum()
                    cat_counts = pd.concat([top_cats, pd.Series([outros], index=['Outros'])])
                

        cat_df = cat_counts.reset_index()
        cat_df.columns = ['Categoria', 'Quantidade']
        
        fig_cat_pie = px.pie(
            cat_df,
            values='Quantidade',
            names='Categoria',
            title="🥧 Distribuição Percentual por Categoria",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_cat_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_cat_pie, use_container_width=True)
        
        st.markdown("---")
        
        # Categorias críticas (maior tempo de resolução)
        st.subheader("📉 Categorias Críticas (Maior Tempo de Resolução)")
        col_cat3, col_cat4 = st.columns(2)
        
        with col_cat3:
            # Categorias com maior tempo médio
            df_cat_tempo = df_filtered.groupby('Categoria Limpa')['Tempo Resolução (h)'].mean().reset_index()
            df_cat_tempo = df_cat_tempo.sort_values('Tempo Resolução (h)', ascending=False).head(10)
            df_cat_tempo.columns = ['Categoria', 'Tempo Médio (h)']
            
            fig_cat_tempo = px.bar(
                df_cat_tempo,
                x='Tempo Médio (h)',
                y='Categoria',
                title="⏱️ Categorias com Maior Tempo Médio de Resolução",
                orientation='h',
                color='Tempo Médio (h)',
                color_continuous_scale='Reds',
                text='Tempo Médio (h)'
            )
            fig_cat_tempo.update_traces(textposition='outside', texttemplate='%{text:.1f}h')
            st.plotly_chart(fig_cat_tempo, use_container_width=True)
        
        with col_cat4:
            # Recorrência - problemas repetitivos
            df_cat_count = df_filtered.groupby('Categoria Limpa').agg({
                'ID': 'count',

                'Requerente - Requerente': 'nunique'
            }).reset_index()

            df_cat_count.columns = ['Categoria', 'Total Chamados', 'Usuários Únicos']
            df_cat_count['Recorrência'] = df_cat_count['Total Chamados'] / df_cat_count['Usuários Únicos']
            df_cat_count = df_cat_count.sort_values('Recorrência', ascending=False).head(10)
            
            fig_recor = px.scatter(
                df_cat_count,
                x='Usuários Únicos',
                y='Total Chamados',
                size='Recorrência',
                color='Recorrência',
                hover_data=['Categoria'],
                title="🔄 Recorrência de Problemas (Tamanho = Recorrência)",
                labels={'Usuários Únicos': 'Usuários Diferentes', 'Total Chamados': 'Total de Chamados'},
                color_continuous_scale='Viridis',
                text='Categoria'
            )
            st.plotly_chart(fig_recor, use_container_width=True)
        
        st.markdown("---")
        
        # Padrões sazonais
        st.subheader("💡 Padrões Sazonais - Categoria x Período")
        
        # Heatmap: Categoria x Mês
        df_heatmap = df_filtered.copy()
        df_heatmap['Mês'] = df_heatmap['Data Abertura Datetime'].dt.to_period('M').astype(str)
        
        # Selecionar top 10 categorias para o heatmap
        top_10_cat = df_filtered['Categoria Limpa'].value_counts().head(10).index.tolist()
        df_heatmap_filtered = df_heatmap[df_heatmap['Categoria Limpa'].isin(top_10_cat)]
        
        heatmap_data = df_heatmap_filtered.pivot_table(
            index='Categoria Limpa',
            columns='Mês',
            values='ID',
            aggfunc='count',
            fill_value=0
        )
        
        fig_heatmap = px.imshow(
            heatmap_data,
            title="🗓️ Mapa de Calor: Categorias x Meses",
            labels=dict(x="Mês", y="Categoria", color="Chamados"),
            color_continuous_scale='YlOrRd',
            aspect="auto"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Tabela de detalhes por categoria
        st.subheader("📋 Detalhes por Categoria")
        df_categoria_detalhe = df_filtered.groupby('Categoria Limpa').agg({
            'ID': 'count',
            'Tempo Resolução (h)': 'mean',
            'Requerente - Requerente': 'nunique',
            'Localização': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'N/A'
        }).reset_index()
        df_categoria_detalhe.columns = ['Categoria', 'Total', 'Tempo Médio (h)', 'Usuários Únicos', 'Localização Mais Comum']
        df_categoria_detalhe = df_categoria_detalhe.sort_values('Total', ascending=False)
        
        st.dataframe(df_categoria_detalhe, height=400, use_container_width=True)
    
    # ====================================================================
    # ABA 4: ANÁLISE DE TÉCNICOS
    # ====================================================================
    with tab4:
        st.header("👨‍💻 Análise Completa de Técnicos")
        
        # Produtividade individual
        st.subheader("📊 Produtividade Individual")
        
        df_tec_prod = df_filtered.groupby('Atribuído - Técnico').agg({
            'ID': 'count',
            'Tempo Resolução (h)': ['mean', 'median'],
        }).reset_index()
        df_tec_prod.columns = ['Técnico', 'Total Chamados', 'Tempo Médio (h)', 'Tempo Mediano (h)']
        df_tec_prod = df_tec_prod.sort_values('Total Chamados', ascending=False)
        
        col_tec1, col_tec2 = st.columns(2)
        
        with col_tec1:
            # Chamados por técnico
            fig_tec_prod = px.bar(
                df_tec_prod.head(15),
                x='Total Chamados',
                y='Técnico',
                title="📊 Chamados por Técnico (Top 15)",
                orientation='h',
                color='Total Chamados',
                color_continuous_scale='Blues',
                text='Total Chamados'
            )
            fig_tec_prod.update_traces(textposition='outside')
            st.plotly_chart(fig_tec_prod, use_container_width=True)
        
        with col_tec2:
            # Distribuição de carga (balanceamento)
            media_chamados = df_tec_prod['Total Chamados'].mean()
            df_tec_prod['Desvio da Média'] = df_tec_prod['Total Chamados'] - media_chamados
            
            fig_balance = px.bar(
                df_tec_prod.head(15),
                x='Desvio da Média',
                y='Técnico',
                title="⚖️ Balanceamento de Carga (Desvio da Média)",
                orientation='h',
                color='Desvio da Média',
                color_continuous_scale='RdYlGn_r',
                text='Desvio da Média'
            )
            fig_balance.update_traces(textposition='outside', texttemplate='%{text:.0f}')
            fig_balance.add_vline(x=0, line_dash="dash", line_color="black", annotation_text="Média")
            st.plotly_chart(fig_balance, use_container_width=True)
        
        st.markdown("---")
        
        # Especialização e Eficiência
        col_tec3, col_tec4 = st.columns(2)
        
        with col_tec3:
            st.subheader("🎯 Especialização por Técnico")
            # Categoria dominante por técnico
            df_espec = df_filtered.groupby(['Atribuído - Técnico', 'Categoria Limpa'])['ID'].count().reset_index()
            df_espec = df_espec.sort_values('ID', ascending=False).groupby('Atribuído - Técnico').first().reset_index()
            df_espec.columns = ['Técnico', 'Especialização', 'Chamados']
            df_espec = df_espec.sort_values('Chamados', ascending=False).head(10)
            
            fig_espec = px.sunburst(
                df_espec,
                path=['Técnico', 'Especialização'],
                values='Chamados',
                title="🎯 Especialização: Técnico x Categoria Dominante",
                color='Chamados',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_espec, use_container_width=True)
        
        with col_tec4:
            st.subheader("⏱️ Eficiência (Chamados/Hora)")
            df_tec_prod['Eficiência'] = df_tec_prod['Total Chamados'] / df_tec_prod['Tempo Médio (h)']
            df_ef_top = df_tec_prod.sort_values('Eficiência', ascending=False).head(10)
            
            fig_ef_tec = px.bar(
                df_ef_top,
                x='Eficiência',
                y='Técnico',
                title="🚀 Top 10 Técnicos Mais Eficientes",
                orientation='h',
                         color='Eficiência',

                color_continuous_scale='Greens',
                text='Eficiência'
            )
            fig_ef_tec.update_traces(textposition='outside', texttemplate='%{text:.2f}')
            st.plotly_chart(fig_ef_tec, use_container_width=True)
        
        st.markdown("---")
        
        # Ranking com melhor SLA
        st.subheader("🏆 Ranking de Técnicos - Melhor SLA")
        
        df_tec_sla = df_filtered[df_filtered['Status'].isin(['Fechado', 'Solucionado'])].copy()
        df_tec_sla['Dentro SLA'] = df_tec_sla['Tempo Resolução (h)'] <= 8
        
        df_sla_rank = df_tec_sla.groupby('Atribuído - Técnico').agg({
            'ID': 'count',
            'Dentro SLA': 'sum'
        }).reset_index()
        df_sla_rank['SLA (%)'] = (df_sla_rank['Dentro SLA'] / df_sla_rank['ID']) * 100
        df_sla_rank = df_sla_rank[df_sla_rank['ID'] >= 10]  # Mínimo 10 chamados
        df_sla_rank = df_sla_rank.sort_values('SLA (%)', ascending=False).head(15)
        df_sla_rank.columns = ['Técnico', 'Total Chamados', 'Dentro SLA', 'SLA (%)']
        
        fig_sla_rank = px.bar(
            df_sla_rank,
            x='SLA (%)',
            y='Técnico',
            title="🏆 Ranking de Cumprimento de SLA por Técnico (mín. 10 chamados)",
            orientation='h',
            color='SLA (%)',
            color_continuous_scale='RdYlGn',
            text='SLA (%)'
        )
        fig_sla_rank.update_traces(textposition='outside', texttemplate='%{text:.1f}%')
        fig_sla_rank.add_vline(x=80, line_dash="dash", line_color="orange", annotation_text="Meta 80%")
        st.plotly_chart(fig_sla_rank, use_container_width=True)
        
        # Tabela detalhada de técnicos
        st.dataframe(df_sla_rank, height=300, use_container_width=True)
    
    # ====================================================================
    # ABA 5: ANÁLISE DE REQUERENTES
    # ====================================================================
    with tab5:
        st.header("👥 Análise de Requerentes e Solicitantes")
        
        # Top solicitantes
        st.subheader("🏆 Top Usuários que Mais Abrem Chamados")
        col_req1, col_req2 = st.columns(2)
        
        with col_req1:
            top_requerentes = df_filtered['Requerente - Requerente'].value_counts().head(20).reset_index()
            top_requerentes.columns = ['Requerente', 'Total Chamados']
            
            fig_req = px.bar(
                top_requerentes,
                x='Total Chamados',
                y='Requerente',
                title="👥 Top 20 Solicitantes",
                orientation='h',
                color='Total Chamados',
                color_continuous_scale='Purples',
                text='Total Chamados'
            )
            fig_req.update_traces(textposition='outside')
            st.plotly_chart(fig_req, use_container_width=True)
        
        with col_req2:
            # Recorrência por usuário
            df_recor_user = df_filtered.groupby('Requerente - Requerente').agg({
                'ID': 'count',
                'Categoria Limpa': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Variado'
            }).reset_index()
            df_recor_user.columns = ['Requerente', 'Total', 'Problema Mais Comum']
            df_recor_user = df_recor_user[df_recor_user['Total'] >= 5].sort_values('Total', ascending=False).head(15)
            
            fig_recor_user = px.scatter(
                df_recor_user,
                x='Requerente',
                y='Total',
                size='Total',
                color='Problema Mais Comum',
                title="🔁 Recorrência: Usuários com Mais de 5 Chamados",
                labels={'Total': 'Número de Chamados'}
            )
            fig_recor_user.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_recor_user, use_container_width=True)
        
        st.markdown("---")
        
        # Setores problemáticos
        st.subheader("📍 Setores/Localizações com Mais Chamados")
        col_req3, col_req4 = st.columns(2)
        
        with col_req3:
            top_locais = df_filtered['Localização'].value_counts().head(15).reset_index()
            top_locais.columns = ['Localização', 'Total Chamados']
            
            fig_local = px.bar(
                top_locais,
                x='Total Chamados',
                y='Localização',
                title="🏥 Top 15 Localizações Mais Problemáticas",
                orientation='h',
                color='Total Chamados',
                color_continuous_scale='Reds',
                text='Total Chamados'
            )
            fig_local.update_traces(textposition='outside')
            st.plotly_chart(fig_local, use_container_width=True)
        
        with col_req4:
            # Relação Requerente x Localização
            df_req_local = df_filtered.groupby(['Localização', 'Requerente - Requerente'])['ID'].count().reset_index()
            df_req_local = df_req_local.sort_values('ID', ascending=False).head(30)
            
            fig_treemap = px.treemap(
                df_req_local,
                path=['Localização', 'Requerente - Requerente'],
                values='ID',
                title="🗺️ TreeMap: Localização x Requerentes",
                color='ID',
                color_continuous_scale='YlOrRd'
            )
            st.plotly_chart(fig_treemap, use_container_width=True)
    
    # ====================================================================
    # ABA 6: ANÁLISE DE LOCALIZAÇÃO
    # ====================================================================
    with tab6:
        st.header("🏥 Análise Geográfica por Localização")
        
        # Setores críticos
        st.subheader("🔴 Setores Críticos")
        
        df_local_analise = df_filtered.groupby('Localização').agg({
            'ID': 'count',
            'Tempo Resolução (h)': 'mean',
            'Categoria Limpa': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Variado'
        }).reset_index()
        df_local_analise.columns = ['Localização', 'Total Chamados', 'Tempo Médio (h)', 'Problema Principal']
        df_local_analise = df_local_analise.sort_values('Total Chamados', ascending=False)
        
        col_loc1, col_loc2 = st.columns(2)
        
        with col_loc1:
            # Top setores
            fig_setor = px.bar(
                df_local_analise.head(20),
                x='Total Chamados',
                y='Localização',
                title="🏥 Top 20 Setores com Mais Chamados",
                orientation='h',
                color='Total Chamados',
                color_continuous_scale='Reds',
                text='Total Chamados'
            )
            fig_setor.update_traces(textposition='outside')
            st.plotly_chart(fig_setor, use_container_width=True)
        
        with col_loc2:
            # Mapa de calor: Localização x Categoria
            top_15_locais = df_local_analise.head(15)['Localização'].tolist()
            top_10_cat = df_filtered['Categoria Limpa'].value_counts().head(10).index.tolist()
            
            df_heat_local = df_filtered[
                (df_filtered['Localização'].isin(top_15_locais)) & 
                (df_filtered['Categoria Limpa'].isin(top_10_cat))
            ]
            
            heat_local_cat = df_heat_local.pivot_table(
                index='Localização',
                columns='Categoria Limpa',
                values='ID',
                aggfunc='count',
                fill_value=0
            )
            
            fig_heat_loc = px.imshow(
                heat_local_cat,
                title="🗺️ Mapa de Calor: Localização x Categoria",
                labels=dict(x="Categoria", y="Localização", color="Chamados"),
                color_continuous_scale='YlOrRd',
                aspect="auto"
            )
            st.plotly_chart(fig_heat_loc, use_container_width=True)
        
        st.markdown("---")
        
        # Áreas de risco
        st.subheader("🔴 Áreas de Risco (Mais Incidentes)")
        
        # Scatter: Total x Tempo Médio
        fig_risco = px.scatter(
            df_local_analise.head(30),
            x='Total Chamados',
            y='Tempo Médio (h)',
            size='Total Chamados',
            color='Tempo Médio (h)',
            hover_data=['Localização', 'Problema Principal'],
            title="🎯 Áreas de Risco: Volume x Tempo de Resolução",
            labels={'Total Chamados': 'Volume de Chamados', 'Tempo Médio (h)': 'Tempo Médio (horas)'},
            color_continuous_scale='Reds',
            text='Localização'
        )
        st.plotly_chart(fig_risco, use_container_width=True)

    # Tabela detalhada

        st.dataframe(df_local_analise.head(30), height=400, use_container_width=True)
    
    # ====================================================================
    # ABA 7: ANÁLISE DE PRIORIDADE
    # ====================================================================
    with tab7:
        st.header("⚡ Análise por Prioridade")
        
        # Distribuição de prioridades
        st.subheader("📊 Distribuição de Prioridades")
        col_prior1, col_prior2 = st.columns(2)
        
        with col_prior1:
            prior_counts = df_filtered['Prioridade'].value_counts().reset_index()
            prior_counts.columns = ['Prioridade', 'Quantidade']
            
            fig_prior = px.pie(
                prior_counts,
                values='Quantidade',
                names='Prioridade',
                title="🥧 Distribuição por Prioridade",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4
            )
            fig_prior.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_prior, use_container_width=True)
        
        with col_prior2:
            # Tempo de resposta por prioridade
            df_prior_tempo = df_filtered.groupby('Prioridade')['Tempo Resolução (h)'].mean().reset_index()
            df_prior_tempo.columns = ['Prioridade', 'Tempo Médio (h)']
            
            fig_prior_tempo = px.bar(
                df_prior_tempo,
                x='Prioridade',
                y='Tempo Médio (h)',
                title="⏰ Tempo Médio de Resposta por Prioridade",
                color='Tempo Médio (h)',
                color_continuous_scale='Oranges',
                text='Tempo Médio (h)'
            )
            fig_prior_tempo.update_traces(textposition='outside', texttemplate='%{text:.1f}h')
            st.plotly_chart(fig_prior_tempo, use_container_width=True)
        
        st.markdown("---")
        
        # Violações de SLA por prioridade
        st.subheader("❌ Violações de SLA por Prioridade")
        
        df_viol = df_filtered[df_filtered['Status'].isin(['Fechado', 'Solucionado'])].copy()
        df_viol['Violação SLA'] = df_viol['Tempo Resolução (h)'] > 8
        
        df_viol_prior = df_viol.groupby('Prioridade').agg({
            'ID': 'count',
            'Violação SLA': 'sum'
        }).reset_index()
        df_viol_prior['% Violação'] = (df_viol_prior['Violação SLA'] / df_viol_prior['ID']) * 100
        df_viol_prior.columns = ['Prioridade', 'Total', 'Violações', '% Violação']
        
        fig_viol = px.bar(
            df_viol_prior,
            x='Prioridade',
            y=['Total', 'Violações'],
            title="📊 Violações de SLA por Prioridade",
            barmode='group',
            color_discrete_sequence=['#28a745', '#dc3545']
        )
        st.plotly_chart(fig_viol, use_container_width=True)
        
        st.dataframe(df_viol_prior, use_container_width=True)
    
    # ====================================================================
    # ABA 8: ANÁLISE DE STATUS
    # ====================================================================
    with tab8:
        st.header("📈 Análise de Status e Fluxo")
        
        # Funil de conversão
        st.subheader("📊 Funil de Conversão")
        
        status_flow = df_filtered['Status'].value_counts().reset_index()
        status_flow.columns = ['Status', 'Quantidade']
        
        col_stat1, col_stat2 = st.columns(2)
        
        with col_stat1:
            # Funil
            fig_funil = px.funnel(
                status_flow,
                x='Quantidade',
                y='Status',
                title="📉 Funil: Status dos Chamados",
                color='Status',
                color_discrete_map={'Fechado': '#28a745', 'Solucionado': '#17a2b8', 'Pendente': '#ffc107'}
            )
            st.plotly_chart(fig_funil, use_container_width=True)
        
        with col_stat2:
            # Evolução temporal do status
            df_status_tempo = df_filtered.groupby([df_filtered['Data Abertura Datetime'].dt.to_period('M'), 'Status'])['ID'].count().reset_index()
            df_status_tempo['Período'] = df_status_tempo['Data Abertura Datetime'].astype(str)
            
            fig_status_evolucao = px.line(
                df_status_tempo,
                x='Período',
                y='ID',
                color='Status',
                title="📈 Evolução dos Status ao Longo do Tempo",
                labels={'ID': 'Quantidade'},
                markers=True
            )
            fig_status_evolucao.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_status_evolucao, use_container_width=True)
        
        st.markdown("---")
        
        # Backlog
        st.subheader("⏳ Análise de Backlog (Chamados Pendentes)")
        
        df_pendentes = df_filtered[df_filtered['Status'] == 'Pendente'].copy()
        
        if len(df_pendentes) > 0:
            col_back1, col_back2 = st.columns(2)
            
            with col_back1:
                st.metric("📋 Total de Pendentes", len(df_pendentes))
                
                # Tempo em aberto
                hoje = pd.Timestamp.now()
                df_pendentes['Dias em Aberto'] = (hoje - df_pendentes['Data Abertura Datetime']).dt.days
                
                fig_backlog = px.histogram(
                    df_pendentes,
                    x='Dias em Aberto',
                    nbins=20,
                    title="⏳ Distribuição do Backlog (Dias em Aberto)",
                    color_discrete_sequence=['#ffc107']
                )
                st.plotly_chart(fig_backlog, use_container_width=True)
            
            with col_back2:
                # Backlog por categoria
                back_cat = df_pendentes['Categoria Limpa'].value_counts().head(10).reset_index()
                back_cat.columns = ['Categoria', 'Pendentes']
                
                fig_back_cat = px.bar(
                    back_cat,
                    x='Pendentes',
                    y='Categoria',
                    title="📊 Backlog por Categoria",
                    orientation='h',
                    color='Pendentes',
                    color_continuous_scale='Oranges',
                    text='Pendentes'
                )
                fig_back_cat.update_traces(textposition='outside')
                st.plotly_chart(fig_back_cat, use_container_width=True)
            
            # Chamados antigos pendentes
            df_antigos = df_pendentes.nlargest(15, 'Dias em Aberto')[['ID', 'Título', 'Requerente - Requerente', 'Localização', 'Dias em Aberto']]
            st.subheader("🚨 Chamados Mais Antigos Pendentes")
            st.dataframe(df_antigos, use_container_width=True)
        else:
            st.success("✅ Não há chamados pendentes no momento!")
    
    # ====================================================================
    # ABA 9: ANÁLISE PREDITIVA
    # ====================================================================
    with tab9:
        st.header("🔮 Análise Preditiva e Tendências")
        
        # Previsão de demanda
        st.subheader("📈 Previsão de Demanda")
        
        # Série temporal mensal
        df_serie = df_filtered.groupby(df_filtered['Data Abertura Datetime'].dt.to_period('M'))['ID'].count().reset_index()
        df_serie['Mês'] = df_serie['Data Abertura Datetime'].astype(str)
        df_serie['Ordem'] = range(len(df_serie))
        
        col_pred1, col_pred2 = st.columns(2)
        
        with col_pred1:
            # Tendência linear
            if len(df_serie) >= 3:
                z = np.polyfit(df_serie['Ordem'], df_serie['ID'], 1)
                p = np.poly1d(z)
                df_serie['Tendência'] = p(df_serie['Ordem'])
                
                # Projeção para próximos 3 meses
                projecao_meses = 3
                ordem_futura = range(len(df_serie), len(df_serie) + projecao_meses)
                chamados_previstos = p(list(ordem_futura))
                
                fig_tend = go.Figure()
                fig_tend.add_trace(go.Scatter(x=df_serie['Mês'], y=df_serie['ID'], 
                                             mode='lines+markers', name='Real',
                                             line=dict(color='#007bff', width=3)))
                fig_tend.add_trace(go.Scatter(x=df_serie['Mês'], y=df_serie['Tendência'],
                                             mode='lines', name='Tendência',
                                             line=dict(color='red', dash='dash')))
                fig_tend.update_layout(title="📈 Tendência e Histórico de Chamados",
                                      xaxis_title="Período", yaxis_title="Chamados")
                st.plotly_chart(fig_tend, use_container_width=True)
                
                # Métricas de previsão
                media_projecao = np.mean(chamados_previstos)
                st.metric("📊 Média Prevista (próximos 3 meses)", f"{media_projecao:.0f} chamados/mês")
                
                crescimento = ((df_serie['ID'].iloc[-1] - df_serie['ID'].iloc[0]) / df_serie['ID'].iloc[0]) * 100
                st.metric("📈 Crescimento Total", f"{crescimento:.1f}%")
        
        with col_pred2:
            # Necessidade de recursos
            media_chamados_mes = df_serie['ID'].mean()
            media_tempo_resolucao = df_filtered['Tempo Resolução (h)'].mean()
            
            # Cálculo de técnicos necessários (assumindo 160h/mês por técnico)
            if pd.isna(media_chamados_mes) or pd.isna(media_tempo_resolucao):
                horas_totais_mes = np.nan
                tecnicos_necessarios = np.nan
            else:
                horas_totais_mes = media_chamados_mes * media_tempo_resolucao
                tecnicos_necessarios = np.ceil(horas_totais_mes / 160)
            tecnicos_atuais = df_filtered['Atribuído - Técnico'].nunique()
            
            st.subheader("🎯 Necessidade de Recursos")
            st.metric("👥 Técnicos Atuais", f"{tecnicos_atuais}")
            if pd.isna(tecnicos_necessarios):
                st.metric("📊 Técnicos Sugeridos", "N/A")
                st.metric("⏱️ Horas/Mês Estimadas", "N/A")
                st.metric("📞 Média Chamados/Mês", f"{media_chamados_mes:.0f}" if not pd.isna(media_chamados_mes) else "N/A")
            else:
                st.metric("📊 Técnicos Sugeridos", f"{int(tecnicos_necessarios)}", 
                         delta=f"{int(tecnicos_necessarios - tecnicos_atuais)}")
                st.metric("⏱️ Horas/Mês Estimadas", f"{horas_totais_mes:.0f}h")
                st.metric("📞 Média Chamados/Mês", f"{media_chamados_mes:.0f}")
            
            # Gráfico de capacidade
            if not pd.isna(tecnicos_necessarios) and not pd.isna(media_chamados_mes):
                fig_capacidade = go.Figure()
                fig_capacidade.add_trace(go.Bar(
                    x=['Capacidade Atual', 'Demanda Real', 'Capacidade Ideal'],
                    y=[tecnicos_atuais * 20, media_chamados_mes, tecnicos_necessarios * 20],
                    marker_color=['#28a745', '#ffc107', '#007bff'],
                    text=[f"{tecnicos_atuais * 20:.0f}", f"{media_chamados_mes:.0f}", f"{tecnicos_necessarios * 20:.0f}"],
                    textposition='outside'
                ))
                fig_capacidade.update_layout(
                    title="📊 Análise de Capacidade (Chamados/Mês)",
                    yaxis_title="Chamados"
                )
                st.plotly_chart(fig_capacidade, use_container_width=True)
            else:
                st.info("🔎 Sem dados suficientes para o gráfico de capacidade.")
        
        st.markdown("---")
        
        # Tendências futuras por categoria
        st.subheader("📉 Tendências Futuras por Categoria")
        
        top_5_cat = df_filtered['Categoria Limpa'].value_counts().head(5).index.tolist()
        df_cat_tempo = df_filtered[df_filtered['Categoria Limpa'].isin(top_5_cat)]
        
        df_cat_serie = df_cat_tempo.groupby([
            df_cat_tempo['Data Abertura Datetime'].dt.to_period('M'),
            'Categoria Limpa'
        ])['ID'].count().reset_index()
        df_cat_serie['Período'] = df_cat_serie['Data Abertura Datetime'].astype(str)
        
        fig_cat_tend = px.line(
            df_cat_serie,
            x='Período',
            y='ID',
            color='Categoria Limpa',
            title="📈 Evolução das Top 5 Categorias",
            labels={'ID': 'Número de Chamados'},
            markers=True
        )
        fig_cat_tend.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_cat_tend, use_container_width=True)
    
    # ====================================================================
    # ABA 10: ANÁLISE DE QUALIDADE
    # ====================================================================
    with tab10:
        st.header("✅ Análise de Qualidade dos Chamados")
        
        # Taxa de primeira resolução
        st.subheader("🎯 Taxa de Primeira Resolução")
        
        col_qual1, col_qual2 = st.columns(2)
        
        with col_qual1:
            # Estimativa de retrabalho (mesmo usuário, mesma categoria, intervalo curto)
            df_retrabalho = df_filtered.sort_values('Data Abertura Datetime')
            df_retrabalho['Possível Retrabalho'] = (
                df_retrabalho.duplicated(subset=['Requerente - Requerente', 'Categoria Limpa'], keep=False)
            )
            
            retrabalho_count = df_retrabalho['Possível Retrabalho'].sum()
            taxa_primeira_resolucao = ((len(df_filtered) - retrabalho_count) / len(df_filtered)) * 100
            
            st.metric("✅ Taxa de Primeira Resolução", f"{taxa_primeira_resolucao:.1f}%")
            st.metric("🔄 Possível Retrabalho", f"{retrabalho_count} chamados")
            
            # Gráfico
            fig_retrab = go.Figure(data=[
                go.Pie(
                    labels=['Primeira Resolução', 'Possível Retrabalho'],
                    values=[len(df_filtered) - retrabalho_count, retrabalho_count],
                    marker=dict(colors=['#28a745', '#dc3545']),
                    hole=0.4
                )
            ])
            fig_retrab.update_layout(title="🎯 Taxa de Primeira Resolução")
            st.plotly_chart(fig_retrab, use_container_width=True)
        
        with col_qual2:
            # Qualidade da descrição
            df_filtered['Tamanho Título'] = df_filtered['Título'].str.len()
            df_filtered['Qualidade Desc'] = df_filtered['Tamanho Título'].apply(
                lambda x: 'Boa (>20 chars)' if x > 20 else 'Ruim (≤20 chars)' if pd.notna(x) else 'N/A'
            )
            
            qual_desc = df_filtered['Qualidade Desc'].value_counts().reset_index()
            qual_desc.columns = ['Qualidade', 'Quantidade']
            
            fig_qual = px.pie(
                qual_desc,
                values='Quantidade',
                names='Qualidade',
                title="✍️ Qualidade das Descrições",
                color_discrete_sequence=['#28a745', '#dc3545', '#6c757d'],
                hole=0.4
            )
            fig_qual.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_qual, use_container_width=True)
            
            pct_boa = (qual_desc[qual_desc['Qualidade'] == 'Boa (>20 chars)']['Quantidade'].sum() / len(df_filtered)) * 100
            st.metric("✅ Descrições Detalhadas", f"{pct_boa:.1f}%")
        
        st.markdown("---")
        
        # Chamados duplicados
        st.subheader("🔄 Análise de Chamados Duplicados")
        
        # Duplicados: mesmo título, mesma localização, período próximo
        df_dup = df_filtered.groupby(['Título', 'Localização']).agg({
            'ID': 'count',
            'Categoria Limpa': 'first'
        }).reset_index()
        df_dup = df_dup[df_dup['ID'] > 1].sort_values('ID', ascending=False).head(20)
        df_dup.columns = ['Título', 'Localização', 'Repetições', 'Categoria']
        
        if len(df_dup) > 0:
            fig_dup = px.bar(
                df_dup,
                x='Repetições',
                y='Título',
                title="🔄 Top 20 Problemas Duplicados (Mesmo Título + Local)",
                orientation='h',
                color='Repetições',
                color_continuous_scale='Reds',
                text='Repetições',
                hover_data=['Localização', 'Categoria']
            )
            fig_dup.update_traces(textposition='outside')
            st.plotly_chart(fig_dup, use_container_width=True)
            
            st.dataframe(df_dup, use_container_width=True)
        else:
            st.success("✅ Nenhum chamado duplicado identificado!")
    
    # ====================================================================
    # ABA 11: MÉTRICAS ESPECÍFICAS DO SISTEMA
    # ====================================================================
    with tab11:
        st.header("🖨️ Métricas Específicas por Tipo de Problema")
        
        # Incidentes de impressora
        st.subheader("🖨️ Análise de Incidentes de Impressora")
        col_esp1, col_esp2 = st.columns(2)
        
        with col_esp1:
            df_impressora = df_filtered[df_filtered['Categoria Limpa'].str.contains('IMPRESSORA', case=False, na=False)]
            
            if len(df_impressora) > 0:
                local_impressora = df_impressora['Localização'].value_counts().head(15).reset_index()
                local_impressora.columns = ['Localização', 'Incidentes']
                
                fig_imp = px.bar(
                    local_impressora,
                    x='Incidentes',
                    y='Localização',
                    title="🖨️ Top 15 Locais com Problemas de Impressora",
                    orientation='h',
                    color='Incidentes',
                    color_continuous_scale='Reds',
                    text='Incidentes'
                )
                fig_imp.update_traces(textposition='outside')
                st.plotly_chart(fig_imp, use_container_width=True)
                
                st.metric("Total Incidentes", len(df_impressora))
                st.metric("% do Total", f"{(len(df_impressora)/len(df_filtered)*100):.1f}%")
        
        with col_esp2:
            # Problemas de hardware
            df_hardware = df_filtered[df_filtered['Categoria Limpa'].str.contains('COMPUTADOR|TECLADO|MOUSE|MONITOR', case=False, na=False)]
            
            if len(df_hardware) > 0:
                hw_cat = df_hardware['Categoria Limpa'].value_counts().head(10).reset_index()
                hw_cat.columns = ['Tipo Hardware', 'Quantidade']
                
                fig_hw = px.pie(
                    hw_cat,
                    values='Quantidade',
                    names='Tipo Hardware',
                    title="💻 Distribuição de Problemas de Hardware",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_hw.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_hw, use_container_width=True)
                
                st.metric("Total Hardware", len(df_hardware))
                st.metric("% do Total", f"{(len(df_hardware)/len(df_filtered)*100):.1f}%")
        
        st.markdown("---")
        
        # Reset de senhas SPDATA
        st.subheader("🔐 Análise de Reset de Senhas")
        col_esp3, col_esp4 = st.columns(2)
        
        with col_esp3:
            df_senha = df_filtered[df_filtered['Categoria Limpa'].str.contains('RESET|SENHA|SPDATA', case=False, na=False)]
            
            if len(df_senha) > 0:
                # Volume de resets por mês
                df_senha_mes = df_senha.groupby(df_senha['Data Abertura Datetime'].dt.to_period('M'))['ID'].count().reset_index()
                df_senha_mes['Mês'] = df_senha_mes['Data Abertura Datetime'].astype(str)
                
                fig_senha = px.bar(
                    df_senha_mes,
                    x='Mês',
                    y='ID',
                    title="🔐 Volume de Reset de Senhas por Mês",
                    color='ID',
                    color_continuous_scale='Purples',
                    text='ID'
                )
                fig_senha.update_traces(textposition='outside')
                fig_senha.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_senha, use_container_width=True)
                
                st.metric("Total Resets", len(df_senha))
                st.metric("% do Total", f"{(len(df_senha)/len(df_filtered)*100):.1f}%")
                st.metric("Média/Mês", f"{len(df_senha)/len(df_serie):.0f}")
        
        with col_esp4:
            # Suprimentos (TONNER)
            df_tonner = df_filtered[df_filtered['Categoria Limpa'].str.contains('TONNER|TONER', case=False, na=False)]
            
            if len(df_tonner) > 0:
                tonner_local = df_tonner['Localização'].value_counts().head(10).reset_index()
                tonner_local.columns = ['Localização', 'Solicitações']
                
                fig_tonner = px.bar(
                    tonner_local,
                    x='Solicitações',
                    y='Localização',
                    title="📦 Top 10 Setores - Solicitações de Tonner",
                    orientation='h',
                    color='Solicitações',
                    color_continuous_scale='Oranges',
                    text='Solicitações'
                )
                fig_tonner.update_traces(textposition='outside')
                st.plotly_chart(fig_tonner, use_container_width=True)
                
                st.metric("Total Tonners", len(df_tonner))
                st.metric("% do Total", f"{(len(df_tonner)/len(df_filtered)*100):.1f}%")
                st.metric("Média/Mês", f"{len(df_tonner)/len(df_serie):.0f}")
        
        st.markdown("---")
        
        # Resumo geral de tipos
        st.subheader("📊 Resumo Geral por Tipo de Problema")
        
        tipos = {
            'Impressora': df_filtered[df_filtered['Categoria Limpa'].str.contains('IMPRESSORA', case=False, na=False)],
            'SPDATA': df_filtered[df_filtered['Categoria Limpa'].str.contains('SPDATA', case=False, na=False)],
            'Tonner': df_filtered[df_filtered['Categoria Limpa'].str.contains('TONNER|TONER', case=False, na=False)],
            'Computador': df_filtered[df_filtered['Categoria Limpa'].str.contains('COMPUTADOR', case=False, na=False)],
            'Hardware': df_filtered[df_filtered['Categoria Limpa'].str.contains('TECLADO|MOUSE|MONITOR', case=False, na=False)],
            'Rede': df_filtered[df_filtered['Categoria Limpa'].str.contains('REDE|INTERNET', case=False, na=False)]
        }
        
        resumo_tipos = pd.DataFrame([
            {
                'Tipo': tipo,
                'Quantidade': len(df_tipo),
                '% Total': f"{(len(df_tipo)/len(df_filtered)*100):.1f}%",
                'Tempo Médio (h)': f"{df_tipo['Tempo Resolução (h)'].mean():.1f}" if len(df_tipo) > 0 else "N/A"
            }
            for tipo, df_tipo in tipos.items()
        ])
        resumo_tipos = resumo_tipos.sort_values('Quantidade', ascending=False)
        
        fig_resumo = px.bar(
            resumo_tipos,
            x='Quantidade',
            y='Tipo',
            title="📊 Resumo por Tipo de Problema",
            orientation='h',
            color='Quantidade',
            color_continuous_scale='Viridis',
            text='Quantidade'
        )
        fig_resumo.update_traces(textposition='outside')
        st.plotly_chart(fig_resumo, use_container_width=True)
        
        st.dataframe(resumo_tipos, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela geral de dados
    st.subheader("📋 Dados Detalhados dos Chamados")
    if not df_filtered.empty:

        # Selecionar colunas relevantes
        colunas_exibicao = ['ID', 'Título', 'Status', 'Prioridade', 'Categoria Limpa', 

                           'Atribuído - Técnico', 'Data Abertura', 'Hora Abertura', 
                           'Data Atualização', 'Tempo Resolução (h)', 'Localização']
        colunas_disponiveis = [col for col in colunas_exibicao if col in df_filtered.columns]
        

        df_exibicao = df_filtered[colunas_disponiveis].copy()
        if 'Data Abertura Datetime' in df_filtered.columns:
            df_exibicao = df_exibicao.sort_values(by=[col for col in df_exibicao.columns if 'Data' in col][0] if any('Data' in col for col in df_exibicao.columns) else df_exibicao.columns[0], ascending=False)
        
        st.dataframe(df_exibicao.head(100), height=400, use_container_width=True)
        st.caption(f"Exibindo os 100 chamados mais recentes de {len(df_exibicao)} total")
    else:
        st.info("Nenhum chamado encontrado com os filtros aplicados.")

# Rodapé
st.markdown("---")
st.markdown("**Dashboard desenvolvido Pedro Henrique (Analista de Sistema Pleno)** | Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M"))

st.markdown("**Fonte:** Sistema de Chamados Técnicos HMSI")