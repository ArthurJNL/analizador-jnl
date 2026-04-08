import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador de Documentos", page_icon="📄", layout="centered")

st.title("📄 ANALIZADOR DE DOCUMENTOS")
st.write("Anexe a planilha abaixo para gerar um resumo instantâneo.")

# ==========================================
# BOTÃO DE UPLOAD (A MÁGICA DA NUVEM)
# ==========================================
# Permite que o usuário faça upload direto do PC dele
arquivo_enviado = st.file_uploader("Arraste e solte ou clique para procurar no seu computador", type=["xlsx", "xls", "xlsm"])

st.markdown("---")

# ==========================================
# LÓGICA DE LEITURA E RESUMO
# ==========================================
if arquivo_enviado is not None:
    # Se o usuário anexou um arquivo, o robô começa a trabalhar
    st.success(f"✅ Arquivo recebido: **{arquivo_enviado.name}**")
    
    with st.spinner("Analisando os dados..."):
        try:
            # Lê o arquivo diretamente da memória da nuvem
            df = pd.read_excel(arquivo_enviado)
            
            # Caixa de Resumo Destacada
            st.info(f"📊 **Resumo Rápido:** A planilha possui {df.shape[0]} linhas preenchidas e {df.shape[1]} colunas.")
            
            # Mostra as colunas disponíveis
            st.write(f"📋 **Colunas identificadas:** {', '.join(df.columns.tolist())}")
            
            # Mostra uma amostra dos dados (apenas leitura)
            st.write("🔎 **Amostra dos Dados (Primeiras 5 linhas):**")
            st.dataframe(df.head(), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erro ao tentar ler a planilha. Certifique-se de que é um arquivo Excel válido. (Erro: {e})")
else:
    st.info("Aguardando o envio de um arquivo para iniciar a análise.")

# Rodapé simples
st.markdown("---")
st.caption("Desenvolvido para JNL Importadora | Sistema em Nuvem Independente")