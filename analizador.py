import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador JNL", page_icon="📊", layout="wide")

st.title("📄 ANALIZADOR DINÂMICO JNL")
st.write("Análise inteligente de múltiplas planilhas (Financeiras e Gerais).")

# ==========================================
# UPLOAD DE ARQUIVOS
# ==========================================
arquivos_enviados = st.file_uploader("Selecione as planilhas", type=["xlsx", "xls", "xlsm"], accept_multiple_files=True)

st.markdown("---")

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# LÓGICA DE PROCESSAMENTO HÍBRIDO
# ==========================================
if arquivos_enviados:
    for arquivo in arquivos_enviados:
        with st.expander(f"📊 RELATÓRIO: {arquivo.name.upper()}", expanded=True):
            try:
                df = pd.read_excel(arquivo)
                
                # CORREÇÃO DA PLANILHA PIX: Força a conversão do título da coluna para texto (str) antes de buscar
                cols = {str(c).lower(): c for c in df.columns}
                
                # O Scanner Inteligente procura palavras-chave nos títulos
                col_data = next((v for k, v in cols.items() if 'vencimento' in k or 'data' in k), None)
                col_valor = next((v for k, v in cols.items() if 'valor' in k or 'r$' in k or 'total' in k), None)
                col_cliente = next((v for k, v in cols.items() if 'cliente' in k or 'nome' in k or 'empresa' in k or 'descrição' in k or 'fornecedor' in k), "NÃO IDENTIFICADO")
                col_orc = next((v for k, v in cols.items() if 'orc' in k or 'pedido' in k or 'número' in k or 'doc' in k), "S/N")
                col_parcela = next((v for k, v in cols.items() if 'parcela' in k), "ÚNICA")

                # CÁLCULO 1: SE FOR PLANILHA FINANCEIRA
                if col_data and col_valor:
                    df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
                    hoje = pd.to_datetime('today').normalize()
                    
                    df_vencidos = df[df[col_data] < hoje].sort_values(by=col_data)
                    df_a_vencer = df[df[col_data] >= hoje].sort_values(by=col_data)
                    
                    subtotal_vencidos = df_vencidos[col_valor].sum()
                    subtotal_a_vencer = df_a_vencer[col_valor].sum()
                    total_geral = subtotal_vencidos + subtotal_a_vencer
                    
                    tab_venc, tab_dados = st.tabs(["📅 Resumo Financeiro", "📋 Planilha Completa"])
                    
                    with tab_venc:
                        st.markdown("#### Segue o resumo financeiro desta planilha:")
                        st.markdown("**Itens já vencidos (ou com data no passado):**")
                        
                        if not df_vencidos.empty:
                            for _, linha in df_vencidos.iterrows():
                                data_f = linha[col_data].strftime('%d/%m/%Y') if not pd.isnull(linha[col_data]) else "S/D"
                                st.write(f"- {linha.get(col_cliente, 'S/N')}, DOC/ORÇ: {linha.get(col_orc, 'S/N')}, {linha.get(col_parcela, 'ÚNICA')}, {formatar_moeda(linha[col_valor])}, {data_f}")
                            st.write(f"**Subtotal: {formatar_moeda(subtotal_vencidos)}**")
                        else:
                            st.success("✅ Não há itens vencidos ou atrasados detectados.")
                        
                        st.markdown("---")
                        st.write(f"**Itens a vencer:** {len(df_a_vencer)} (Subtotal: {formatar_moeda(subtotal_a_vencer)})")
                        st.write(f"**Valor total em aberto: {formatar_moeda(total_geral)}**")
                        
                        if not df_a_vencer.empty:
                            proximo = df_a_vencer.iloc[0]
                            data_p = proximo[col_data].strftime('%d/%m/%Y') if not pd.isnull(proximo[col_data]) else "S/D"
                            st.write(f"**Próximo vencimento:** {proximo.get(col_cliente, 'S/N')}, DOC/ORÇ: {proximo.get(col_orc, 'S/N')}, {proximo.get(col_parcela, 'ÚNICA')}, {formatar_moeda(proximo[col_valor])}, {data_p}")

                    with tab_dados:
                        st.dataframe(df, use_container_width=True)

                # CÁLCULO 2: SE FOR PLANILHA GERAL (Sem Data/Valor claro)
                else:
                    tab_resumo, tab_dados = st.tabs(["📊 Análise Estrutural", "📋 Planilha Completa"])
                    with tab_resumo:
                        st.info("ℹ️ **Modo Estrutural:** O robô detectou que esta planilha não possui formato padrão de contas/vencimentos. Exibindo análise geral de dados.")
                        st.write(f"- **Volume de Dados:** {df.shape[0]} linhas preenchidas registradas.")
                        st.write(f"- **Mapeamento de Colunas:** {', '.join([str(c) for c in df.columns])}")
                        
                        vazios = df.isnull().sum().sum()
                        if vazios > 0:
                            st.warning(f"⚠️ **Atenção:** O sistema detectou {vazios} células em branco no documento. É recomendável revisar se há perda de informação importante.")
                        else:
                            st.success("✅ **Integridade:** A planilha encontra-se 100% preenchida, sem buracos ou lacunas detectáveis.")
                            
                    with tab_dados:
                        st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Erro crítico ao processar o arquivo. A planilha pode estar corrompida. (Detalhe: {e})")

else:
    st.info("O robô está ocioso. Aguardando o envio de planilhas para iniciar o trabalho.")