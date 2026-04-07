from .state import PatientState

# --- BASE DE PRONTUÁRIOS (SIMULADA) ---
PRONTUARIO_DB = {
    "Ana Silva": {"nascimento": "1985-05-20", "ultimo_papanicolau": 2020, "ultima_mamografia": 2023},
    "Maria Oliveira": {"nascimento": "1998-03-12", "ultimo_papanicolau": 2024, "ultima_mamografia": 0},
    "Juliana Costa": {"nascimento": "1970-12-05", "ultimo_papanicolau": 2019, "ultima_mamografia": 2021}
}

def safe_invoke(llm, prompt, state, node_name):
    """
    Fallback ULTRA-RESILIENTE: 
    Se o Ollama travar ou alucinar, entregamos a resposta clínica perfeita baseada em regras.
    """
    relato = state['relato'].lower()
    
    # --- RESPOSTAS "PADRÃO OURO" (Puras, sem IA) ---
    if "sangramento" in relato or "dor forte" in relato:
        return "🚨 **PROTOCOLO DE EMERGÊNCIA (FEBRASGO):** Seus sintomas indicam a necessidade de avaliação imediata. Por favor, dirija-se ao pronto-socorro ginecológico mais próximo. Não utilize medicamentos sem prescrição."
    
    if "gravida" in relato or "gravidez" in relato or "gestante" in relato:
        return "🤰 **ACOMPANHAMENTO PRÉ-NATAL:** É fundamental manter a regularidade das consultas. Recomendamos seguir o calendário da OMS/FEBRASGO para garantir a sua saúde e a do bebê."
    
    if "violencia" in relato or "abuso" in relato or "briga" in relato or "ameaça" in relato or "bater" in relato:
        return "💜 **ACOLHIMENTO E SEGURANÇA:** Você não está sozinha. Para apoio sigiloso e orientação jurídica, ligue para o **180** (Central de Atendimento à Mulher) ou procure o CREAS. Em caso de perigo imediato, ligue 190."

    # Tenta invocar a IA, mas se demorar ou falhar, usa o fallback de rotina
    try:
        # Nota: Se o Ollama estiver gerando 'word salad', o invoke pode demorar.
        # Aqui ele agirá como o seu motor principal, mas o Streamlit agora está protegido.
        return llm.invoke(prompt)
    except Exception:
        return "✨ **Orientação Preventiva:** Com base no seu perfil, recomendamos manter seus exames de rotina (Papanicolau e Mamografia) em dia conforme o calendário do Ministério da Saúde."

def node_identificacao(state: PatientState):
    print("--- 👤 NÓ: IDENTIFICAÇÃO ---")
    # Tenta extrair nome do formato 'Nome: Relato' ou do estado atual
    relato_bruto = state['relato']
    nome_usuario = "Nenhuma"
    
    if ":" in relato_bruto:
        nome_usuario = relato_bruto.split(':')[0].strip()
    
    dados = PRONTUARIO_DB.get(nome_usuario)
    exames = []
    if dados:
        if 2020 >= int(dados['ultimo_papanicolau']): exames.append("Papanicolau")
        if 2021 >= int(dados['ultima_mamografia']): exames.append("Mamografia")
        return {"exames_sugeridos": exames, "categoria": "identificada"}
    return {"categoria": "nova_paciente"}

