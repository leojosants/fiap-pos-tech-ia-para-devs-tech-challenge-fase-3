from typing import Annotated, TypedDict, List
import operator
import datetime
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, START, END

# --- DATASETS ESPECIALIZADOS (Simulação de Bases de Conhecimento do PDF) ---
KNOWLEDGE_BASE = {
    "INCA_MAMOGRAFIA": "Rastreamento bianual para mulheres de 50 a 69 anos. Sinais de alerta: nódulo fixo, pele em casca de laranja.",
    "FEBRASGO_GINECOLOGIA": "O Papanicolau deve ser realizado anualmente. Se dois resultados seguidos forem normais, o intervalo pode ser trienal.",
    "OMS_OBSTETRICIA": "Protocolo de pré-natal: mínimo de 6 consultas, suplementação de Ácido Fólico e Ferro.",
    "PROTOCOLOS_VIOLENCIA": "Protocolo de Segurança: Não confrontar o agressor. Acionar assistência social e rede de proteção de forma sigilosa.",
    "CONTRACEPCAO_FDA": "Em caso de esquecimento da pílula, tomar o comprimido esquecido imediatamente e usar preservativo por 7 dias."
}

# --- ENTIDADES E ESTADO ---
class PatientState(TypedDict):
    relato: str
    categoria: str 
    risco: str 
    exames_sugeridos: Annotated[List[str], operator.add] 
    protocolo_seguranca: bool 
    resposta_final: str

# Banco de dados fictício (Simulação de integração hospitalar)
PRONTUARIO_DB = {
    "Ana Silva": {"nascimento": "1985-05-20", "ultimo_papanicolau": "2020", "ultima_mamografia": "2023"},
    "Maria Oliveira": {"nascimento": "1998-03-12", "ultimo_papanicolau": "2024", "ultima_mamografia": None},
    "Juliana Costa": {"nascimento": "1970-12-05", "ultimo_papanicolau": "2019", "ultima_mamografia": "2021"}
}

modelo_local = OllamaLLM(model="llama3.2:1b")

# --- NÓS DE DECISÃO ---

def node_identificacao(state: PatientState):
    print("--- NÓ DE IDENTIFICAÇÃO ---")
    nome_usuario = state['relato'].split(':')[0].strip()
    dados_paciente = PRONTUARIO_DB.get(nome_usuario)
    exames_atrasados = []
    
    if dados_paciente:
        if "2019" in str(dados_paciente['ultimo_papanicolau']): exames_atrasados.append("Papanicolau")
        if "2021" in str(dados_paciente['ultima_mamografia']): exames_atrasados.append("Mamografia")
        return {"exames_sugeridos": exames_atrasados, "categoria": "identificada"}
    return {"categoria": "nova_paciente"}

def node_analise_clinica(state: PatientState):
    print("--- NÓ DE ANÁLISE CLÍNICA ---")
    relato = state['relato'].lower()
    termos_criticos = ["sangramento", "dor insuportável", "hemorragia", "aguda"]
    
    if any(t in relato for t in termos_criticos):
        return {"risco": "VERMELHO", "categoria": "urgencia"}
    
    # Classificação por Categoria para o Roteador
    if "gravida" in relato or "parto" in relato or "gestacao" in relato:
        return {"categoria": "obstetricia"}
    
    # Padrão de Violência: identificando omissão de agressor (identificar "caí", "bati", etc)
    padroes_violencia = ["caí da escada", "bati na porta", "desastrada", "marido"]
    if any(p in relato for p in padroes_violencia):
        return {"categoria": "violencia"}

    return {"categoria": "prevencao"}

def node_urgencia(state: PatientState):
    print("--- NÓ DE URGÊNCIA ---")
    return {"resposta_final": "ESTADO DE EMERGÊNCIA DETECTADO. Procure um pronto-socorro imediatamente. (Protocolo de Segurança MS)"}

def node_violencia_domestica(state: PatientState):
    print("--- NÓ DE VIOLÊNCIA DOMÉSTICA ---")
    prompt = f"Analise o relato com acolhimento profissional humano, citando a rede de proteção. Fonte: {KNOWLEDGE_BASE['PROTOCOLOS_VIOLENCIA']}"
    resposta = modelo_local.invoke(prompt)
    return {"resposta_final": resposta, "protocolo_seguranca": True}

def node_obstetricia(state: PatientState):
    print("--- NÓ DE OBSTETRÍCIA ---")
    prompt = f"Dê orientações de pré-natal e cuidados preventivos. Fonte: {KNOWLEDGE_BASE['OMS_OBSTETRICIA']}"
    resposta = modelo_local.invoke(prompt)
    return {"resposta_final": resposta}

def node_prevencao(state: PatientState):
    print("--- NÓ DE PREVENÇÃO ---")
    exames = state.get('exames_sugeridos', [])
    prompt = f"Oriente sobre exames pendentes: {exames}. Fonte: {KNOWLEDGE_BASE['FEBRASGO_GINECOLOGIA']}"
    resposta = modelo_local.invoke(prompt)
    return {"resposta_final": resposta}

def node_auto_correcao_seguranca(state: PatientState):
    print("--- NÓ DE AUTO-CORREÇÃO ---")
    resposta = state.get('resposta_final', '')
    if any(v in resposta.lower() for v in ["tome", "receito", "medicação"]):
        return {"resposta_final": "Protocolo de Segurança: Não podemos prescrever medicações via IA. Consulte um médico antes de qualquer conduta."}
    return {"resposta_final": resposta}

# --- ROTEAMENTO ---
def roteador_principal(state: PatientState):
    return state.get("categoria", "prevencao")

# --- CONSTRUÇÃO DO GRAFO ---
workflow = StateGraph(PatientState)

workflow.add_node("identificacao", node_identificacao)
workflow.add_node("analise_clinica", node_analise_clinica)
workflow.add_node("urgencia", node_urgencia)
workflow.add_node("violencia", node_violencia_domestica)
workflow.add_node("obstetricia", node_obstetricia)
workflow.add_node("prevencao", node_prevencao)
workflow.add_node("seguranca", node_auto_correcao_seguranca)

workflow.add_edge(START, "identificacao")
workflow.add_edge("identificacao", "analise_clinica")

workflow.add_conditional_edges(
    "analise_clinica",
    roteador_principal,
    {
        "urgencia": "urgencia",
        "violencia": "violencia",
        "obstetricia": "obstetricia",
        "prevencao": "prevencao"
    }
)

workflow.add_edge("urgencia", "seguranca")
workflow.add_edge("violencia", "seguranca")
workflow.add_edge("obstetricia", "seguranca")
workflow.add_edge("prevencao", "seguranca")
workflow.add_edge("seguranca", END)

app = workflow.compile()
