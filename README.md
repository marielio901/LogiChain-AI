# LogiChain AI

Sistema CLM completo com **Streamlit + SQLite + ReportLab** para criação, gestão, análise e consulta inteligente de contratos.

## Funcionalidades
- Dashboard com KPIs financeiros, prazo, compliance, operacional, fornecedor, jurídico, CLM, estratégicos e avançados
- Gestão de contratos com Kanban (fluxo de status) e Tabela com filtros/ordenação/ações
- Novo Contrato com formulário completo, validações e geração de PDF profissional
- Agente de IA para perguntas sobre contratos e carteira inteira com dados do SQLite
- Auditoria de eventos (status, edição, PDF, aditivos, ocorrências)

## Estrutura de pastas
```text
.
├── app.py
├── db/
│   ├── connection.py
│   └── migrations.py
├── models/
│   └── contract.py
├── services/
│   ├── ai_agent.py
│   ├── contract_service.py
│   ├── kpi_service.py
│   └── pdf_service.py
├── ui/
│   └── pages/
│       ├── ai_agent_page.py
│       ├── contracts.py
│       ├── dashboard.py
│       ├── info.py
│       └── new_contract.py
├── utils/
│   ├── helpers.py
│   └── validators.py
├── scripts/
│   └── init_db.py
└── storage/
    └── pdfs/
```

## Pré-requisitos
- Python 3.10+

## Instalação
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Inicializar banco
```bash
python scripts/init_db.py
```

## Rodar aplicação
```bash
streamlit run app.py
```

## Regras de negócio implementadas
- Fluxo permitido: `Gerado -> Assinado -> Protocolado -> Em vigor -> Finalizado`
- Sem pular status (exceto `admin override` na Tabela)
- Contratos finalizados saem do Kanban e permanecem na Tabela
- Validação de datas (`start_date <= end_date`)
- Toda alteração relevante gera evento de auditoria
- PDF pode ser regenerado e evento é registrado

## Definição de pronto coberta
- Criar contrato, salvar no SQLite, gerar PDF e baixar
- Mover status no Kanban até Finalizado (e remover do Kanban)
- Ver/filtar/ordenar contratos na Tabela
- Dashboard com KPIs calculados do banco
- Agente IA responde com consultas fundamentadas no SQLite

## Prints
- Dashboard: `Dashboard` na sidebar
- Kanban/Tabela: `Gestão de Contratos`
- Formulário: `Novo Contrato`
- Chat IA: `Agente de IA`

