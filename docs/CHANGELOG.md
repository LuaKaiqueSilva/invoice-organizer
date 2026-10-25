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

## Revisão de extração e empacotamento

- Detecção de rótulos e tipo de documento sem depender de acentos, preservando a grafia original dos nomes.
- Valores monetários exigem centavos; boletos usam dígitos verificadores da linha digitável como complemento.
- Senha de proprietário sem senha de abertura aceita; suporte AES declarado em `pypdf[crypto]`.
- Valores manuais pt-BR validam agrupamento e rejeitam negativos.
- OCR renderiza próximo de 300 dpi, limita a cinco páginas e mostra progresso durante importação.
- Projeto instalado como pacote `invoice_organizer`; entrada Streamlit agora é `app.py`.
