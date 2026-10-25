# Banco de dados

O SQLite local armazena uma linha por PDF importado. O arquivo original fica em `data/documents/` com um nome aleatório; o nome enviado pelo usuário é mantido apenas para exibição.

## Tabela `documents`

- `id`: UUID hexadecimal usado pela aplicação.
- `file_name`: nome original sanitizado para exibição.
- `stored_name`: nome gerado localmente para o arquivo PDF.
- `document_type`: `invoice`, `bank_slip` ou `other`.
- `issuer`, `document_number`, `issue_date`, `due_date`, `amount`: campos extraídos, opcionais.
- `sha256`: hash do arquivo, único para impedir duplicação.
- `created_at`: data/hora local da importação.

A pasta `data/` está no `.gitignore`, pois pode conter documentos financeiros pessoais.
