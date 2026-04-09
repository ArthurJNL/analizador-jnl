import streamlit as st
import pandas as pd
from datetime import datetime
from docx import Document # Para ler arquivos Word

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador JNL", page_icon="🛡️", layout="wide")

st.title("🛡️ ANALIZADOR INTEGRADO JNL")
st.write("Análise de Faturamento, Patrimônio e Catálogos (Excel, Word e TXT).")

# Atualizamos os tipos de arquivos aceitos
arquivos_enviados = st.file_uploader("Arraste seus arquivos aqui", type=["xlsx", "xls", "xlsm", "docx", "txt"], accept_multiple_files=True)

st.markdown("---")

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

# ==========================================
# PROCESSAMENTO DE ARQUIVOS
# ==========================================
if arquivos_enviados:
    for arquivo in arquivos_enviados:
        extensao = arquivo.name.split('.')[-1].lower()
        
        with st.expander(f"📄 ARQUIVO: {arquivo.name.upper()}", expanded=True):
            
            # --- CASO 1: PLANILHAS EXCEL ---
            if extensao in ['xlsx', 'xls', 'xlsm']:
                try:
                    df = pd.read_excel(arquivo)
                    
                    # Auto-detecção de cabeçalho
                    if any("Unnamed" in str(c) for c in df.columns):
                        for idx, row in df.head(10).iterrows():
                            linha_texto = " ".join([str(x).lower() for x in row.values])
                            if any(k in linha_texto for k in ['valor', 'r$', 'data', 'venc', 'cliente', 'item', 'patrimonio']):
                                df.columns = [str(n).strip() if pd.notna(n) else f"vazio_{i}" for i, n in enumerate(row.values)]
                                df = df.iloc[idx+1:].reset_index(drop=True)
                                break
                    
                    df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                    cols_limpas = {str(c).lower().strip(): c for c in df.columns}

                    # Identifica se é FINANCEIRO ou PATRIMÔNIO
                    is_financeiro = any(k in str(cols_limpas.keys()) for k in ['vencimento', 'data']) and any(k in str(cols_limpas.keys()) for k in ['valor', 'r$'])
                    
                    if is_financeiro:
                        # [LÓGICA FINANCEIRA QUE JÁ FUNCIONA]
                        col_data = next((v for k, v in cols_limpas.items() if 'vencimento' in k or 'data' in k), None)
                        col_valor = next((v for k, v in cols_limpas.items() if 'valor' in k or 'r$' in k), None)
                        col_status = next((v for k, v in cols_limpas.items() if 'pago' in k or 'obs' in k or 'situa' in k), df.columns[-1])
                        
                        df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
                        
                        # Filtro de Pagos
                        mask_pago = df[col_status].astype(str).str.lower().str.contains('pago')
                        df_pendente = df[~mask_pago].dropna(subset=[col_data])
                        
                        hoje = pd.to_datetime('today').normalize()
                        vencidos = df_pendente[df_pendente[col_data] < hoje]
                        
                        st.write(f"### Resumo Financeiro")
                        st.error(f"Itens Vencidos: {len(vencidos)} | Subtotal: {formatar_moeda(vencidos[col_valor].sum())}")
                        st.dataframe(vencidos, use_container_width=True)
                    
                    else:
                        # [LÓGICA DE PATRIMÔNIO / GERAL]
                        st.write("### Análise de Controle de Patrimônio")
                        total_itens = len(df)
                        
                        # Analisa buracos nos dados
                        dados_faltantes = df.isnull().sum()
                        colunas_com_falha = dados_faltantes[dados_faltantes > 0]
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Total de Itens", total_itens)
                        col2.metric("Colunas Incompletas", len(colunas_com_falha))
                        
                        if not colunas_com_falha.empty:
                            st.warning("🚨 **Atenção: Faltam dados no inventário!**")
                            for col, qtd in colunas_com_falha.items():
                                st.write(f"- A coluna **'{col}'** está sem informação em **{qtd}** itens.")
                        else:
                            st.success("✅ Todos os itens do patrimônio estão com os dados preenchidos!")
                        
                        st.write("---")
                        st.write("**Visualização dos Itens:**")
                        st.dataframe(df, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro ao ler planilha: {e}")

            # --- CASO 2: DOCUMENTOS (WORD OU TXT) ---
            elif extensao in ['docx', 'txt']:
                st.write("### 🔍 Pesquisa Inteligente no Catálogo")
                conteudo = []
                
                if extensao == 'docx':
                    doc = Document(arquivo)
                    conteudo = [p.text for p in doc.paragraphs if p.text.strip() != ""]
                else:
                    conteudo = arquivo.read().decode("utf-8").splitlines()
                
                # Campo de busca dinâmico
                busca = st.text_input(f"O que deseja filtrar em {arquivo.name}?", placeholder="Digite o código da peça, nome ou marca...")
                
                if busca:
                    resultados = [linha for linha in conteudo if busca.lower() in linha.lower()]
                    if resultados:
                        st.success(f"Encontrados {len(resultados)} correspondências:")
                        for r in resultados:
                            st.info(r)
                    else:
                        st.warning("Nenhum item encontrado com esse termo.")
                else:
                    st.write("Digite algo acima para filtrar o catálogo.")
                    with st.expander("Ver conteúdo completo"):
                        for linha in conteudo:
                            st.write(linha)

else:
    st.info("Aguardando o envio de planilhas ou catálogos.")