# Organizador de Notas e Boletos

Aplicação local para guardar notas fiscais e boletos em PDF, extrair alguns campos automaticamente e encontrar documentos sem abrir cada arquivo manualmente.

> O projeto está em desenvolvimento. A extração funciona em PDFs com texto selecionável; documentos escaneados ainda precisam de OCR e devem ser conferidos manualmente.

## O que já faz

- Importa PDFs de até 15 MB e identifica notas fiscais e boletos por conteúdo.
- Extrai campos comuns, como emitente/beneficiário, número, datas e valor.
- Guarda os arquivos e os dados em SQLite na máquina local.
- Evita importar o mesmo arquivo duas vezes usando seu hash SHA-256.
- Pesquisa e filtra documentos e permite baixar o PDF original ou exportar a lista como CSV.
- Oferece modo de demonstração com dados fictícios, sem tocar nos documentos locais.

Os campos extraídos são uma conveniência e podem estar ausentes ou incorretos conforme o formato do PDF. Confira o documento original antes de usar os dados em pagamentos ou registros contábeis.

## Demonstração

O **Modo de demonstração** começa ativado para você explorar a interface sem arquivos reais. Desative-o na barra lateral para importar PDFs e usar seu banco de dados local.

![Dashboard com exemplos fictícios de notas fiscais e boletos](assets/screenshots/dashboard-demo.png)

## Requisitos

- Python 3.11 ou mais recente
- Um ambiente gráfico para abrir o dashboard Streamlit

## Instalação

```bash
git clone https://github.com/LuaKaiqueSilva/invoice-organizer.git
cd invoice-organizer
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Como alternativa, `./scripts/setup.sh` cria o ambiente virtual e instala as dependências.

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

## Executar

```bash
streamlit run src/main.py
```

Ou execute `./scripts/run.sh` se instalou pelo script acima.

O Streamlit mostrará um endereço local, normalmente <http://localhost:8501>. Os dados ficam em `data/` dentro do projeto. A variável `INVOICE_ORGANIZER_DATA_DIR` pode apontar para outra pasta local.

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -v
ruff check src tests
```

## Privacidade

Os PDFs e o banco ficam na pasta local `data/`, ignorada pelo Git. O app não envia documentos a serviços externos. Evite compartilhar capturas que mostrem dados reais e mantenha uma cópia de segurança da pasta `data/` se guardar arquivos importantes.

## Limitações atuais

- PDFs protegidos por senha ou sem texto selecionável não são importados.
- Não há OCR, validação fiscal, conexão bancária, envio automático de pagamentos nem classificação contábil.
- Os layouts de notas e boletos variam; a extração usa rótulos textuais conhecidos e não substitui conferência humana.

## Estrutura

```text
src/
├── config/       # caminhos e limites locais
├── dashboard/    # interface Streamlit
├── database/     # conexão e esquema SQLite
├── models/       # estruturas de documento
├── parsers/      # extração de campos a partir do texto do PDF
├── repositories/ # persistência
├── services/     # validação e importação
└── utils/        # leitura e armazenamento seguro de PDFs
```

## Licença

MIT. Consulte [LICENSE](LICENSE).
