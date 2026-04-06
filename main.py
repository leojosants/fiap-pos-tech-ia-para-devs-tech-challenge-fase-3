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
    .stSecondaryBlock { 
        background-color: rgba(255, 255, 255, 0.03); 
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px; 
        padding: 20px; 
    }
    .risk-badge { 
        padding: 12px 20px; 
        border-radius: 12px; 
        font-weight: 800; 
        text-align: center; 
        margin-bottom: 20px; 
        text-transform: uppercase;
        letter-spacing: 1.5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .risk-VERMELHO { background: linear-gradient(135deg, #ff4b4b, #990000); color: white; }
    .risk-AMARELO { background: linear-gradient(135deg, #ffa500, #cc8400); color: black; }
    .risk-VERDE { background: linear-gradient(135deg, #28a745, #1a632a); color: white; }
    
    .activation-card {
        text-align: center;
        padding: 60px;
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        margin: 50px auto;
        max-width: 800px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_patient" not in st.session_state:
    st.session_state.current_patient = {"nome": "Nenhuma", "risco": "PENDENTE", "exames": []}
if "engines_ready" not in st.session_state:
    st.session_state.engines_ready = False
if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
if "consultation_active" not in st.session_state:
    st.session_state.consultation_active = False

# --- CACHING DOS MOTORES ---
@st.cache_resource
def get_ai_engines():
    # Trocado para llama3.2:1b por ser mais leve e rápido em CPUs/iGPUs
    llm = OllamaLLM(model="llama3.2:1b", temperature=0)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    retriever, knowledge, is_vector = get_rag_engine(embeddings)
    return llm, retriever, knowledge, is_vector

@st.cache_resource
def get_compiled_graph(_llm, _search_func):
    return compile_biotech_graph(_llm, _search_func)

def initialize_engines():
    with st.status("🚀 Otimizando Motores de IA...", expanded=True) as status:
        llm, retriever, knowledge, is_vector = get_ai_engines()
        def search_wrapper(query):
            if is_vector:
                try:
                    res = retriever.invoke(query)
                    return res[0].page_content if res else buscar_diretriz_manual(query, knowledge)
                except:
                    return buscar_diretriz_manual(query, knowledge)
            return buscar_diretriz_manual(query, knowledge)
        graph_app = get_compiled_graph(llm, search_wrapper)
        st.session_state.graph_app = graph_app
        st.session_state.engines_ready = True
        status.update(label="✅ Sistema Pronto!", state="complete", expanded=False)

# --- MODAIS ---
@st.dialog("Simulação de Agendamento")
def agendamento_dialog(exame, paciente):
    st.markdown(f"### 📋 Detalhes do Agendamento")
    st.info(f"**Paciente:** {paciente['nome']}")
    st.write(f"**Exame:** {exame} | **Data:** 14/04/2026")
    if st.button("CONFIRMAR AGENDAMENTO", type="primary", use_container_width=True):
        st.toast(f"✅ Agendamento de {exame} realizado!")
        st.rerun()

@st.dialog("🏁 Finalizar Atendimento")
def finalizar_consulta_dialog():
    st.warning("⚠️ **Atenção:** Deseja realmente encerrar a consulta e salvar o relatório?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("SIM, FINALIZAR", type="primary", use_container_width=True):
            st.toast("✅ Consulta finalizada!")
            st.session_state.messages = []
            st.session_state.consultation_active = False
            st.session_state.current_patient = {"nome": "Nenhuma", "risco": "PENDENTE", "exames": []}
            st.rerun()
    with col2:
        if st.button("CANCELAR", use_container_width=True):
            st.rerun()

# --- SIDEBAR (VISÍVEL APENAS QUANDO PRONTO) ---
with st.sidebar:
    st.title("🩺 BioTech IA")
    st.markdown("---")
    
    if not st.session_state.engines_ready:
        st.warning("⚠️ Sistema Offline. Ative os motores na tela principal.")
    else:
        st.success("🟢 Motores de IA: ONLINE")
        st.markdown("---")
        st.subheader("👤 Gestão de Paciente")
        lista_pacientes = ["Selecione uma paciente", "Ana Silva", "Maria Oliveira", "Juliana Costa"]
        # Bloqueia o seletor durante o atendimento ativo para evitar erros
        paciente_selecionada = st.selectbox(
            "Buscar no Prontuário:", 
            lista_pacientes, 
            index=0, 
            disabled=st.session_state.consultation_active
        )
        
        if st.session_state.consultation_active:
            st.info("💡 Finalize o atendimento atual para trocar de paciente.")
        
        if paciente_selecionada != "Selecione uma paciente" and not st.session_state.consultation_active:
            if st.session_state.current_patient['nome'] != paciente_selecionada:
                st.session_state.current_patient.update({"nome": paciente_selecionada, "risco": "PENDENTE", "exames": []})
                st.session_state.messages = []
                st.session_state.consultation_active = False
                st.rerun()
        
        risco = st.session_state.current_patient['risco']
        if risco != "PENDENTE":
            st.markdown(f'<div class="risk-badge risk-{risco}">Classificação: {risco}</div>', unsafe_allow_html=True)
        
        if st.session_state.current_patient['exames']:
            st.subheader("📋 Ações Clínicas")
            for exame in st.session_state.current_patient['exames']:
                if st.button(f"🗓️ Agendar {exame}", use_container_width=True, key=f"btn_{exame}"):
                    agendamento_dialog(exame, st.session_state.current_patient)
                
        st.markdown("---")
        # Só exibe o botão de finalizar se houver um atendimento em curso
        if st.session_state.consultation_active:
            if st.button("🏁 FINALIZAR ATENDIMENTO", type="primary", use_container_width=True):
                finalizar_consulta_dialog()

# --- ÁREA PRINCIPAL: ESTADOS DE FLUXO ---

# ESTADO 1: SISTEMA OFFLINE
if not st.session_state.engines_ready:
    st.markdown("""
        <div class="activation-card">
            <h1>🚀 BioTech IA</h1>
            <p style="font-size: 1.2rem; color: #888; margin-bottom: 30px;">
                Bem-vindo ao Sistema de Inteligência Clínica para Saúde da Mulher.<br>
                Para iniciar, ative os motores de processamento local (Ollama/Phi-3).
            </p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🔴 ATIVAR MOTORES DE INTELIGÊNCIA CLÍNICA", use_container_width=True, type="primary"):
        initialize_engines()
        st.rerun()

# ESTADO 2: SISTEMA ONLINE, MAS SEM PACIENTE SELECIONADA
elif st.session_state.current_patient['nome'] in ["Nenhuma", "Selecione uma paciente"]:
    st.markdown("""
        <div style='text-align: center; padding-top: 100px;'>
            <h1 style="font-size: 4rem;">👈</h1>
            <h1>Motores Ativados!</h1>
            <p style="font-size: 1.2rem; color: #888;">Por favor, selecione uma paciente na barra lateral para iniciar o atendimento.</p>
        </div>
    """, unsafe_allow_html=True)

# ESTADO 3: PERFIL CLÍNICO DA PACIENTE (PRÉ-ATENDIMENTO)
elif not st.session_state.consultation_active:
    st.markdown(f"### 🩺 Perfil Clínico: {st.session_state.current_patient['nome']}")
    dados = PRONTUARIO_DB.get(st.session_state.current_patient['nome'], {})
    nasc = dados.get('nascimento', '1990-01-01')
    idade = 2026 - int(nasc.split('-')[0])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Idade", f"{idade} anos")
    col2.metric("Último Papanicolau", dados.get('ultimo_papanicolau', 'N/D'))
    col3.metric("Última Mamografia", dados.get('ultima_mamografia', 'N/D'))
    st.markdown("---")
    
    if st.button("🚀 INICIAR ATENDIMENTO AGORA", use_container_width=True, type="primary"):
        st.session_state.consultation_active = True
        st.session_state.processing = True
        paciente_nome = st.session_state.current_patient['nome']
        st.session_state.last_prompt = f"{paciente_nome}: Por favor, inicie meu atendimento me saudando."
        st.rerun()

# ESTADO 4: ATENDIMENTO ATIVO (CHAT)
else:
    st.markdown(f"### 💬 Atendimento: {st.session_state.current_patient['nome']}")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Digite aqui...", disabled=st.session_state.processing):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.last_prompt = prompt 
        st.session_state.processing = True
        st.rerun()

    if st.session_state.processing and st.session_state.last_prompt:
        with st.chat_message("assistant"):
            with st.spinner("Analisando relato clínico..."):
                try:
                    res = st.session_state.graph_app.invoke({"relato": st.session_state.last_prompt})
                    st.session_state.current_patient.update({"risco": res.get("risco", "VERDE"), "exames": res.get("exames_sugeridos", [])})
                    st.markdown(res["resposta_final"])
                    st.session_state.messages.append({"role": "assistant", "content": res["resposta_final"]})
                except Exception as e:
                    st.error(f"Erro IA: {str(e)}")
        st.session_state.processing = False
        st.session_state.last_prompt = None
        st.rerun()
