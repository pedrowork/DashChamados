# 📊 Dashboard de Chamados Técnicos - HMSI

Dashboard interativo para análise de chamados técnicos desenvolvido com Python, Streamlit e Plotly.

## 🚀 **Funcionalidades**

- **Métricas Dinâmicas**: Total de chamados, tempo médio, SLA, distribuição por técnico
- **Gráficos Interativos**: Clique nos gráficos para filtrar dados automaticamente
- **Filtros Avançados**: Por período, técnico, status, prioridade e categoria
- **Visualizações**: Gráficos de barras, pizza e análise temporal
- **Responsivo**: Interface adaptável para diferentes dispositivos

## 📦 **Instalação Local**

### Pré-requisitos
- Python 3.8+
- pip

### Passos
1. **Clone o repositório**
   ```bash
   git clone <seu-repositorio>
   cd dashChamados
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute o dashboard**
   ```bash
   streamlit run dashboard_chamados.py
   ```

## 🌐 **Deploy em Produção**

### Streamlit Cloud
1. Faça push para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Deploy automático

### Heroku
1. Instale Heroku CLI
2. Crie `Procfile` e `runtime.txt`
3. Deploy via Git

## 📊 **Estrutura dos Dados**

O dashboard espera um arquivo Excel (`s.xlsx`) com as seguintes colunas:
- ID, Título, Status, Prioridade
- Categoria, Atribuído - Técnico
- Data de abertura, Última atualização
- Tempo para solução + Progresso

## 🛠️ **Tecnologias**

- **Frontend**: Streamlit
- **Gráficos**: Plotly
- **Dados**: Pandas, NumPy
- **Interatividade**: streamlit-plotly-events

## 📝 **Licença**

Projeto desenvolvido para HMSI - Sistema de Chamados Técnicos

## 🤝 **Suporte**

Para dúvidas ou suporte, entre em contato com a equipe de desenvolvimento.
