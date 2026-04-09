import streamlit as st
import pandas as pd
from datetime import datetime
from docx import Document

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
                        for idx, row in df.head(15).iterrows():
                            linha_texto = " ".join([str(x).lower() for x in row.values])
                            if any(k in linha_texto for k in ['valor', 'r$', 'data', 'venc', 'cliente', 'item', 'patrimônio', 'empresa']):
                                # Cria nomes únicos para evitar erros
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

                    # Identificação Inteligente do Objetivo
                    is_financeiro = any(k in str(cols_limpas.keys()) for k in ['vencimento', 'data']) and any(k in str(cols_limpas.keys()) for k in ['valor', 'r$'])
                    
                    if is_financeiro:
                        st.info("🎯 **Objetivo Detectado:** Controle Financeiro / Contas a Receber. O sistema está priorizando a análise de fluxo de caixa, verificando inadimplência e projetando recebimentos futuros.")
                        
                        col_data = next((v for k, v in cols_limpas.items() if 'vencimento' in k or 'data' in k), None)
                        col_valor = next((v for k, v in cols_limpas.items() if 'valor' in k or 'r$' in k), None)
                        col_cliente = next((v for k, v in cols_limpas.items() if 'cliente' in k or 'nome' in k or 'empresa' in k), "S/N")
                        col_orc = next((v for k, v in cols_limpas.items() if 'orc' in k or 'pedido' in k or 'doc' in k), None)
                        col_parcela = next((v for k, v in cols_limpas.items() if 'parcela' in k), None)
                        col_status = next((v for k, v in cols_limpas.items() if 'obs' in k or 'status' in k or 'situa' in k), None)
                        
                        # Prepara os dados matemáticos
                        df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
                        
                        # Filtro de Pagos
                        if col_status:
                            mask_pago = df[col_status].astype(str).str.lower().str.contains('pago')
                            df_pendente = df[~mask_pago].dropna(subset=[col_data])
                        else:
                            ultima_coluna = df.columns[-1]
                            mask_pago = df[ultima_coluna].astype(str).str.lower().str.contains('pago')
                            df_pendente = df[~mask_pago].dropna(subset=[col_data])
                        
                        hoje = pd.to_datetime('today').normalize()
                        df_vencidos = df_pendente[df_pendente[col_data] < hoje].sort_values(by=col_data)
                        df_a_vencer = df_pendente[df_pendente[col_data] >= hoje].sort_values(by=col_data)
                        
                        # Criação da Planilha Visual (Para exibição perfeita)
                        df_display = df_pendente.copy()
                        
                        # O CÁLCULO AO VIVO DOS DIAS (Substitui as fórmulas engessadas do Excel)
                        df_display['Status Dinâmico (Dias)'] = df_display[col_data].apply(
                            lambda x: "S/D" if pd.isnull(x) else (
                                "⚠️ VENCE HOJE" if (x - hoje).days == 0 
                                else (f"❌ Atrasado há {abs((x - hoje).days)} dias" if (x - hoje).days < 0 
                                else f"✅ Vence em {(x - hoje).days} dias")
                            )
                        )
                        
                        # Remove a coluna de observação velha do Excel para não confundir
                        if col_status and col_status in df_display.columns:
                            df_display = df_display.drop(columns=[col_status])
                        
                        # Formata Datas e Valores exclusivamente para a visualização
                        df_display[col_data] = df_display[col_data].dt.strftime('%d/%m/%Y')
                        df_display[col_valor] = df_display[col_valor].apply(formatar_moeda)
                        
                        tab_venc, tab_dados = st.tabs(["📅 Resumo Financeiro", "📋 Planilha Completa Formatada"])
                        
                        with tab_venc:
                            st.markdown("**Itens já vencidos:**")
                            st.write("")
                            if not df_vencidos.empty:
                                for _, linha in df_vencidos.iterrows():
                                    data_f = linha[col_data].strftime('%d/%m/%Y')
                                    c_nome = linha.get(col_cliente, 'S/N')
                                    t_orc = f", ORÇ: {int(linha[col_orc]) if pd.notnull(linha[col_orc]) else 'S/N'}" if col_orc else ""
                                    t_parc = f", {linha[col_parcela]}" if col_parcela and pd.notnull(linha[col_parcela]) else ""
                                    st.write(f"{c_nome}{t_orc}{t_parc}, {formatar_moeda(linha[col_valor])}, {data_f}")
                                
                                st.write("")
                                st.markdown(f"**Subtotal: {formatar_moeda(df_vencidos[col_valor].sum())};**")
                            else:
                                st.success("Nenhum item vencido.")
                                st.markdown(f"**Subtotal: R$ 0,00;**")
                            
                            st.write("")
                            st.write("")
                            st.markdown(f"**Itens a vencer: {len(df_a_vencer)} (Subtotal: {formatar_moeda(df_a_vencer[col_valor].sum())});**")
                            st.write("")
                            st.write("")
                            st.markdown(f"**Valor total em aberto: {formatar_moeda(df_pendente[col_valor].sum())};**")
                            st.write("")
                            st.write("")
                            
                            if not df_a_vencer.empty:
                                prox = df_a_vencer.iloc[0]
                                st.markdown(f"**Próximo vencimento:** {prox.get(col_cliente, 'S/N')}, {formatar_moeda(prox[col_valor])}, {prox[col_data].strftime('%d/%m/%Y')}")

                        with tab_dados:
                            st.dataframe(df_display, use_container_width=True)
                    
                    else:
                        st.success("🎯 **Objetivo Detectado:** Controle de Patrimônio / Inventário. O sistema está focado em auditar a integridade dos dados, contar peças e identificar lacunas de informação.")
                        
                        df_display = df.copy()
                        # Formata qualquer coluna que pareça data no patrimônio para dd/mm/aaaa
                        for col in df_display.select_dtypes(include=['datetime', 'datetimetz']).columns:
                            df_display[col] = df_display[col].dt.strftime('%d/%m/%Y')
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Total de Itens Cadastrados", len(df))
                        
                        dados_faltantes = df.isnull().sum()
                        colunas_com_falha = dados_faltantes[dados_faltantes > 0]
                        col2.metric("Colunas Incompletas", len(colunas_com_falha))
                        
                        st.write("---")
                        if not colunas_com_falha.empty:
                            st.warning("🚨 **Auditoria: Dados Ausentes Detectados**")
                            for col, qtd in colunas_com_falha.items():
                                st.write(f"- A coluna **'{col}'** está sem informação em **{qtd}** registros.")
                        else:
                            st.success("✅ O patrimônio está com integridade total de dados!")
                        
                        st.write("**Tabela de Controle:**")
                        st.dataframe(df_display, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro na planilha: {e}")

            # --- CASO 2: DOCUMENTOS (WORD OU TXT) ---
            elif extensao in ['docx', 'txt']:
                st.info("🎯 **Objetivo Detectado:** Catálogo / Documentação de Pesquisa. O sistema ativou o motor de busca instantânea para localização de itens e códigos.")
                conteudo = []
                
                if extensao == 'docx':
                    doc = Document(arquivo)
                    conteudo = [p.text for p in doc.paragraphs if p.text.strip() != ""]
                else:
                    conteudo = arquivo.read().decode("utf-8").splitlines()
                
                busca = st.text_input(f"O que deseja filtrar em {arquivo.name}?", placeholder="Digite o código da peça, nome ou marca...")
                
                if busca:
                    resultados = [linha for linha in conteudo if busca.lower() in linha.lower()]
                    if resultados:
                        st.success(f"✅ Encontradas {len(resultados)} correspondências:")
                        for r in resultados:
                            st.write(f"🔹 {r}")
                    else:
                        st.warning("Nenhum item encontrado com esse termo.")
                else:
                    st.write("Digite algo acima para filtrar.")

else:
    st.info("Aguardando o envio de documentos para iniciar as operações.")