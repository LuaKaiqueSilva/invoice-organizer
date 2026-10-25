# Próximas melhorias

## MVP implementado

- Importação local de PDFs com limite de tamanho e validação básica.
- Extração heurística de tipo, emitente/beneficiário, número, datas e valor.
- Banco SQLite, detecção de duplicatas, busca, filtros, download do original e CSV.
- Modo de demonstração com dados fictícios.
- Exemplos sintéticos de nota fiscal, boleto e PDF escaneado.
- OCR local opcional com indicação explícita de que os campos foram reconhecidos por imagem.
- Migração automática do banco para registrar o método de extração.
- Correção manual dos campos e exclusão confirmada de documentos.

## Próximos passos

1. Medir confiança por campo e permitir revisão manual dos dados do OCR.
2. Melhorar a extração com fixtures sintéticas e consentidas, sem guardar documentos financeiros reais no Git.

As extrações são heurísticas e precisam ser verificadas no PDF original.
