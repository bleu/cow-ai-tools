# op_brains.optimism — Optimism project

Todo o código **específico do projeto Optimism** fica aqui:

- **documents.py** — estratégias para governance docs, forum threads e summaries (FragmentsProcessingStrategy, SummaryProcessingStrategy, ForumPostsProcessingStrategy)

Uso: defina `PROJECT=optimism` ou deixe sem definir. O `documents/__init__.py` do op_brains importa `chat_sources` daqui quando o projeto ativo é Optimism.

`op_data` e o summarizer importam de `op_brains.documents.optimism` (re-export deste módulo).
