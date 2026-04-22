import streamlit as st
import pandas as pd
from datetime import datetime
from docx import Document
import uuid

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador JNL", page_icon="🛡️", layout="wide")

st.title("🛡️ ANALIZADOR JNL")
st.write("Análise inteligente e ao vivo.")

arquivos_enviados = st.file_uploader("Arraste seus arquivos aqui", type=["xlsx", "xls", "xlsm", "docx", "txt"], accept_multiple_files=True)

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

def criar_lembrete_estoque(item, qtd):
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
        f"DESCRIPTION:Alerta JNL\\nO item {item_limpo} está com apenas {qtd} unidades em estoque. Necessário repor urgente.\n"
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
                    
                    # Limpeza de cabeçalhos
                    if any("Unnamed" in str(c) for c in df.columns):
                        for idx, row in df.head(15).iterrows():
                            linha_texto = " ".join([str(x).lower() for x in row.values])
                            if any(k in linha_texto for k in ['valor', 'r$', 'data', 'venc', 'cliente', 'item', 'qtd', 'estoque']):
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

                    # Identificação de Tipo de Planilha
                    is_financeiro = any(k in str(cols_limpas.keys()) for k in ['vencimento', 'data']) and any(k in str(cols_limpas.keys()) for k in ['valor', 'r$'])
                    is_estoque = any(k in str(cols_limpas.keys()) for k in ['qtd', 'estoque', 'quantidade', 'saldo'])

                    # --- FLUXO 1: FINANCEIRO ---
                    if is_financeiro:
                        st.info("🎯 **Objetivo Detectado:** Controle Financeiro / Contas a Receber.")
                        col_data = next((v for k, v in cols_limpas.items() if 'vencimento' in k or 'data' in k), None)
                        col_valor = next((v for k, v in cols_limpas.items() if 'valor' in k or 'r$' in k), None)
                        col_cliente = next((v for k, v in cols_limpas.items() if 'cliente' in k or 'nome' in k or 'empresa' in k), "S/N")
                        col_orc = next((v for k, v in cols_limpas.items() if 'orc' in k or 'orç' in k or 'pedido' in k or 'doc' in k), None)
                        col_parcela = next((v for k, v in cols_limpas.items() if 'parcela' in k), None)
                        col_status = next((v for k, v in cols_limpas.items() if 'obs' in k or 'status' in k or 'situa' in k), None)
                        
                        df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
                        
                        mask_pago = df[col_status].astype(str).str.lower().str.contains('pago') if col_status else df[df.columns[-1]].astype(str).str.lower().str.contains('pago')
                        df_pendente = df[~mask_pago].dropna(subset=[col_data])
                        
                        hoje = pd.to_datetime('today').normalize()
                        df_vencidos = df_pendente[df_pendente[col_data] < hoje]
                        df_a_vencer = df_pendente[df_pendente[col_data] >= hoje].sort_values(by=col_data)

                        tab_venc, tab_dados = st.tabs(["📅 Resumo Financeiro", "📋 Planilha Completa"])
                        
                        with tab_venc:
                            st.markdown(f"**Valor total em aberto: {formatar_moeda(df_pendente[col_valor].sum())}**")
                            if not df_a_vencer.empty:
                                st.markdown("#### Próximos Vencimentos:")
                                for _, linha in df_a_vencer.head(10).iterrows():
                                    c1, c2 = st.columns([0.85, 0.15])
                                    c1.write(f"📌 **{linha.get(col_cliente, 'S/N')}** | {formatar_moeda(linha[col_valor])} | Venc: {linha[col_data].strftime('%d/%m/%Y')}")
                                    conteudo_ics = criar_lembrete_item(linha[col_data], linha.get(col_cliente, 'S/N'), linha[col_valor], linha.get(col_orc))
                                    c2.download_button("🔔 Me lembre", data=conteudo_ics, file_name="Lembrete.ics", key=str(uuid.uuid4()))

                        with tab_dados:
                            st.dataframe(df, use_container_width=True)

                    # --- FLUXO 2: ESTOQUE (NOVIDADE) ---
                    elif is_estoque:
                        st.warning("🎯 **Objetivo Detectado:** Controle de Estoque. O sistema está monitorando níveis críticos de mercadoria para evitar falta de itens.")
                        
                        col_qtd = next((v for k, v in cols_limpas.items() if 'qtd' in k or 'quantidade' in k or 'saldo' in k or 'estoque' in k), None)
                        col_item = next((v for k, v in cols_limpas.items() if 'item' in k or 'descrição' in k or 'peça' in k or 'produto' in k or 'nome' in k), df.columns[0])
                        
                        df[col_qtd] = pd.to_numeric(df[col_qtd], errors='coerce').fillna(0)
                        df_critico = df[df[col_qtd] <= 2].sort_values(by=col_qtd)
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Total de Itens em Estoque", len(df))
                        col2.metric("Itens com Baixa Qtd (≤ 2)", len(df_critico))
                        
                        st.write("---")
                        if not df_critico.empty:
                            st.error("🚨 **ALERTA DE REPOSIÇÃO: Itens Críticos Encontrados**")
                            for _, linha in df_critico.iterrows():
                                c1, c2 = st.columns([0.85, 0.15])
                                nome_item = linha[col_item]
                                saldo = int(linha[col_qtd])
                                
                                c1.write(f"📦 **{nome_item}** | Saldo atual: **{saldo}** unidades.")
                                conteudo_ics_estoque = criar_lembrete_estoque(nome_item, saldo)
                                c2.download_button(
                                    label="🔔 Repor",
                                    data=conteudo_ics_estoque,
                                    file_name=f"Repor_{str(nome_item)[:10].strip()}.ics",
                                    mime="text/calendar",
                                    key=str(uuid.uuid4())
                                )
                        else:
                            st.success("✅ Todos os itens estão com saldo acima do nível crítico!")
                        
                        st.write("**Tabela Geral de Estoque:**")
                        st.dataframe(df, use_container_width=True)

                    # --- FLUXO 3: PATRIMÔNIO / GERAL ---
                    else:
                        st.success("🎯 **Objetivo Detectado:** Controle de Patrimônio / Inventário.")
                        st.metric("Total de Itens Cadastrados", len(df))
                        st.dataframe(df, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro na planilha: {e}")

            # --- CASO 2: DOCUMENTOS (WORD OU TXT) ---
            elif extensao in ['docx', 'txt']:
                st.info("🎯 **Objetivo Detectado:** Catálogo / Documentação.")
                conteudo = [p.text for p in Document(arquivo).paragraphs] if extensao == 'docx' else arquivo.read().decode("utf-8").splitlines()
                busca = st.text_input(f"Buscar em {arquivo.name}")
                if busca:
                    for r in [l for l in conteudo if busca.lower() in l.lower()]: st.write(f"🔹 {r}")

else:
    st.info("Aguardando o envio de documentos para iniciar as operações.")
