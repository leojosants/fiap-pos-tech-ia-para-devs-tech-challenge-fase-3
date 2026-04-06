from typing import Annotated, TypedDict, List
import operator

class PatientState(TypedDict):
    # Relato original para análise semântica
    relato: str 
    
    # Classificação dinâmica (urgencia, violencia, obstetricia, prevencao)
    categoria: str 
    
    # Classificação de Risco (Verde, Amarelo, Vermelho)
    risco: str 
    
    # Acumulador de exames (usa operator.add para não sobrescrever o histórico)
    exames_sugeridos: Annotated[List[str], operator.add] 
    
    # Sentinela de segurança ética
    protocolo_seguranca: bool 
    
    # Resultado final após auditoria
    resposta_final: str
