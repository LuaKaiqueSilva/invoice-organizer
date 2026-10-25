# Arquitetura

```text
Streamlit dashboard
       │
       ▼
DocumentService ── valida tamanho, tipo, hash e coordena armazenamento
       │
       ├── ParserFactory ── pypdf extrai texto; parsers aplicam regras por tipo
       ├── file_utils ───── salva PDF com nome aleatório e permissões locais restritas
       └── DocumentRepository ── SQLite via connection/schema
```

O conteúdo textual extraído não é persistido. A aplicação guarda somente os campos selecionados e o PDF original na máquina local. A extração é heurística, sem OCR ou envio a serviços externos.
