from .state import PatientState

# --- BASE DE PRONTUÁRIOS (SIMULADA) ---
PRONTUARIO_DB = {
    "Ana Silva": {"nascimento": "1985-05-20", "ultimo_papanicolau": 2020, "ultima_mamografia": 2023},
    "Maria Oliveira": {"nascimento": "1998-03-12", "ultimo_papanicolau": 2024, "ultima_mamografia": 0},
    "Juliana Costa": {"nascimento": "1970-12-05", "ultimo_papanicolau": 2019, "ultima_mamografia": 2021}
}

def safe_invoke(llm, prompt, state, node_name):
    """Fallback Resiliente para falhas do Ollama."""
    try:
        return llm.invoke(prompt)
    except Exception as e:
        relato = state['relato'].lower()
        if "sangramento" in relato: return "🚨 Procure EMERGÊNCIA imediatamente (Protocolo FEBRASGO)."
        if "grávida" in relato: return "🤰 Siga as suplementações do pré-natal (Protocolo OMS)."
        if "violencia" in relato or "marido" in relato: return "💜 Procure ajuda sigilosa no Ligue 180 (Lei Maria da Penha)."
        if "papanicolau" in relato or "mamografia" in relato: return "✅ Recomendamos agendar seus exames preventivos (Protocolo INCA)."
        return "Orientação BioTech: É importante agendar uma avaliação clínica presencial."

def node_identificacao(state: PatientState):
    nome_usuario = state['relato'].split(':')[0].strip()
    dados = PRONTUARIO_DB.get(nome_usuario)
    exames = []
    if dados:
        if 2020 >= int(dados['ultimo_papanicolau']): exames.append("Papanicolau")
        if 2021 >= int(dados['ultima_mamografia']): exames.append("Mamografia")
        return {"exames_sugeridos": exames, "categoria": "identificada"}
    return {"categoria": "nova_paciente"}

def node_analise_clinica(llm, state: PatientState):
    relato = state['relato'].lower()
    if any(t in relato for t in ["sangramento", "dor forte", "aguda"]): return {"risco": "VERMELHO"}
    try:
        resp = llm.invoke(f"Responda APENAS 'VERDE', 'AMARELO' ou 'VERMELHO' para: {relato}")
        return {"risco": "VERMELHO" if "VERMELHO" in resp.upper() else "AMARELO" if "AMARELO" in resp.upper() else "VERDE"}
    except:
        return {"risco": "AMARELO"}

def node_prevencao_integracao(llm, search_func, state: PatientState):
    diretriz = search_func("rastreamento mamografia papanicolau inca")
    prompt = f"Relato: {state['relato']}. Use esta diretriz: {diretriz}. Seja acolhedora e cite a FONTE."
    return {"resposta_final": safe_invoke(llm, prompt, state, "Prevencao")}

def node_urgencia(llm, search_func, state: PatientState):
    diretriz = search_func("urgencia sinais alerta gravidez febrasgo")
    prompt = f"Urgência: {state['relato']}. Diretriz oficial: {diretriz}. Oriente socorro imediato."
    return {"resposta_final": safe_invoke(llm, prompt, state, "Urgencia")}

def node_violencia_domestica(llm, search_func, state: PatientState):
    diretriz = search_func("violencia domestica maria da penha acolhimento")
    prompt = f"Acolhimento: {state['relato']}. Protocolo ético: {diretriz}. Cite o Ligue 180."
    return {"resposta_final": safe_invoke(llm, prompt, state, "Violencia"), "protocolo_seguranca": True}

def node_obstetricia(llm, search_func, state: PatientState):
    diretriz = search_func("pre natal consultas febrasgo oms")
    prompt = f"Orientação Gestacional: {state['relato']}. Base: {diretriz}. Cite a FONTE oficial."
    return {"resposta_final": safe_invoke(llm, prompt, state, "Obstetricia")}

def node_seguranca(state: PatientState):
    res = state.get('resposta_final', '')
    proibidos = ["tome", "receito", "medicação", "diagnóstico é", "dosagem", "remédio"]
    if any(p in res.lower() for p in proibidos):
        return {"resposta_final": "⚠️ Protocolo Ético: Identificamos termos de prescrição. Nossa IA não substitui a consulta médica. Procure avaliação presencial."}
    return {"resposta_final": res}
