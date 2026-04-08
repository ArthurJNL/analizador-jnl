import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador JNL", page_icon="💰", layout="wide")

st.title("📄 ANALIZADOR FINANCEIRO JNL")
st.write("Análise detalhada de contas e vencimentos por planilha.")

# ==========================================
# UPLOAD DE ARQUIVOS
# ==========================================
arquivos_enviados = st.file_uploader("Selecione as planilhas de contas", type=["xlsx", "xls", "xlsm"], accept_multiple_files=True)

st.markdown("---")

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# LÓGICA DE PROCESSAMENTO INDIVIDUAL
# ==========================================
if arquivos_enviados:
    for arquivo in arquivos_enviados:
        with st.expander(f"📊 RELATÓRIO: {arquivo.name.upper()}", expanded=True):
            try:
                df = pd.read_excel(arquivo)
                
                # TENTATIVA DE MAPEAMENTO AUTOMÁTICO DE COLUNAS
                cols = {c.lower(): c for c in df.columns}
                
                # Busca colunas por palavras-chave
                col_data = next((v for k, v in cols.items() if 'vencimento' in k or 'data' in k), None)
                col_valor = next((v for k, v in cols.items() if 'valor' in k or 'r$' in k or 'total' in k), None)
                col_cliente = next((v for k, v in cols.items() if 'cliente' in k or 'nome' in k or 'empresa' in k), "CLIENTE NÃO IDENTIFICADO")
                col_orc = next((v for k, v in cols.items() if 'orc' in k or 'pedido' in k or 'número' in k), "S/N")
                col_parcela = next((v for k, v in cols.items() if 'parcela' in k), "UNICA")

                if col_data and col_valor:
                    # Preparação dos dados
                    df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
                    hoje = pd.to_datetime('today').normalize()
                    
                    df_vencidos = df[df[col_data] < hoje].sort_values(by=col_data)
                    df_a_vencer = df[df[col_data] >= hoje].sort_values(by=col_data)
                    
                    # CÁLCULOS
                    subtotal_vencidos = df_vencidos[col_valor].sum()
                    subtotal_a_vencer = df_a_vencer[col_valor].sum()
                    total_geral = subtotal_vencidos + subtotal_a_vencer
                    
                    # ABAS DE ANÁLISE
                    tab_venc, tab_dados = st.tabs(["📅 Resumo de Vencimentos", "📋 Ver Planilha Completa"])
                    
                    with tab_venc:
                        st.markdown("#### Segue o resumo das contas a receber:")
                        
                        st.markdown("**Itens já vencidos:**")
                        if not df_vencidos.empty:
                            for _, linha in df_vencidos.iterrows():
                                data_f = linha[col_data].strftime('%d/%m/%Y') if not pd.isnull(linha[col_data]) else "S/D"
                                st.write(f"- {linha[col_cliente]}, ORÇ: {linha[col_orc]}, {linha[col_parcela]}, {formatar_moeda(linha[col_valor])}, {data_f}")
                            
                            st.write(f"**Subtotal: {formatar_moeda(subtotal_vencidos)}**")
                        else:
                            st.success("Não há itens vencidos nesta planilha.")
                        
                        st.markdown("---")
                        st.write(f"**Itens a vencer:** {len(df_a_vencer)} (Subtotal: {formatar_moeda(subtotal_a_vencer)})")
                        st.write(f"**Valor total em aberto: {formatar_moeda(total_geral)}**")
                        
                        if not df_a_vencer.empty:
                            proximo = df_a_vencer.iloc[0]
                            data_p = proximo[col_data].strftime('%d/%m/%Y')
                            st.write(f"**Próximo vencimento:** {proximo[col_cliente]}, ORÇ: {proximo[col_orc]}, {proximo[col_parcela]}, {formatar_moeda(proximo[col_valor])}, {data_p}")

                    with tab_dados:
                        st.dataframe(df, use_container_width=True)
                else:
                    st.error(f"❌ Não foi possível identificar colunas de 'Data' e 'Valor' no arquivo {arquivo.name}. Verifique os títulos da primeira linha.")

            except Exception as e:
                st.error(f"Erro ao processar {arquivo.name}: {e}")

else:
    st.info("Aguardando o senhor anexar as planilhas de faturamento.")