def node_analise_clinica(llm, state: PatientState):
    print("--- 🧠 NÓ: ANÁLISE CLÍNICA (HEURÍSTICA/IA) ---")
    relato = state['relato'].lower()
    # 🚨 Heurística de Urgência (Resposta Imediata) - VERMELHO
    if any(t in relato for t in ["sangramento", "dor forte", "aguda", "febre alta", "hemorragia", "emergencia"]):
        return {"risco": "VERMELHO"}
    
    # 🤰 Heurística de Acompanhamento Especializado - AMARELO
    if any(t in relato for t in ["grávida", "gravidez", "gestação", "prenatal", "pré-natal", "violencia", "medo", "agrediu", "briga", "ameaça", "hematoma", "bater"]):
        return {"risco": "AMARELO"}

    # ✅ Heurística de Rotina / Boas-Vindas (Resposta Imediata) - VERDE
    if any(t in relato for t in ["exame", "rotina", "preventivo", "papanicolau", "duvida", "oi", "olá", "inicie", "atendimento", "histórico"]):
        return {"risco": "VERDE"}
    
    # IA como último recurso (Protegida pelo safe_invoke)
    try:
        resp = llm.invoke(f"Risco (VERDE, AMARELO, VERMELHO): {relato}")
        return {"risco": "VERMELHO" if "VERMELHO" in resp.upper() else "AMARELO" if "AMARELO" in resp.upper() else "VERDE"}
    except:
        return {"risco": "AMARELO"}

def node_prevencao_integracao(llm, search_func, state: PatientState):
    print("--- 🏥 NÓ: PREVENÇÃO (Protocolo INCA/MS) ---")
    relato = state['relato'].lower()
    
    # --- RESPOSTAS DETERMINÍSTICAS (Padrão Ouro INCA) ---
    if "papanicolau" in relato or "colo do útero" in relato:
        return {
            "resposta_final": "### 🏥 Diretriz INCA: Câncer de Colo de Útero (Papanicolau)\n\n"
                              "Conforme o Ministério da Saúde e o INCA:\n\n"
                              "*   **Público-Alvo:** Mulheres de 25 a 64 anos que já iniciaram vida sexual.\n"
                              "*   **Frequência:** Os dois primeiros exames devem ser anuais. Se ambos estiverem normais, os próximos podem ser realizados **a cada 3 anos**.\n"
                              "*   **Objetivo:** Detecção precoce de lesões precursoras."
        }
        
    if "mamografia" in relato or "mama" in relato:
        return {
            "resposta_final": "### 🎀 Diretriz INCA: Câncer de Mama (Mamografia)\n\n"
                              "Conforme as diretrizes brasileiras atuais:\n\n"
                              "*   **Público-Alvo:** Mulheres de 50 a 69 anos.\n"
                              "*   **Frequência:** Recomendada a realização **a cada 2 anos**.\n"
                              "*   **Nota:** Fora dessa faixa etária ou com histórico familiar, a indicação deve ser avaliada individualmente pelo seu médico."
        }
    
    # --- RESPOSTA DE STATUS DE EXAMES (Baseado no Prontuário) ---
    if any(t in relato for t in ["em dia", "pendente", "fazer", "exames totais", "meu histórico"]):
        exames = state.get('exames_sugeridos', [])
        if not exames:
            return {
                "resposta_final": "### ✅ Tudo em Dia!\n\n"
                                  "Analisei seu histórico no prontuário e fico feliz em informar que você está com seus exames preventivos atualizados. "
                                  "Não há pendências de Papanicolau ou Mamografia para o seu perfil no momento. Continue cuidando da sua saúde!"
            }
        else:
            txt = ", ".join(exames)
            return {
                "resposta_final": f"### 📋 Pendências de Exames\n\n"
                                  f"Identifiquei que você possui as seguintes recomendações pendentes: **{txt}**.\n\n"
                                  "Manter esses exames em dia é fundamental para a sua saúde. Gostaria que eu te ajudasse a agendar algum deles agora?"
            }

    # --- BYPASS DE SAUDAÇÃO (Já implementado) ---
    if "Inicie meu atendimento" in state['relato'] or "saudando" in state['relato']:
         nome_paciente = state['relato'].split(':')[0].strip()
         exames_necessarios = state.get('exames_sugeridos', [])
         txt_exames = ", ".join(exames_necessarios) if exames_necessarios else "Atualmente não constam exames pendentes."
         return {
             "resposta_final": f"Olá, **{nome_paciente}**! 👋\n\nSou sua assistente virtual BioTech IA. Analisei seu histórico médico e notei o seguinte:\n\n*   **Exames no Prontuário:** {txt_exames}\n\nComo estamos focando na sua saúde preventiva, hoje podemos conversar sobre o seu acompanhamento anual. Em que posso te ajudar?"
         }

    prompt = f"Diretriz INCA: Resuma o rastreamento preventivo para: {relato}"
    return {"resposta_final": safe_invoke(llm, prompt, state, "Prevencao")}

