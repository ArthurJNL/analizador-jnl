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

                    # Identificação de Tipo de Planilha
                    is_financeiro = any(k in str(cols_limpas.keys()) for k in ['vencimento', 'data']) and any(k in str(cols_limpas.keys()) for k in ['valor', 'r$'])

                    # --- FLUXO 1: FINANCEIRO ---
                    if is_financeiro:
                        st.info("🎯 **Objetivo Detectado:** Controle Financeiro / Contas a Receber.")
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
                            st.dataframe(df, use_container_width=True)

                    # --- FLUXO 2: PATRIMÔNIO / INVENTÁRIO (ATUALIZADO) ---
                    else:
                        st.warning("🎯 **Objetivo Detectado:** Controle de Patrimônio / Inventário. O sistema está monitorando a quantidade de itens e localização.")
                        
                        # Mapeamento Inteligente de Colunas
                        col_qtd = next((v for k, v in cols_limpas.items() if any(x in k for x in ['qtd', 'quantidade', 'saldo', 'estoque'])), None)
                        col_desc = next((v for k, v in cols_limpas.items() if any(x in k for x in ['descri', 'item', 'produto', 'nome'])), None)
                        col_marca = next((v for k, v in cols_limpas.items() if 'marca' in k or 'fabricante' in k), None)
                        col_prat = next((v for k, v in cols_limpas.items() if 'prateleira' in k or 'local' in k), None)
                        col_obs = next((v for k, v in cols_limpas.items() if 'obs' in k or 'coment' in k), None)

                        # Verificação de Alertas Críticos (≤ 2 unidades)
                        if col_qtd and col_desc:
                            df[col_qtd] = pd.to_numeric(df[col_qtd], errors='coerce').fillna(0)
                            df_critico = df[df[col_qtd] <= 2].sort_values(by=col_qtd)
                            
                            if not df_critico.empty:
                                st.error(f"🚨 **ALERTA DE REPOSIÇÃO: {len(df_critico)} itens com estoque baixo!**")
                                for _, linha in df_critico.iterrows():
                                    c1, c2 = st.columns([0.85, 0.15])
                                    item_nome = linha[col_desc]
                                    saldo = int(linha[col_qtd])
                                    c1.write(f"📦 **{item_nome}** | Saldo: **{saldo}** | Marca: {linha.get(col_marca, 'S/M')} | Local: {linha.get(col_prat, 'S/L')}")
                                    conteudo_ics_estoque = criar_lembrete_estoque(item_nome, saldo)
                                    c2.download_button(label="🔔 Repor", data=conteudo_ics_estoque, file_name=f"Repor_{str(item_nome)[:10]}.ics", key=str(uuid.uuid4()))
                            else:
                                st.success("✅ Todos os itens do patrimônio estão com saldo acima de 2 unidades.")

                        # Arrumando a Planilha para exibição limitada
                        st.write("---")
                        st.write("**Tabela de Controle (Filtro Especial):**")
                        
                        # Definindo as colunas que devem ser mostradas (apenas se existirem no arquivo)
                        colunas_desejadas = [c for c in [col_qtd, col_desc, col_marca, col_prat, col_obs] if c]
                        
                        if colunas_desejadas:
                            df_filtrado = df[colunas_desejadas].copy()
                            # Renomeando para ficar padrão na visualização
                            nomes_exibicao = {}
                            if col_qtd: nomes_exibicao[col_qtd] = "QUANTIDADE"
                            if col_desc: nomes_exibicao[col_desc] = "DESCRIÇÃO"
                            if col_marca: nomes_exibicao[col_marca] = "MARCA"
                            if col_prat: nomes_exibicao[col_prat] = "PRATELEIRA"
                            if col_obs: nomes_exibicao[col_obs] = "OBSERVAÇÕES"
                            
                            df_filtrado.rename(columns=nomes_exibicao, inplace=True)
                            st.dataframe(df_filtrado, use_container_width=True)
                        else:
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
