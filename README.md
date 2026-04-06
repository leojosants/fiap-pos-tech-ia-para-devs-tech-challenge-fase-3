# 🩺 BioTech IA - Assistente Clínico de Saúde da Mulher
### FIAP | Pós Tech IA para Devs - Tech Challenge Fase 3

Este projeto apresenta um Assistente Clínico Inteligente desenvolvido com foco em **Saúde da Mulher**, utilizando tecnologias de IA generativa de ponta com execução **100% local** para garantir a máxima privacidade dos dados sensíveis (LGPD).

---

## 🚀 Visão Geral
O **BioTech IA** é uma solução orquestrada que guia o profissional de saúde através de uma "Jornada do Atendimento", realizando triagens automáticas, sugerindo exames preventivos baseados no prontuário e garantindo a conformidade ética através de filtros de segurança em tempo real.

### Principais Diferenciais:
- **Orquestração com LangGraph:** Fluxo de decisão não linear que diferencia rotina, urgência e casos especializados.
- **RAG (Retrieval Augmented Generation):** Consulta direta a diretrizes oficiais (INCA/MS/OMS) via FAISS.
- **Privacidade Total (Air-Gapped):** Execução local via Ollama (Llama 3.2), sem envio de dados para a nuvem.
- **Filtro Ético de Prescrição:** Bloqueio automático de tentativas de dosagem ou receitas médicas por IA.

---

## 🛠️ Estrutura do Projeto
```text
├── data/                    # Base de conhecimento (PDFs e Dataset JSON)
│   └── dataset_fine_tuning.json
├── docs/                    # Documentação adicional do projeto
├── knowledge/               # Repositório de informações estruturadas
├── notebook/               # Notebook da Phase 3 (Exploração e Grafo)
├── src/
│   ├── engine/             # Core da IA (LangGraph, Nós e Estados)
│   ├── rag/                # Motor de busca vetorial e processamento de documentos
├── main.py                 # Interface Dashboard (Streamlit)
├── guia_de_testes_biotech.md # Manual com 10 cenários de validação
├── tech_report_notes.md    # Notas técnicas para o relatório PDF
└── README.md
```

---

## ⚙️ Como Executar

### Pré-requisitos
- **Python 3.10+** (Recomendado via `uv`)
- **Ollama** instalado no sistema ([Link para download](https://ollama.com/))

### Passo 1: Configurar os Modelos Locais
No seu terminal, baixe o modelo de linguagem e o de embeddings:
```bash
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

### Passo 2: Clonar o Repositório
```bash
git clone git@github.com:leojosants/fiap-pos-tech-ia-para-devs-tech-challenge-fase-3.git
cd fiap-pos-tech-ia-para-devs-tech-challenge-fase-3
```

### Passo 3: Instalar Dependências
Utilizamos o `uv` para gestão de pacotes rápida e consistente:
```bash
uv sync
```

### Passo 4: Executar a Aplicação (Dashboard)
```bash
uv run streamlit run main.py
```

### Passo 5: Executar o Notebook
Caso queira validar o fluxo via Jupyter Notebook, execute os arquivos dentro da pasta `notebook/`.

---

## 🧪 Cenários de Teste
Para validar a inteligência do sistema, siga o nosso **[Guia de Testes Clínicos](guia_de_testes_biotech.md)**. Nele, detalhamos 10 fluxos críticos, incluindo:
1. Triagem de Gestantes com Sangramento.
2. Acolhimento em casos de Violência Doméstica.
3. Bloqueio de automedicação (Ética).
4. Consulta de protocolos preventivos do INCA.

---

## 🎓 Instituição
**FIAP - Pós Tech IA para Devs**  
**Tech Challenge - Fase 3**  
**Autor:** [leojosants](https://github.com/leojosants)

---
> [!NOTE]
> Este projeto foi desenvolvido como prova de conceito para o uso de Agentes de IA em ambientes clínicos controlados.