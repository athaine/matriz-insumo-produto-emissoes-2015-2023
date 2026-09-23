# Brasil 2015–2023: matriz insumo-produto, emissões e encadeamento setorial

Modelo insumo-produto ambientalmente estendido para 12
setores da economia brasileira, integrando a Tabela de Usos do IBGE (2015 e
2023) com dados de emissões de GEE do SEEG (Energia, Processos Industriais e
Agropecuária). Estima coeficientes técnicos, inversa de Leontief, emissões
diretas/indiretas, multiplicadores de emissão e índices de encadeamento
(Rasmussen-Hirschman) para os dois anos, e compara a estrutura produtiva e de
emissões entre eles.

## Resultados principais

**A Indústria de Transformação é o único setor-chave da economia nos dois
anos** (alto encadeamento para trás *e* para frente), concentra ~36% das
emissões diretas mapeadas em ambos os anos e é o setor cuja cadeia de
fornecedores mais amplifica emissões indiretas.

**Transporte foi o setor que mais ganhou peso relativo em emissões**: sua
participação nas emissões diretas mapeadas subiu de 41,0% (2015) para 48,2%
(2023), um aumento de 7,2 pontos percentuais e já era, nos dois anos, o
setor com o maior multiplicador total de emissão (direta + indireta) por
unidade de demanda final atendida.

**Eletricidade foi o setor que mais perdeu peso relativo**: caiu de 13,3%
para 4,3% de participação nas emissões diretas (-9,0 p.p.). Isso é
consistente com a mudança na matriz elétrica brasileira entre 2015 (ano de
crise hídrica, com forte acionamento de térmicas) e 2023 (maior geração
renovável), o projeto não testa essa hipótese diretamente, mas o resultado
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

## Escopo metodológico e extensões planejadas

As decisões abaixo delimitam deliberadamente o que este projeto mede, para
que cada número reportado tenha lastro metodológico sólido — nenhum
resultado aqui mistura efeitos que a base de dados não permite separar.

- **Recorte de emissões: Energia, Processos Industriais e Agropecuária,
  mapeáveis aos 12 setores de produção (~95% de cobertura nesse recorte).**
  Mudança de Uso da Terra e Floresta (LULUCF) — maior categoria do SEEG em
  volume — foi deixada fora por não corresponder a uma atividade que compra
  e vende insumos na estrutura de insumo-produto; incluí-la à força em um
  único setor (ex.: Agropecuária) distorceria os coeficientes de emissão sem
  base metodológica. Tratar LULUCF corretamente exigiria estender o modelo
  com uma conta satélite de uso da terra, fora do escopo desta versão. Lista
  completa de inclusões/exclusões em `src/seeg_mapping.py`.
- **SDA (decomposição estrutural) implementado e validado como módulo, com
  resultado em valores absolutos reservado para a próxima versão.** O método
  (2-polar average, Dietzenbacher & Los 1998, com resíduo de 3ª ordem
  reportado explicitamente em `src/sda.py`) está correto e testado; o motivo
  de não reportar os valores absolutos como resultado principal é que a
  tabela de 2023 ainda está em preços correntes — próximo passo é
  incorporar deflatores setoriais (IBGE) para isolar variação real de
  estrutura de inflação, e então promover o SDA de módulo experimental a
  resultado do projeto.
- **Agregação a 12 setores é o nível de resolução da Tabela de Usos do IBGE
  usada nesta versão.** Suficiente para identificar setores-chave e padrões
  de encadeamento no nível macro; uma extensão natural é subir para as
  tabelas de 51 ou 68 setores do IBGE para análise setorial mais fina.

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
  sda.py                   decomposição estrutural -- módulo experimental, ver limitações
outputs/                CSVs de resultado gerados pelos scripts
```

## Como rodar

Os caminhos dos arquivos de dados (`data/raw/...`) são resolvidos dentro dos
próprios scripts a partir da localização de cada arquivo `.py`, e não do
diretório de onde você chama o `python` -- então os comandos abaixo funcionam
tanto rodados da raiz do projeto quanto de dentro de `src/`.

Da raiz do projeto:

```bash
pip install -r requirements.txt
python src/load_io.py          # sanity check da matriz A (soma < 1 por setor)
python src/seeg_mapping.py      # sanity check da cobertura do mapeamento SEEG
python src/eeio_model.py         # gera summary_2015.csv, summary_2023.csv, direct_indirect_*.csv
python src/compare_years.py       # gera comparacao_relativa_2015_2023.csv -- resultado principal
python src/sda.py                  # módulo experimental (ver limitações acima)
```

Ou, se preferir entrar em `src/` primeiro, funciona igual:

```bash
cd src
python load_io.py
python seeg_mapping.py
python eeio_model.py
python compare_years.py
python sda.py
```

A pasta `outputs/` é criada automaticamente pelos scripts, se ainda não
existir -- não precisa criá-la manualmente.

## Dados e fontes

- IBGE, Contas Nacionais — Tabela de Usos de Bens e Serviços (agregação
  própria a 12 setores).
  <https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9052-sistema-de-contas-nacionais-brasil.html?edicao=44968>. Anos utilizados: (2015 e 2023).
- SEEG (Sistema de Estimativas de Emissões e Remoções de Gases de Efeito
  Estufa), Observatório do Clima — emissões por categoria/subcategoria.
  <https://plataforma.seeg.eco.br/?yearRange%5B0%5D=2023&yearRange%5B1%5D=2023&sector%5B0%5D=477&sector%5B1%5D=449&emissionType%5B0%5D=1&gas=49&groupBy=Subcategory&rankBy=State&filtersTab=filters&statisticsTab=historical>
  Anos utilizados: (2015 e 2023).
