# IA no Piauí — Monitor de Notícias 

Painel simples para **monitorar menções** a “Inteligência Artificial” no Piauí a partir do **RSS do Google Notícias**.  
Inclui **limpeza de texto**, **análise de sentimento baseada em regras**, **temas recorrentes** e **visualizações** (barras, donut, nuvem), além de **tabela com filtros** e **exportação CSV**.

## Funcionalidades

**Coleta** via RSS do Google Notícias (consulta customizável).<br><br>
**Busca aprimorada**:<br>
Presets de 1 clique (IA Piauí / SIA Piauí / IA Governo).<br>
Filtros avançados: obrigatórias, exclusões e `site:dominio.com`.<br><br>
**Processamento**:<br>
Limpeza HTML → texto limpo.<br>
Deduplicação por `title`/`link`.<br>
Extração de **fonte** (domínio) e **data de publicação**.<br>
**Classificação de sentimento** por regras simples.<br><br>
**Dashboard (abas)**:<br><br>
**Visão Geral**: KPIs, badges das principais fontes, cards das últimas notícias.<br><br>
**Gráficos**: barras e donut (Plotly).<br><br>
**Tabela**: filtros por termo, fonte, sentimento e intervalo de datas + export CSV.<br><br>
**Nuvem & Temas**: wordcloud + top palavras/bigramas.<br><br>
**Cache** da coleta (menos chamadas ao RSS).<br>

## Arquitetura e pastas

.
├── app.py                     
├── requirements.txt           
├── src/
│   ├── fetch.py               
│   ├── clean.py               
│   ├── sentiment.py           
│   └── utils.py               

          

## Requisitos

**Python 3.10+** (recomendado 3.11/3.12/3.13)
macOS/Linux/Windows
Pip e venv

## Como rodar localmente

1. Clone (ou baixe) o repositório.

2. Crie e ative o ambiente virtual: 
```bash



python3 -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

3. Instale as dependências:

python -m pip install --upgrade pip
pip install -r requirements.txt

4.	Rode o app:

python -m streamlit run app.py

5. Acesse no navegador o endereço mostrado (geralmente http://localhost:8501).

Customizações

1. Palavras de sentimento

Edite src/sentiment.py para mudar listas de palavras positivas/negativas.


2. Presets de busca

Edite a seção de presets no app.py.

Autor: Bruno Ibiapina
