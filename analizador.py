import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# --- MOTORES EXTERNOS ---
try:
    from docx import Document
except ImportError:
    Document = None

try:
    from st_keyup import st_keyup
except ImportError:
    st_keyup = None

try:
    from streamlit_echarts import st_echarts
except ImportError:
    st_echarts = None

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador JNL", page_icon="🛡️", layout="wide")

# --- DESIGN PREMIUM SAAS (Inspirado no AgentOps) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
    }
    
    /* Fundo da Tela (Cinza/Azulado muito suave) */
    .main { 
        background-color: #F7F9FC; 
    }
    
    /* Barra Lateral Branca e Limpa */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF; 
        border-right: 1px solid #E2E8F0; 
    }
    
    /* Cartões Flutuantes (SaaS Style) */
    .stMetric, .echarts-container, [data-testid="stDataFrame"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        padding: 15px !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stMetric:hover {
        box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-2px);
    }

    /* Caixas de Texto (Pesquisa) */
    .stTextInput > div > div > input {
        border-radius: 10px; 
        border: 1px solid #CBD5E1; 
        padding: 12px 16px;
        background-color: #FFFFFF;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
    }
    .stTextInput > div > div > input:focus {
        border-color: #0F172A; 
        box-shadow: 0 0 0 1px #0F172A;
    }
    
    /* Abas Modernas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 15px;
        border-radius: 8px 8px 0px 0px;
    }
    
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ ANALIZADOR JNL")
st.write("Análise inteligente e controle operacional.")

# --- MOTOR DE PESQUISA INTELIGENTE (KEYUP) ---
def campo_pesquisa(label, placeholder, key):
    if st_keyup is not None:
        return st_keyup(label, placeholder=placeholder, key=key)
    else:
        return st.text_input(label, placeholder=placeholder, key=key)

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configurações")
arquivos_enviados = st.sidebar.file_uploader("Arraste seus arquivos aqui", type=["xlsx", "xls", "xlsm", "docx", "txt"], accept_multiple_files=True)

st.markdown("---")

def formatar_moeda(valor):
    try:
        if pd.isna(valor): return "R$ 0,00"
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def formatar_orcamento(valor):
    if pd.isna(valor) or str(valor).strip() == "" or str(valor).strip().upper() in ["S/N", "NAN", "NONE"]:
        return "S/N"
    try:
        return str(int(float(valor)))
    except (ValueError, TypeError):
        return str(valor).strip()

# ==========================================
# MOTOR DE AGENDA (ICS)
# ==========================================
def criar_lembrete_item(data_venc, cliente, valor, orc):
    if pd.isnull(data_venc): return None
    dtstart = data_venc.strftime("%Y%m%d") + "T100000"
    dtend = data_venc.strftime("%Y%m%d") + "T103000"
    cliente_limpo = str(cliente).replace("\n", " ")
    valor_f = formatar_moeda(valor)
    orc_f = formatar_orcamento(orc)
    uid = f"{uuid.uuid4()}@jnl.com"
    
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//JNL//Lembrete Financeiro//PT\n"
        "BEGIN:VEVENT\n"
        f"UID:{uid}\n"
        f"DTSTART:{dtstart}\n"
        f"DTEND:{dtend}\n"
        f"SUMMARY:⚠️ COBRAR: {cliente_limpo} ({valor_f})\n"
        f"DESCRIPTION:Lembrete JNL\\nOrçamento: {orc_f}\\nValor: {valor_f}\n"
        "BEGIN:VALARM\nTRIGGER:-P1D\nACTION:DISPLAY\nDESCRIPTION:Vence Amanhã\nEND:VALARM\n"
        "END:VEVENT\nEND:VCALENDAR"
    )
    return ics

def criar_lembrete_estoque(item, qtd, minimo_exigido):
    hoje = datetime.now()
    dtstart = hoje.strftime("%Y%m%d") + "T090000"
    dtend = hoje.strftime("%Y%m%d") + "T093000"
    item_limpo = str(item).replace("\n", " ")
    uid = f"{uuid.uuid4()}@jnl.com"
    
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//JNL//Lembrete Estoque//PT\n"
        "BEGIN:VEVENT\n"
        f"UID:{uid}\n"
        f"DTSTART:{dtstart}\n"
        f"DTEND:{dtend}\n"
        f"SUMMARY:📦 REPOR ESTOQUE: {item_limpo}\n"
        f"DESCRIPTION:Alerta JNL\\nO item '{item_limpo}' atingiu nível crítico.\\nSaldo Atual: {qtd} unidades\\nMínimo Exigido: {minimo_exigido} unidades\\nNecessário solicitar reposição imediatamente.\n"
        "BEGIN:VALARM\nTRIGGER:-PT5M\nACTION:DISPLAY\nDESCRIPTION:Reposição de Estoque\nEND:VALARM\n"
        "END:VEVENT\nEND:VCALENDAR"
    )
    return ics

# ==========================================
# PROCESSAMENTO DE ARQUIVOS
# ==========================================
if arquivos_enviados:
    for arquivo in arquivos_enviados:
        extensao = arquivo.name.split('.')[-1].lower()
        
        with st.expander(f"📄 ARQUIVO: {arquivo.name.upper()}", expanded=True):
            
            if extensao in ['xlsx', 'xls', 'xlsm']:
                try:
                    df = pd.read_excel(arquivo)
                    
                    if any("Unnamed" in str(c) for c in df.columns):
                        for idx, row in df.head(15).iterrows():
                            linha_texto = " ".join([str(x).lower() for x in row.values])
                            if any(k in linha_texto for k in ['valor', 'r$', 'data', 'venc', 'cliente', 'item', 'qtd', 'estoque', 'marca', 'prateleira']):
                                nomes_limpos = []
                                for i, c in enumerate(row.values):
                                    nome = str(c).strip() if pd.notna(c) and str(c).strip() != "" else f"vazio_{i}"
                                    if nome in nomes_limpos: nome = f"{nome}_{i}"
                                    nomes_limpos.append(nome)
                                df.columns = nomes_limpos
                                df = df.iloc[idx+1:].reset_index(drop=True)
                                break
                    
                    df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                    cols_limpas = {str(c).lower().strip(): c for c in df.columns}

                    is_financeiro = any(k in str(cols_limpas.keys()) for k in ['vencimento', 'data']) and any(k in str(cols_limpas.keys()) for k in ['valor', 'r$'])

                    # --- FLUXO 1: FINANCEIRO ---
                    if is_financeiro:
                        st.info("🎯 **Objetivo Detectado:** Controle Financeiro.")
                        col_data = next((v for k, v in cols_limpas.items() if 'vencimento' in k or 'data' in k), None)
                        col_valor = next((v for k, v in cols_limpas.items() if 'valor' in k or 'r$' in k), None)
                        col_cliente = next((v for k, v in cols_limpas.items() if 'cliente' in k or 'nome' in k or 'empresa' in k), "S/N")
                        col_orc = next((v for k, v in cols_limpas.items() if 'orc' in k or 'orç' in k or 'pedido' in k or 'doc' in k), None)
                        col_status = next((v for k, v in cols_limpas.items() if 'obs' in k or 'status' in k or 'situa' in k), None)
                        
                        df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
                        
                        mask_pago = df[col_status].astype(str).str.lower().str.contains('pago') if col_status else df[df.columns[-1]].astype(str).str.lower().str.contains('pago')
                        df_pendente = df[~mask_pago].dropna(subset=[col_data])
                        
                        hoje = pd.to_datetime('today').normalize()
                        df_a_vencer = df_pendente[df_pendente[col_data] >= hoje].sort_values(by=col_data)

                        tab_venc, tab_dados = st.tabs(["📅 Resumo Financeiro", "📋 Planilha Completa"])
                        with tab_venc:
                            st.markdown(f"**Valor total em aberto: {formatar_moeda(df_pendente[col_valor].sum())}**")
                            for _, linha in df_a_vencer.head(10).iterrows():
                                c1, c2 = st.columns([0.85, 0.15])
                                c1.write(f"📌 **{linha.get(col_cliente, 'S/N')}** | {formatar_moeda(linha[col_valor])} | Venc: {linha[col_data].strftime('%d/%m/%Y')}")
                                conteudo_ics = criar_lembrete_item(linha[col_data], linha.get(col_cliente, 'S/N'), linha[col_valor], linha.get(col_orc))
                                c2.download_button("🔔 Me lembre", data=conteudo_ics, file_name="Lembrete.ics", key=str(uuid.uuid4()))
                        
                        with tab_dados:
                            busca_fin = campo_pesquisa("🔍 Busca Dinâmica", "Digite cliente, nota ou valor para filtrar a tabela instantaneamente...", key=f"bf_{arquivo.name}")
                            df_view = df.copy()
                            if busca_fin:
                                mask_fin = df_view.astype(str).apply(lambda x: x.str.contains(busca_fin, case=False, na=False)).any(axis=1)
                                df_view = df_view[mask_fin]
                            st.dataframe(df_view, use_container_width=True)

                    # --- FLUXO 2: PATRIMÔNIO / INVENTÁRIO (COM GRÁFICO SAAS) ---
                    else:
                        st.info("🎯 **Objetivo Detectado:** Inventário (Análise de Estoque e Ponto de Reposição).")
                        
                        col_qtd = next((v for k, v in cols_limpas.items() if any(x in k for x in ['qtd', 'quantidade', 'saldo', 'estoque'])), None)
                        col_desc = next((v for k, v in cols_limpas.items() if any(x in k for x in ['descri', 'item', 'produto', 'nome'])), None)
                        col_marca = next((v for k, v in cols_limpas.items() if 'marca' in k or 'fabricante' in k), None)
                        col_prat = next((v for k, v in cols_limpas.items() if 'prateleira' in k or 'local' in k), None)
                        col_obs = next((v for k, v in cols_limpas.items() if 'obs' in k or 'coment' in k), None)
                        col_minimo = next((v for k, v in cols_limpas.items() if 'mínimo' in k or 'minimo' in k), None)

                        if col_qtd and col_desc:
                            df[col_qtd] = pd.to_numeric(df[col_qtd], errors='coerce').fillna(0)
                            
                            # 💡 MÉTRICAS ESTILO SAAS (TOPO)
                            col_m1, col_m2, col_m3 = st.columns(3)
                            
                            if col_minimo:
                                df[col_minimo] = pd.to_numeric(df[col_minimo], errors='coerce').fillna(0)
                                df_critico = df[df[col_qtd] <= df[col_minimo]].sort_values(by=col_qtd)
                                
                                col_m1.metric("📦 Total de Itens", len(df))
                                col_m2.metric("🔢 Volume em Estoque", f"{int(df[col_qtd].sum())} unid.")
                                col_m3.metric("🚨 Itens em Nível Crítico", len(df_critico))

                                if not df_critico.empty:
                                    st.error(f"🚨 **ALERTA DE REPOSIÇÃO: {len(df_critico)} itens atingiram a sua cota mínima!**")
                                    for _, linha in df_critico.iterrows():
                                        c1, c2 = st.columns([0.85, 0.15])
                                        item_nome = linha[col_desc]
                                        saldo = int(linha[col_qtd])
                                        minimo_item = int(linha[col_minimo])
                                        
                                        c1.write(f"📦 **{item_nome}** | Saldo: **{saldo}** (Mín: **{minimo_item}**) | Marca: {linha.get(col_marca, 'S/M')}")
                                        conteudo_ics_estoque = criar_lembrete_estoque(item_nome, saldo, minimo_item)
                                        c2.download_button(label="🔔 Repor", data=conteudo_ics_estoque, file_name=f"Repor_{str(item_nome)[:10]}.ics", key=str(uuid.uuid4()))
                            else:
                                col_m1.metric("📦 Total de Itens Analisados", len(df))
                                col_m2.metric("🔢 Volume Total em Estoque", f"{int(df[col_qtd].sum())} unid.")
                                st.warning("⚠️ **Atenção:** Coluna de 'ESTOQUE MÍNIMO' não encontrada para gerar alertas.")

                        st.write("---")
                        
                        # 💡 CAMPO DE PESQUISA INTELIGENTE E SAAS
                        busca_est = campo_pesquisa("🔍 Busca Dinâmica", "Pesquise por peça, marca ou local para filtrar o gráfico e a tabela...", key=f"be_{arquivo.name}")
                        
                        colunas_desejadas = [c for c in [col_qtd, col_minimo, col_desc, col_marca, col_prat, col_obs] if c]
                        
                        if colunas_desejadas:
                            df_filtrado = df[colunas_desejadas].copy()
                            if busca_est:
                                mask_est = df_filtrado.astype(str).apply(lambda x: x.str.contains(busca_est, case=False, na=False)).any(axis=1)
                                df_filtrado = df_filtrado[mask_est]
                            
                            # 💡 O NOVO SISTEMA DE ABAS (COM O GRÁFICO IGUAL AO DO RELATORIADOR)
                            aba_visu, aba_tab = st.tabs(["📊 Ranking de Estoque (Gráfico)", "📋 Tabela Detalhada"])
                            
                            with aba_visu:
                                if not df_filtrado.empty and st_echarts is not None:
                                    st.write("💡 *Visualize as peças com maior e menor disponibilidade. Use a Câmera para baixar a imagem.*")
                                    
                                    # Agrupa as peças para o gráfico e ordena (maior em cima)
                                    dados_grafico = df_filtrado.groupby(col_desc)[col_qtd].sum().reset_index().sort_values(by=col_qtd, ascending=True)
                                    
                                    dados_barras_formatados = []
                                    for _, row in dados_grafico.iterrows():
                                        dados_barras_formatados.append({
                                            "value": int(row[col_qtd]),
                                            "label": {"show": True, "position": "right", "formatter": "{c} unid.", "color": "#0F172A", "fontWeight": "bold"}
                                        })
                                    
                                    altura_dinamica = max(500, len(dados_grafico) * 45)
                                    
                                    bar_options = {
                                        "backgroundColor": "transparent",
                                        "title": {"text": "Volume de Estoque por Item", "left": "center", "textStyle": {"color": "#0F172A", "fontSize": 16, "fontFamily": "Plus Jakarta Sans"}},
                                        "toolbox": {"feature": {"saveAsImage": {"show": True, "title": "Baixar PNG", "pixelRatio": 2}}},
                                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                                        "grid": {"top": 60, "left": "1%", "right": "10%", "bottom": "1%", "containLabel": True},
                                        "xAxis": {"type": "value", "splitLine": {"lineStyle": {"type": "dashed", "color": "#E2E8F0"}}},
                                        "yAxis": {
                                            "type": "category", 
                                            "data": dados_grafico[col_desc].tolist(), 
                                            "axisLabel": {
                                                "interval": 0, 
                                                "width": 250, 
                                                "overflow": "break", 
                                                "lineHeight": 14,
                                                "color": "#475569",
                                                "fontFamily": "Plus Jakarta Sans"
                                            }
                                        },
                                        "series": [{"type": "bar", "data": dados_barras_formatados, "itemStyle": {"color": "#0F172A", "borderRadius": [0, 6, 6, 0]}}]
                                    }
                                    st_echarts(options=bar_options, height=f"{altura_dinamica}px")
                                else:
                                    st.info("Nenhum dado encontrado para gerar o gráfico.")

                            with aba_tab:
                                nomes_exibicao = {col_qtd: "QUANTIDADE", col_minimo: "ESTOQUE MÍNIMO", col_desc: "DESCRIÇÃO", col_marca: "MARCA", col_prat: "PRATELEIRA", col_obs: "OBSERVAÇÕES"}
                                df_tabela = df_filtrado.rename(columns={k: v for k, v in nomes_exibicao.items() if k in df_filtrado.columns})
                                st.dataframe(df_tabela, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro na planilha: {e}")

            elif extensao in ['docx', 'txt']:
                st.info("🎯 **Objetivo Detectado:** Catálogo / Documentação.")
                if Document is None and extensao == 'docx':
                    st.error("Biblioteca 'python-docx' não instalada. Adicione ao requirements.txt.")
                else:
                    conteudo = [p.text for p in Document(arquivo).paragraphs] if extensao == 'docx' else arquivo.read().decode("utf-8").splitlines()
                    
                    busca = campo_pesquisa(f"🔍 Busca Dinâmica no arquivo: {arquivo.name}", "Digite para escanear o documento...", key=f"bd_{arquivo.name}")
                    
                    if busca:
                        resultados = [l for l in conteudo if busca.lower() in l.lower()]
                        if resultados:
                            for r in resultados: 
                                st.write(f"🔹 {r}")
                        else:
                            st.warning("Nenhum trecho correspondente encontrado no documento.")

else:
    st.info("Aguardando o envio de documentos para iniciar as operações.")