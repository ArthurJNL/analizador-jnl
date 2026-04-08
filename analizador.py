import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador JNL", page_icon="💰", layout="wide")

st.title("📄 ANALIZADOR FINANCEIRO JNL")
st.write("Análise inteligente de planilhas de faturamento.")

arquivos_enviados = st.file_uploader("Selecione as planilhas", type=["xlsx", "xls", "xlsm"], accept_multiple_files=True)

st.markdown("---")

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

if arquivos_enviados:
    for arquivo in arquivos_enviados:
        with st.expander(f"📊 RELATÓRIO: {arquivo.name.upper()}", expanded=True):
            try:
                # Carrega o arquivo inteiro
                df = pd.read_excel(arquivo)
                
                # ==========================================
                # O TRUQUE MESTRE: AUTO-DETECÇÃO DE CABEÇALHO
                # Se a planilha tem título mesclado na linha 1, o pandas cria colunas "Unnamed".
                # O robô vai caçar o cabeçalho real nas 15 primeiras linhas.
                # ==========================================
                if any("Unnamed" in str(c) for c in df.columns):
                    for idx, row in df.head(15).iterrows():
                        linha_texto = " ".join([str(x).lower() for x in row.values])
                        # Se achar as palavras chaves na linha, essa linha vira o cabeçalho
                        if ('valor' in linha_texto or 'r$' in linha_texto) and ('data' in linha_texto or 'venc' in linha_texto or 'cliente' in linha_texto):
                            df.columns = row
                            df = df.iloc[idx+1:].reset_index(drop=True)
                            break
                
                # Limpa colunas e linhas fantasmas (100% vazias) geradas por formatação do Excel
                df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)

                # ==========================================
                # MAPEAR AS COLUNAS ENCONTRADAS
                # ==========================================
                cols = {str(c).lower().strip(): c for c in df.columns}
                
                col_data = next((v for k, v in cols.items() if 'vencimento' in k or 'data' in k), None)
                col_valor = next((v for k, v in cols.items() if 'valor' in k or 'r$' in k or 'total' in k), None)
                col_cliente = next((v for k, v in cols.items() if 'cliente' in k or 'nome' in k or 'empresa' in k or 'descrição' in k or 'fornecedor' in k), "S/N")
                col_orc = next((v for k, v in cols.items() if 'orc' in k or 'pedido' in k or 'número' in k or 'doc' in k), None)
                col_parcela = next((v for k, v in cols.items() if 'parcela' in k), None)

                if col_data and col_valor:
                    # Formata as colunas matemáticas para evitar erros
                    df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
                    
                    # Remove linhas que não têm data válida
                    df_valid = df.dropna(subset=[col_data])
                    
                    hoje = pd.to_datetime('today').normalize()
                    
                    df_vencidos = df_valid[df_valid[col_data] < hoje].sort_values(by=col_data)
                    df_a_vencer = df_valid[df_valid[col_data] >= hoje].sort_values(by=col_data)
                    
                    subtotal_vencidos = df_vencidos[col_valor].sum()
                    subtotal_a_vencer = df_a_vencer[col_valor].sum()
                    total_geral = subtotal_vencidos + subtotal_a_vencer
                    
                    # Aba interativa com a apresentação exigida
                    tab_venc, tab_dados = st.tabs(["📅 Resumo Financeiro", "📋 Planilha Completa"])
                    
                    with tab_venc:
                        nome_planilha_limpo = arquivo.name.upper().replace(".XLSX", "").replace(".XLSM", "").replace(".XLS", "")
                        st.markdown(f"#### Segue o resumo da planilha {nome_planilha_limpo}:")
                        st.write("")
                        
                        st.markdown("**Itens já vencidos:**")
                        st.write("")
                        
                        if not df_vencidos.empty:
                            for _, linha in df_vencidos.iterrows():
                                data_f = linha[col_data].strftime('%d/%m/%Y')
                                cliente_nome = linha.get(col_cliente, 'S/N')
                                
                                # Monta o texto de Orçamento e Parcela se eles existirem na planilha
                                txt_orc = f", ORÇ: {int(linha[col_orc]) if pd.notnull(linha[col_orc]) else 'S/N'}" if col_orc else ""
                                txt_parc = f", {linha[col_parcela]}" if col_parcela and pd.notnull(linha[col_parcela]) else ""
                                
                                st.write(f"{cliente_nome}{txt_orc}{txt_parc}, {formatar_moeda(linha[col_valor])}, {data_f}")
                            
                            st.write("")
                            st.markdown(f"**Subtotal: {formatar_moeda(subtotal_vencidos)};**")
                        else:
                            st.success("Nenhum item vencido.")
                            st.markdown(f"**Subtotal: R$ 0,00;**")
                        
                        st.write("")
                        st.write("")
                        st.markdown(f"**Itens a vencer: {len(df_a_vencer)} (Subtotal: {formatar_moeda(subtotal_a_vencer)});**")
                        st.write("")
                        st.write("")
                        st.markdown(f"**Valor total em aberto: {formatar_moeda(total_geral)};**")
                        st.write("")
                        st.write("")
                        
                        if not df_a_vencer.empty:
                            proximo = df_a_vencer.iloc[0]
                            data_p = proximo[col_data].strftime('%d/%m/%Y')
                            cliente_p = proximo.get(col_cliente, 'S/N')
                            txt_orc_p = f", ORÇ: {int(proximo[col_orc]) if pd.notnull(proximo[col_orc]) else 'S/N'}" if col_orc else ""
                            txt_parc_p = f", {proximo[col_parcela]}" if col_parcela and pd.notnull(proximo[col_parcela]) else ""
                            
                            st.markdown(f"**Próximo vencimento:** {cliente_p}{txt_orc_p}{txt_parc_p}, {formatar_moeda(proximo[col_valor])}, {data_p}")

                    with tab_dados:
                        st.dataframe(df, use_container_width=True)

                else:
                    st.info(f"Modo Estrutural: O robô detectou que '{arquivo.name}' é um relatório sem dados financeiros (Data e Valor).")
                    st.write(f"Volume: {df.shape[0]} linhas.")
                    st.dataframe(df.head(10), use_container_width=True)

            except Exception as e:
                st.error(f"Erro ao processar: {e}")

else:
    st.info("Aguardando o senhor anexar as planilhas.")