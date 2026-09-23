"""
Mapeamento das subcategorias de emissão do SEEG (setores Energia, Processos
Industriais e Agropecuária) para os 12 setores da Tabela de Usos do IBGE.

ESCOPO E LIMITAÇÃO METODOLÓGICA (documentada, não escondida):
- A categoria "Mudança de Uso da Terra e Floresta" (MUTF/LULUCF) é EXCLUÍDA
  deste modelo. Ela não corresponde a uma atividade de produção de bens e
  serviços na estrutura de insumo-produto (não compra nem vende insumos na
  matriz), sendo tratada à parte na literatura de EEIO. Incluir essa fatia
  dentro de um único setor (ex.: Agropecuária) distorceria os coeficientes de
  emissão e a decomposição estrutural sem base metodológica sólida.
  Consequência: o modelo cobre uma fração minoritária do total de GEE do
  Brasil (a MUTF responde por mais da metade do total do SEEG nesses anos) —
  isso é intencional e está documentado no README.
- A subcategoria "Residencial" também é excluída: são emissões de consumo
  final das famílias (queima de GLP/lenha em domicílios), não de atividade
  produtiva intermediária — não há setor comprador de insumos a associar.
- "Público" é mapeada à atividade 12 (Administração pública).
- Itens residuais ("Outros", "Uso não-energético de combustíveis e solventes
  em outros setores") são excluídos por ambiguidade de destino setorial.
"""
from pathlib import Path

import pandas as pd

# Caminhos calculados a partir da localização deste arquivo (não do diretório
# de onde o script é chamado) -- assim funciona independente de cwd.
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "raw"

# subcategoria SEEG -> código do setor IBGE (12 setores)
SUBCATEGORY_TO_SECTOR = {
    # Transporte
    "Rodoviário": "07",
    "Aéreo": "07",
    "Hidroviário": "07",
    "Ferroviário": "07",
    "Transporte de petróleo e gás natural": "07",
    # Energia elétrica
    "Geração de eletricidade (serviço público)": "04",
    # Extração
    "Exploração de petróleo e gás natural": "02",
    "Mineração e pelotização": "02",
    # Indústria de transformação (metalurgia, química, não-metálicos, etc.)
    "Produção de ferro gusa e aço": "03",
    "Ferro gusa e aço": "03",
    "Refino de petróleo": "03",
    "Produção de cimento": "03",
    "Cimento": "03",
    "Química": "03",
    "Não ferrosos e outros da metalurgia": "03",
    "Outras indústrias": "03",
    "Produção de cal": "03",
    "Cerâmica": "03",
    "Alimentos e bebidas": "03",
    "Papel e celulose": "03",
    "Produção de outros não-ferrosos": "03",
    "Produção de alumínio": "03",
    "Produção de negro-de-fumo": "03",
    "Produção de magnésia não metalúrgica": "03",
    "Produção de ferroligas": "03",
    # Comércio e administração pública
    "Comercial": "06",
    "Público": "12",
    # Agropecuária
    "Agropecuária": "01",
}

# excluídos explicitamente (ver docstring acima) — mantidos aqui só para
# rastreabilidade/checagem de soma total, nunca usados no modelo
EXCLUDED_SUBCATEGORIES = {
    "Residencial",
    "Outros",
    "Uso não-energético de combustíveis e solventes em outros setores",
}


def build_sector_emission_vector(subcategoria_csv_path: str, year_col: str) -> pd.Series:
    """Lê o csv de subcategorias do SEEG e agrega para os 12 setores IBGE.
    Retorna emissões em tCO2e por setor (índice = código '01'..'12')."""
    df = pd.read_csv(subcategoria_csv_path)
    df.columns = [c.strip() for c in df.columns]
    cat_col = df.columns[0]
    df["setor"] = df[cat_col].map(SUBCATEGORY_TO_SECTOR)

    unmapped = df[df["setor"].isna() & ~df[cat_col].isin(EXCLUDED_SUBCATEGORIES)]
    if len(unmapped) > 0:
        raise ValueError(
            f"Subcategorias não mapeadas e não marcadas como excluídas: "
            f"{unmapped[cat_col].tolist()}"
        )

    mapped = df.dropna(subset=["setor"])
    vec = mapped.groupby("setor")[year_col].sum()
    vec = vec.reindex([f"{i:02d}" for i in range(1, 13)], fill_value=0.0)
    vec.name = "emissoes_tco2e"
    return vec


def coverage_report(subcategoria_csv_path: str, year_col: str) -> dict:
    """Retorna o % do total do SEEG (nesse nível de agregação) que o modelo
    efetivamente cobre, para deixar explícito no README/relatório."""
    df = pd.read_csv(subcategoria_csv_path)
    df.columns = [c.strip() for c in df.columns]
    cat_col = df.columns[0]
    total = df[year_col].sum()
    mapped_total = df[df[cat_col].isin(SUBCATEGORY_TO_SECTOR.keys())][year_col].sum()
    return {
        "total_subcategorias": total,
        "total_mapeado": mapped_total,
        "cobertura_pct": round(100 * mapped_total / total, 1),
    }


if __name__ == "__main__":
    for year, path, col in [
        (2015, DATA_DIR / "SEEG__2015__-_sub_categoria.csv", "2015"),
        (2023, DATA_DIR / "SEEG__2023__-_subcategorias.csv", "2023"),
    ]:
        vec = build_sector_emission_vector(path, col)
        rep = coverage_report(path, col)
        print(f"--- {year} --- cobertura do nível 'subcategoria': {rep['cobertura_pct']}%")
        print(vec.round(0))
        print()
