# Histórico de alterações

## MVP local

- Dashboard em Streamlit para importar, pesquisar e filtrar notas fiscais e boletos em PDF.
- Extração inicial de metadados de PDFs com texto selecionável.
- Armazenamento local em SQLite com hash de duplicidade e download do original.
- Modo de demonstração e exportação da lista para CSV.

## OCR local e fluxo de revisão

- Adicionados exemplos sintéticos para notas, boletos e uma nota escaneada.
- OCR local opcional para PDFs digitalizados, com aviso sobre revisão manual.
- Banco registra o método de extração e migra automaticamente bancos existentes.
- README ampliado com instalação, teste de OCR e decisões técnicas.
