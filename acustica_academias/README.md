# ImpactoSEA-ProPG

Documentacao inicial do notebook `ImpactoSEA_ProPG.ipynb`, criado para servir como fundamentacao teorica e base computacional da evolucao do estudo de transmissao de ruido e vibracao em academias.

## Objetivo

O notebook organiza uma calculadora tecnica para avaliar, de forma preliminar, impactos de ruido e vibracao gerados por atividades de academia, com foco em exercicios de impacto e transmissao estrutural.

A proposta e apoiar a fase de estudo, comparacao de cenarios e justificativa tecnica antes de qualquer consolidacao em laudo ou memoria de calculo definitiva.

## Fundamentacao teorica

O estudo utiliza como referencia principal a abordagem de Analise Estatistica de Energia, conhecida como SEA, aplicada ao contexto de academias. A metodologia esta alinhada ao guia ProPG/GAG para acustica de academias e considera:

- transmissao de energia por impacto;
- resposta dinamica de sistemas piso-estrutura;
- comportamento em baixa frequencia;
- curvas de referencia do guia ProPG/GAG;
- avaliacao de mitigacao por piso flutuante modelado como sistema massa-mola-amortecedor;
- interpretacao tecnica de resultados para comparacao entre cenarios.

## Estrutura do notebook

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

## Arquivos

- `ImpactoSEA_ProPG.ipynb`: notebook principal do estudo.
- `README.md`: documentacao inicial do estudo.

Arquivos de backup locais nao fazem parte da documentacao principal e devem ser mantidos fora do versionamento, salvo necessidade especifica.
