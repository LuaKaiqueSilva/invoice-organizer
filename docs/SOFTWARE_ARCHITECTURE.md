# Arquitetura

```text
Streamlit dashboard
       │
       ▼
DocumentService ── valida tamanho, tipo, hash e coordena armazenamento
       │
       ├── ParserFactory ── pypdf extrai texto; OCR local opcional lê PDFs escaneados
       │                    parsers aplicam regras por tipo
       ├── file_utils ───── salva PDF com nome aleatório e permissões locais restritas
       └── DocumentRepository ── SQLite via connection/schema
```

O conteúdo textual extraído não é persistido. A aplicação guarda os campos selecionados, o método de extração e o PDF original na máquina local. O OCR opcional usa Tesseract e renderização via pypdfium2; nenhum conteúdo é enviado a serviços externos. A precisão depende do layout e da qualidade da imagem.
