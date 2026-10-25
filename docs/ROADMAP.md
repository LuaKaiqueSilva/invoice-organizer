# Próximas melhorias

## MVP implementado

- Importação local de PDFs com limite de tamanho e validação básica.
- Extração heurística de tipo, emitente/beneficiário, número, datas e valor.
- Banco SQLite, detecção de duplicatas, busca, filtros, download do original e CSV.
- Modo de demonstração com dados fictícios.

## Próximos passos

1. Adicionar OCR local opcional para PDFs escaneados e sinalizar confiança por campo.
2. Incluir documentos sintéticos para testes de regressão dos formatos mais comuns.
3. Adicionar edição manual dos campos e exclusão com confirmação/recuperação.
4. Melhorar a extração com fixtures anonimizadas e consentidas, sem guardar documentos financeiros reais no Git.

As extrações são heurísticas e precisam ser verificadas no PDF original.
