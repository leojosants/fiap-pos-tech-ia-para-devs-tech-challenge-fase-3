import streamlit as st
import time
import os
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from src.engine.graph import compile_biotech_graph
from src.rag.core import get_rag_engine, buscar_diretriz_manual
from src.engine.nodes import PRONTUARIO_DB

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BioTech IA - Dashboard", layout="wide", page_icon="🩺")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stSecondaryBlock { background-color: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 20px; }
    .risk-badge { padding: 10px 20px; border-radius: 10px; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .risk-VERMELHO { background-color: #ff4b4b; color: white; }
    .risk-AMARELO { background-color: #ffa500; color: black; }
    .risk-VERDE { background-color: #28a745; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_patient" not in st.session_state:
    st.session_state.current_patient = {"nome": "Nenhuma", "risco": "VERDE", "exames": []}
if "engines_ready" not in st.session_state:
    st.session_state.engines_ready = False

# --- FUNÇÃO DE CARREGAMENTO SOB DEMANDA ---
def initialize_engines():
    with st.status("🚀 Iniciando Motores de IA (Phi-3)...", expanded=True) as status:
        st.write("Conectando ao Ollama...")
        llm = OllamaLLM(model="phi3")
        
        st.write("Carregando Base de Conhecimento (RAG)...")
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        retriever, knowledge, is_vector = get_rag_engine(embeddings)
        
        def search_wrapper(query):
            if is_vector:
                try:
                    res = retriever.invoke(query)
                    return res[0].page_content if res else buscar_diretriz_manual(query, knowledge)
                except:
                    return buscar_diretriz_manual(query, knowledge)
            return buscar_diretriz_manual(query, knowledge)
        
        st.write("Compilando Grafo de Decisão...")
        graph_app = compile_biotech_graph(llm, search_wrapper)
        
        st.session_state.graph_app = graph_app
        st.session_state.engines_ready = True
        status.update(label="✅ IA Pronta para Uso!", state="complete", expanded=False)

# --- SIDEBAR: PAINEL DE CONTROLE CLÍNICO ---
with st.sidebar:
    st.title("🩺 BioTech IA")
    st.markdown("---")
    
    if not st.session_state.engines_ready:
        if st.button("🔴 ATIVAR MOTORES DE IA", use_container_width=True):
            initialize_engines()
            st.rerun()
    else:
        st.success("🟢 Sistema Online")
    
    st.markdown("---")
    st.subheader("👤 Paciente Atual")
    st.info(f"**Nome:** {st.session_state.current_patient['nome']}")
    risco = st.session_state.current_patient['risco']
    st.markdown(f'<div class="risk-badge risk-{risco}">RISCO: {risco}</div>', unsafe_allow_html=True)
    
    if st.session_state.current_patient['exames']:
        st.subheader("📋 Ações e Exames")
        for exame in st.session_state.current_patient['exames']:
            st.checkbox(f"Agendar {exame}", value=False)
            
    if st.button("Limpar Atendimento"):
        st.session_state.messages = []
        st.session_state.current_patient = {"nome": "Nenhuma", "risco": "VERDE", "exames": []}
        st.rerun()

# --- CHAT PRINCIPAL ---
st.title("Assistente Clínico Especializado")
st.caption("Fase 3 Tech Challenge - Saúde da Mulher")

if not st.session_state.engines_ready:
    st.warning("⚠️ Clique no botão 'ATIVAR MOTORES DE IA' na barra lateral para começar.")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Relato da paciente..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Processando..."):
            initial_state = {
                "relato": prompt, "exames_sugeridos": [],
                "protocolo_seguranca": False, "resposta_final": "",
                "categoria": "identificada", "risco": "VERDE"
            }
            result = st.session_state.graph_app.invoke(initial_state)
            
            # Atualizar Sidebar
            nome = prompt.split(':')[0] if ":" in prompt else "Não Identificada"
            st.session_state.current_patient.update({
                "nome": nome, "risco": result.get("risco", "VERDE"),
                "exames": result.get("exames_sugeridos", [])
            })
            
            st.session_state.messages.append({"role": "assistant", "content": result["resposta_final"]})
            st.rerun()
