import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Analizador de Documentos", page_icon="📄", layout="wide")

st.title("📄 ANALIZADOR AVANÇADO DE DOCUMENTOS")
st.write("Anexe uma ou mais planilhas abaixo para gerar análises dinâmicas.")

# ==========================================
# BOTÃO DE UPLOAD MULTIPLO
# ==========================================
# accept_multiple_files=True permite carregar várias planilhas de uma vez
arquivos_enviados = st.file_uploader("Arraste e solte ou clique para procurar", type=["xlsx", "xls", "xlsm"], accept_multiple_files=True)

st.markdown("---")

# ==========================================
# LÓGICA DO MOTOR DE ANÁLISE (O "Falso" IA)
# ==========================================
if arquivos_enviados:
    for arquivo in arquivos_enviados:
        st.success(f"✅ Analisando: **{arquivo.name}**")
        
        try:
            df = pd.read_excel(arquivo)
            
            # Os 5 Botões Interativos (Abas) para navegação sem recarregar a página
            aba1, aba2, aba3, aba4, aba5 = st.tabs([
                "📊 Resumo Geral", 
                "📅 Vencimentos", 
                "🧠 Opinião Analítica", 
                "💡 Ideias de Melhoria", 
                "🎯 Ações Sugeridas"
            ])
            
            with aba1:
                st.write("### Resumo da Estrutura")
                st.info(f"O documento possui {df.shape[0]} linhas preenchidas e {df.shape[1]} colunas.")
                st.write("🔎 **Amostra dos Dados:**")
                st.dataframe(df.head(), use_container_width=True)
                
            with aba2:
                st.write("### Inteligência de Datas e Vencimentos")
                # O robô procura automaticamente colunas que parecem datas
                colunas_data = df.select_dtypes(include=['datetime64', 'datetime']).columns.tolist()
                
                if not colunas_data:
                    st.warning("O robô não encontrou nenhuma coluna formatada como Data/Vencimento nesta planilha.")
                else:
                    hoje = pd.to_datetime('today')
                    for col in colunas_data:
                        vencidos = df[df[col] < hoje].shape[0]
                        vencem_breve = df[(df[col] >= hoje) & (df[col] <= hoje + timedelta(days=30))].shape[0]
                        st.write(f"**Análise da Coluna: {col}**")
                        st.error(f"❌ **{vencidos}** itens já estão vencidos ou com data no passado.")
                        st.warning(f"⚠️ **{vencem_breve}** itens vencem nos próximos 30 dias.")
                        st.success(f"✅ O restante possui prazo estendido.")
                        st.write("---")
                        
            with aba3:
                st.write("### Opinião do Sistema")
                vazios = df.isnull().sum().sum()
                total_celulas = df.shape[0] * df.shape[1]
                percentual_vazio = (vazios / total_celulas) * 100 if total_celulas > 0 else 0
                
                if percentual_vazio > 15:
                    st.warning(f"A planilha apresenta {percentual_vazio:.1f}% de células em branco. Minha opinião técnica é que os dados estão fragmentados, o que pode prejudicar análises cruciais da empresa e causar falhas de interpretação.")
                elif df.shape[0] < 10:
                    st.info("A planilha contém um volume muito baixo de dados. Opino que esta seja apenas uma extração rápida, um rascunho de controle ou um pedido pequeno.")
                else:
                    st.success("A planilha apresenta uma integridade estrutural excelente. O preenchimento está consistente e pronto para decisões estratégicas, financeiras ou logísticas de importação.")
                    
            with aba4:
                st.write("### Ideias de Melhoria na Tabela")
                st.write("- **Padronização:** Recomendo revisar colunas de texto para garantir que descrições e marcas estejam em MAIÚSCULO, conforme os padrões corporativos.")
                if "Unnamed" in str(df.columns):
                    st.error("- **Cabeçalhos:** O robô detectou colunas sem nome. É fundamental renomear a primeira linha no Excel para não perder dados nas buscas.")
                if df.duplicated().sum() > 0:
                    st.warning(f"- **Repetições:** O sistema detectou {df.duplicated().sum()} linhas exatamente iguais (duplicadas). Recomendo a limpeza para não haver cobranças ou pedidos em dobro.")
                else:
                    st.write("- A tabela não apresenta duplicidades críticas. A formatação atual parece viável.")
                    
            with aba5:
                st.write("### Próximos Passos (Plano de Ação)")
                st.write("1. Investigar e cobrar imediatamente os itens pontuados na aba de 'Vencimentos'.")
                st.write("2. Preencher os espaços em branco para garantir que as informações estejam precisas para o faturamento e conferência do almoxarifado.")
                st.write("3. Compartilhar os apontamentos mais urgentes desta análise com os responsáveis da equipe.")
                
        except Exception as e:
            st.error(f"❌ Erro ao tentar ler a planilha {arquivo.name}. Arquivo corrompido ou formato não suportado. Detalhe técnico: {e}")
        
        st.markdown("---")
else:
    st.info("O robô está ocioso. Aguardando o envio de planilhas para iniciar o trabalho.")