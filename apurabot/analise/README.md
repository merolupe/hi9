# Análise exploratória

Scripts usados para produzir os achados de `docs/apurabot/05-achados-julho-2026.md`
a partir da apuração manual de Julho/2026.

Não fazem parte do motor. Servem para **reproduzir os números documentados** e
para analisar uma nova competência quando surgir dúvida sobre uma regra.

```bash
pip install xlrd==2.0.1          # leitura de .xls (formato antigo)
python perfil_livro.py   <apuracao.xls>   # volume, CFOPs, CSTs, estabelecimentos
python valida_carga.py   <apuracao.xls>   # afere o algoritmo de equalização
python analisa_rb.py     <apuracao.xls>   # benefício fiscal de Rio Brilhante
```

O arquivo de apuração **não** está no repositório (contém dados fiscais reais).
Pegue-o na pasta da competência.
