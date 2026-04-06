# Notas para o Relatório Técnico - BioTech IA (Fase 3)

Este documento detalha as decisões arquiteturais e o nível de fidelidade de cada componente do sistema para fins de avaliação do Tech Challenge.

## 1. Arquitetura de IA (100% Funcional)
- **Orquestração:** LangGraph para controle de fluxo clínico (Nós de Identificação, Análise de Risco, Prevenção, Urgência e Segurança).
- **RAG (Retrieval Augmented Generation):** Motor de busca vetorial FAISS com embeddings `nomic-embed-text` locais.
- **Processamento Local:** Integração real com Ollama rodando o modelo Phi-3.
- **Heurísticas Clínicas:** Lógica de decisão baseada em palavras-chave para triagem de urgência (Protocolos FEBRASGO/INCA).

## 2. Componentes de Interface & Simulação (Mocked)
- **Base de Dados de Pacientes:** Simulação via `PRONTUARIO_DB` (Dicionário Python). Em ambiente de produção, este componente seria substituído por um banco SQL (PostgreSQL) integrado ao PEP (Prontuário Eletrônico do Paciente).
- **Agendamento de Exames:** Simulação de UX. O sistema demonstra o fluxo de agendamento com orientações clínicas (ex: preparo para Papanicolau), mas não possui integração com APIs reais de hospitais.
- **Persistência de Consulta:** O botão "Finalizar Consulta" demonstra o fluxo de encerramento e auditoria, mas a gravação física em banco de dados persistente foi omitida para simplificar a execução 100% local exigida pelo desafio.

## 3. Conformidade e Segurança
- **Privacidade (LGPD):** O sistema opera em modo *Air-Gapped* (Zero tráfego de dados para a internet), sendo ideal para ambientes hospitalares restritos.
- **Segurança Ética:** Implementação do nó `node_seguranca` que audita alucinações da IA e bloqueia diagnósticos ou prescrições diretas sem supervisão médica.

---
> [!TIP]
> Estas notas servem de base para a justificativa de pontos no Tech Challenge, provando a complexidade do Grafo e a viabilidade do produto.
