# Brasil 2015–2023: matriz insumo-produto, emissões e encadeamento setorial

Modelo insumo-produto ambientalmente estendido (EEIO), híbrido, para 12
setores da economia brasileira, integrando a Tabela de Usos do IBGE (2015 e
2023) com dados de emissões de GEE do SEEG (Energia, Processos Industriais e
Agropecuária). Estima coeficientes técnicos, inversa de Leontief, emissões
diretas/indiretas, multiplicadores de emissão e índices de encadeamento
(Rasmussen-Hirschman) para os dois anos, e compara a estrutura produtiva e de
emissões entre eles.

## Resultados principais

**A Indústria de Transformação é o único setor-chave da economia nos dois
anos** (alto encadeamento para trás *e* para frente) — concentra ~36% das
emissões diretas mapeadas em ambos os anos e é o setor cuja cadeia de
fornecedores mais amplifica emissões indiretas.

**Transporte foi o setor que mais ganhou peso relativo em emissões**: sua
participação nas emissões diretas mapeadas subiu de 41,0% (2015) para 48,2%
(2023), um aumento de 7,2 pontos percentuais — e já era, nos dois anos, o
setor com o maior multiplicador total de emissão (direta + indireta) por
unidade de demanda final atendida.

**Eletricidade foi o setor que mais perdeu peso relativo**: caiu de 13,3%
para 4,3% de participação nas emissões diretas (-9,0 p.p.). Isso é
consistente com a mudança na matriz elétrica brasileira entre 2015 (ano de
crise hídrica, com forte acionamento de térmicas) e 2023 (maior geração
renovável) — o projeto não testa essa hipótese diretamente, mas o resultado
é compatível com ela.

**Nenhum outro setor mudou de posição na lista de setores-chave** entre os
dois anos — a estrutura de encadeamento da economia, no nível de agregação
de 12 setores, é relativamente estável no período.

Tabela completa em `outputs/comparacao_relativa_2015_2023.csv`; resumo por
setor e por ano em `outputs/summary_2015.csv` e `outputs/summary_2023.csv`.

## Por que comparação relativa, e não em R$

As duas tabelas de usos estão em preços correntes de cada ano (R$ de 2015 e
R$ de 2023, sem deflacionar). Comparar valores monetários absolutos entre os
anos misturaria variação real com inflação. Por isso, a comparação entre
2015 e 2023 neste projeto é feita inteiramente em termos **relativos**:
participação percentual, ranking e posição — grandezas normalizadas dentro
de cada ano, que não dependem de deflação para serem comparáveis. Essa é uma
escolha metodológica deliberada, não uma limitação escondida: ela evita
justamente o problema de misturar efeito-preço com efeito-estrutura.

## Escopo do modelo

Este projeto modela emissões associadas à estrutura produtiva da economia —
Energia, Processos Industriais e Agropecuária —, cobrindo ~95% desse
subconjunto do SEEG mapeável aos 12 setores da Tabela de Usos do IBGE (ver
`src/seeg_mapping.py` para o mapeamento completo).

Mudança de Uso da Terra e Floresta não é modelada dentro do arcabouço de
Leontief: é a maior categoria de emissões do Brasil, mas não corresponde a
uma atividade que compra e vende insumos na matriz de usos — por isso, na
literatura de EEIO, costuma ser tratada à parte de exercícios baseados em
insumo-produto, e não incorporada a um setor específico.

## Extensões planejadas

- **Decomposição estrutural (SDA) em termos reais**: o método já está
  implementado em `src/sda.py` (2-polar average, Dietzenbacher & Los, 1998,
  com o resíduo de 3ª ordem reportado explicitamente). A próxima etapa é
  incorporar deflatores setoriais do IBGE para tornar os efeitos
  (intensidade de emissão, estrutura produtiva, demanda final) comparáveis
  em termos reais entre 2015 e 2023.
- Nível de agregação setorial mais fino que os 12 setores atuais.
- Notebook único consolidando a análise com visualizações.

## Metodologia

1. **Matriz de coeficientes técnicos e inversa de Leontief** — a partir da
   Tabela de Usos do IBGE (consumo intermediário ÷ valor da produção por
   setor). Nota técnica: o denominador correto é o "Valor da Produção" da
   atividade (aba VA da planilha do IBGE), não o total de demanda pelo
   produto (que gera coeficientes >1 para setores como Construção e
   Comércio, cujo produto é majoritariamente absorvido por FBCF/margens).
2. **Mapeamento SEEG → 12 setores** — cada subcategoria de emissão
   (Energia, Processos Industriais, Agropecuária) é associada ao setor IBGE
   correspondente; itens sem correspondência clara (ex.: "Residencial",
   "Outros") são excluídos e documentados.
3. **Coeficientes de emissão, multiplicadores e encadeamento** — cálculo
   padrão de EEIO: e = E/x (emissão direta por unidade de produção),
   f = e'L (multiplicador total), índices de Rasmussen-Hirschman a partir da
   inversa de Leontief.
4. **Comparação relativa 2015–2023** — participações percentuais e
   rankings, não valores absolutos (ver seção acima).

## Estrutura do repositório

```
data/raw/              dados originais (IBGE Tabela de Usos, SEEG)
src/
  load_io.py            leitura da Tabela de Usos, matriz A, inversa de Leontief
  seeg_mapping.py        mapeamento SEEG -> 12 setores
  eeio_model.py           coeficientes de emissão, multiplicador total, encadeamento
  compare_years.py        comparação relativa 2015 vs 2023 (resultado principal)
  sda.py                   decomposição estrutural (SDA) -- ver "Extensões planejadas"
outputs/                CSVs de resultado gerados pelos scripts
```

## Como rodar

```bash
pip install -r requirements.txt
cd src
python load_io.py          # sanity check da matriz A (soma < 1 por setor)
python seeg_mapping.py      # sanity check da cobertura do mapeamento SEEG
python eeio_model.py         # gera summary_2015.csv, summary_2023.csv, direct_indirect_*.csv
python compare_years.py       # gera comparacao_relativa_2015_2023.csv -- resultado principal
python sda.py                  # decomposição estrutural (ver "Extensões planejadas" no README)
```

## Dados e fontes

- **IBGE — Sistema de Contas Nacionais do Brasil**, Tabela de Usos de Bens e
  Serviços (agregação própria a 12 setores):
  https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9052-sistema-de-contas-nacionais-brasil.html?edicao=44968
- **SEEG** (Sistema de Estimativas de Emissões e Remoções de Gases de Efeito
  Estufa), Observatório do Clima — emissões por categoria/subcategoria:
  https://plataforma.seeg.eco.br/?yearRange%5B0%5D=2023&yearRange%5B1%5D=2023&sector%5B0%5D=477&sector%5B1%5D=449&emissionType%5B0%5D=1&gas=49&groupBy=Subcategory&rankBy=State&filtersTab=filters&statisticsTab=historical

Os arquivos brutos usados neste projeto estão em `data/raw/`, extraídos
diretamente dessas plataformas.