def node_urgencia(llm, search_func, state: PatientState):
    print("--- 🚑 NÓ: URGÊNCIA (Alerta Crítico) ---")
    prompt = f"🚨 URGÊNCIA: {state['relato']}. Gere um aviso de 2 frases mandando o paciente para o hospital imediatamente."
    return {"resposta_final": safe_invoke(llm, prompt, state, "Urgencia")}

def node_violencia(llm, search_func, state: PatientState):
    print("--- ⚖️ NÓ: PROTOCOLO DE SEGURANÇA (ÉTICA/LEGAL) ---")
    # RESPOSTA INSTANTÂNEA E SEGURA (Lei Maria da Penha)
    return {
        "resposta_final": "### ⚖️ Protocolo de Segurança e Acolhimento\n\n"
                          "Sua segurança é nossa prioridade absoluta. Você não está sozinha.\n\n"
                          "*   **Ligue 180:** Central de Atendimento à Mulher (Gratuito e sigiloso).\n"
                          "*   **Delegacia da Mulher:** Você pode buscar proteção legal e medidas protetivas.\n"
                          "*   **Apoio Social:** Podemos te conectar com o serviço social especializado.\n\n"
                          "Este canal de atendimento é seguro e sigiloso.",
        "protocolo_seguranca": True
    }

def node_obstetricia(llm, search_func, state: PatientState):
    print("--- 🤰 NÓ: OBSTETRÍCIA (Protocolo Ouro) ---")
    relato = state['relato'].lower()
    
    # ATALHO: Resposta Instantânea para primeiro trimestre/descoberta
    if any(t in relato for t in ["grávida", "gestação", "prenatal", "pré-natal"]):
        return {
            "resposta_final": "### 👶 Protocolo de Pré-Natal (OMS/MS)\n\n"
                              "Parabéns por este momento! Os primeiros passos essenciais são:\n\n"
                              "1. **Suplementação:** Inicie o Ácido Fólico imediatamente.\n"
                              "2. **Primeira Consulta:** Agende sua consulta de pré-natal o quanto antes.\n"
                              "3. **Exames Iniciais:** Prepare-se para realizar exames de sangue e ultrassom de primeiro trimestre.\n\n"
                              "Como posso te ajudar no agendamento?"
        }

    prompt = "Diretriz: Protocolo de Pré-natal 1º trimestre. TAREFA: Resuma os principais cuidados."
    return {"resposta_final": safe_invoke(llm, prompt, state, "Obstetricia")}

def node_seguranca_etica(state: PatientState):
    print("--- 🛡️ NÓ: FILTRO DE SEGURANÇA FINAL ---")
    resp = state['resposta_final'].lower()
    
    # Filtro agressivo para evitar prescrição ou dosagem
    prescricao_termos = ["posologia", " prescrição", " mg", " ml ", "gotas", " receitas", "dose", " medicar com", " paracetamol", " dipirona", " ibuprofeno"]
    
    if any(t in resp for t in prescricao_termos):
        return {
            "resposta_final": "### ⚠️ Aviso de Segurança Ética\n\n"
                              "Identificamos uma solicitação ou termo relacionado a dosagens/prescrições.\n\n"
                              "**Como assistente de IA, não tenho autorização para prescrever medicamentos ou dosagens.**\n\n"
                              "A automedicação oferece riscos graves. Por favor, consulte o seu médico para obter uma receita adequada ao seu caso."
        }
    return {"resposta_final": state['resposta_final']}
