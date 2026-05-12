# ImpactoSEA-ProPG

Aplicacao Streamlit e biblioteca de calculo para transformar o notebook
`ImpactoSEA_ProPG.ipynb` em uma ferramenta preliminar de dimensionamento de
ruido de impacto pesado em academias.

## Objetivo

O projeto organiza uma calculadora tecnica para avaliar, de forma preliminar,
impactos de ruido e vibracao gerados por atividades de academia, com foco em
exercicios de impacto e transmissao estrutural.

A proposta e apoiar a fase de estudo, comparacao de cenarios, especificacao de
mitigacao e emissao de uma Declaracao de Design Acustico (ADS) antes de qualquer
consolidacao em laudo ou memoria de calculo definitiva.

## Como rodar

Versao fixada do Python: `3.12.10`. Se usar `pyenv`, `mise` ou ferramenta
compativel, o arquivo `.python-version` ja seleciona essa versao dentro desta
pasta.

```bash
cd acustica_academias
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/Home.py
```

## Testes

Os testes do motor de calculo usam apenas a biblioteca padrao do Python.

```bash
python -m unittest discover -s acustica_academias/tests
```

## Fundamentacao teorica

O estudo utiliza como referencia principal a abordagem de Analise Estatistica de Energia, conhecida como SEA, aplicada ao contexto de academias. A metodologia esta alinhada ao guia ProPG/GAG para acustica de academias e considera:

- transmissao de energia por impacto;
- resposta dinamica de sistemas piso-estrutura;
- comportamento em baixa frequencia;
- curvas de referencia do guia ProPG/GAG;
- avaliacao de mitigacao por piso flutuante modelado como sistema massa-mola-amortecedor;
- interpretacao tecnica de resultados para comparacao entre cenarios.

## Estrutura

- `app/Home.py`: interface Streamlit para Estagio 1, Estagio 2, resultados,
  ADS e validacao H.3.
- `src/impactosea/`: motor SEA, curvas G, mitigacao SDOF, viabilidade e geracao
  do relatorio ADS.
- `data/solutions.yaml`: catalogo versionado de solucoes de mitigacao.
- `tests/`: regressao do caso H.3, Curvas-G, catalogo e relatorio.
- `ImpactoSEA_ProPG.ipynb`: notebook de pesquisa que originou a implementacao.

O arquivo `ImpactoSEA_ProPG.ipynb` contem:

- apresentacao do escopo tecnico;
- definicao das curvas G de referencia;
- motor de calculo SEA revisado;
- funcao de mitigacao por piso flutuante;
- verificacoes, avisos e campos intermediarios para rastreabilidade;
- exemplos de aplicacao para apoiar a evolucao do estudo.

## Uso previsto

Este material deve ser usado como base de pesquisa e desenvolvimento para:

- testar hipoteses de projeto;
- comparar alternativas de mitigacao;
- documentar premissas adotadas;
- evoluir a metodologia de calculo;
- apoiar discussoes tecnicas com referencias rastreaveis.

## Cuidados

O notebook ainda deve ser tratado como estudo tecnico em evolucao. Antes de usar os resultados em decisao final de projeto, recomenda-se revisar:

- unidades e premissas de entrada;
- aderencia das referencias ao caso real;
- sensibilidade dos parametros fisicos;
- validacao com medicoes ou dados de campo, quando disponiveis;
- limitacoes da aplicacao do metodo SEA em geometrias e sistemas construtivos especificos.

Arquivos de backup locais nao fazem parte da documentacao principal e devem ser
mantidos fora do versionamento, salvo necessidade especifica.
