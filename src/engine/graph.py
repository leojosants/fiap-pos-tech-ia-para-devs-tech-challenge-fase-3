from langgraph.graph import StateGraph, START, END
from .state import PatientState
from .nodes import *

def compile_biotech_graph(llm, search_func):
    """Compila o grafo do LangGraph com toda a lógica especializada."""
    workflow = StateGraph(PatientState)

    # 1. Adicionando os Nós (com passagem do LLM e buscas injetados)
    workflow.add_node("identificacao", node_identificacao)
    workflow.add_node("analise_clinica", lambda s: node_analise_clinica(llm, s))
    workflow.add_node("prevencao", lambda s: node_prevencao_integracao(llm, search_func, s))
    workflow.add_node("urgencia", lambda s: node_urgencia(llm, search_func, s))
    workflow.add_node("violencia", lambda s: node_violencia(llm, search_func, s))
    workflow.add_node("obstetricia", lambda s: node_obstetricia(llm, search_func, s))
    workflow.add_node("seguranca_etica", node_seguranca_etica)

    # 2. Definição das Edições (Lógica de Roteamento)
    def roteador_principal(state: PatientState):
        relato = state['relato'].lower()
        if any(t in relato for t in ["sangramento", "dor forte", "aguda"]): return "urgencia"
        if any(p in relato for p in ["marido", "agrediu", "medo", "violencia"]): return "violencia"
        if any(o in relato for o in ["grávida", "parto", "bebê", "gestação"]): return "obstetricia"
        return "prevencao"

    # 3. Construção do Caminho
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

    for node in ["urgencia", "violencia", "obstetricia", "prevencao"]:
        workflow.add_edge(node, "seguranca_etica")

    workflow.add_edge("seguranca_etica", END)

    return workflow.compile()
