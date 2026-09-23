"""
Modelo insumo-produto ambientalmente estendido (EEIO), híbrido, para os 12
setores da Tabela de Usos do IBGE, com vetor de emissões do SEEG.

Emissões diretas:   e_j = E_j / x_j            (coeficiente de emissão direta)
Emissões indiretas: f = e' L                    (multiplicador total de emissão)
onde L = (I - A)^-1 é a inversa de Leontief.

Índices de encadeamento (Rasmussen-Hirschman), usados para identificar
setores-chave do ponto de vista de emissões embutidas na cadeia produtiva:
  BL_j (para trás) = coluna j de L, soma / média das colunas
  FL_i (para frente) = linha i de L, soma / média das linhas
"""
import numpy as np
import pandas as pd

from load_io import (
    load_ci_matrix, load_total_output, build_technical_coefficients,
    leontief_inverse, SECTOR_CODES, SECTOR_NAMES,
)
from seeg_mapping import build_sector_emission_vector


def emission_coefficients(emissions: pd.Series, total_output: pd.Series) -> pd.Series:
    """e_j = E_j / x_j -- tCO2e por R$ milhão produzido, por setor."""
    e = emissions / total_output.replace(0, np.nan)
    e = e.fillna(0)
    e.name = "coef_emissao_direta"
    return e


def total_emission_multiplier(e: pd.Series, L: pd.DataFrame) -> pd.Series:
    """f = e' L -- emissão total (direta + indireta) por unidade de demanda
    final entregue pelo setor j, em tCO2e / R$ milhão."""
    f = e.values @ L.values
    return pd.Series(f, index=L.columns, name="multiplicador_emissao_total")


def direct_and_indirect_emissions(e: pd.Series, L: pd.DataFrame,
                                   final_demand: pd.Series) -> pd.DataFrame:
    """Para cada setor j (fonte de demanda final), decompõe a emissão total
    embutida em atender essa demanda em uma parcela direta (própria produção
    de j) e uma parcela indireta (emissões dos fornecedores de j na cadeia).

    total_j     = (e' L)_j * y_j            -- via multiplicador total (f)
    direta_j    = e_j * y_j                  -- só a produção do próprio setor
    indireta_j  = total_j - direta_j
    """
    y = final_demand.reindex(L.columns).fillna(0)
    f = total_emission_multiplier(e, L)

    total_j = f * y
    direta_j = e.reindex(y.index).fillna(0) * y
    indireta_j = total_j - direta_j

    out = pd.DataFrame({
        "demanda_final_Rmi": y,
        "emissao_total_tCO2e": total_j,
        "emissao_direta_tCO2e": direta_j,
        "emissao_indireta_tCO2e": indireta_j,
        "pct_indireta": (indireta_j / total_j.replace(0, np.nan) * 100).fillna(0),
    })
    return out


def linkage_indices(L: pd.DataFrame) -> pd.DataFrame:
    """Índices de encadeamento de Rasmussen-Hirschman normalizados (média = 1)."""
    n = len(L)
    col_sum = L.sum(axis=0)   # para trás (backward): impacto de 1 unid. de demanda no setor j
    row_sum = L.sum(axis=1)   # para frente (forward): quanto o setor i é demandado pelos outros
    BL = col_sum / col_sum.mean()
    FL = row_sum / row_sum.mean()
    df = pd.DataFrame({"encadeamento_para_tras": BL, "encadeamento_para_frente": FL})
    df["setor_chave"] = (df["encadeamento_para_tras"] > 1) & (df["encadeamento_para_frente"] > 1)
    return df


def run_year(io_xls_path: str, seeg_subcat_csv_path: str, seeg_year_col: str) -> dict:
    ci = load_ci_matrix(io_xls_path)
    x = load_total_output(io_xls_path)
    A = build_technical_coefficients(ci, x)
    L = leontief_inverse(A)

    E = build_sector_emission_vector(seeg_subcat_csv_path, seeg_year_col)
    e = emission_coefficients(E, x)
    f = total_emission_multiplier(e, L)
    linkages = linkage_indices(L)

    summary = pd.DataFrame({
        "setor": [SECTOR_NAMES[c] for c in SECTOR_CODES],
        "producao_total_R$mi": x,
        "emissao_direta_tCO2e": E,
        "coef_emissao_direta": e,
        "multiplicador_emissao_total": f,
        "encadeamento_para_tras": linkages["encadeamento_para_tras"],
        "encadeamento_para_frente": linkages["encadeamento_para_frente"],
        "setor_chave": linkages["setor_chave"],
    })
    return {"A": A, "L": L, "E": E, "e": e, "f": f, "summary": summary}


if __name__ == "__main__":
    from load_io import load_final_demand

    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 10)

    for year, io_path, seeg_path, col in [
        (2015, "data/raw/12_tab2_2015.xls", "data/raw/SEEG__2015__-_sub_categoria.csv", "2015"),
        (2023, "data/raw/12_tab2_2023.xls", "data/raw/SEEG__2023__-_subcategorias.csv", "2023"),
    ]:
        res = run_year(io_path, seeg_path, col)
        print(f"=== {year}: resumo por setor ===")
        print(res["summary"].round(3))

        fd = load_final_demand(io_path)
        y_total = fd["demanda_final_total"]
        decomp = direct_and_indirect_emissions(res["e"], res["L"], y_total)
        print(f"\n=== {year}: emissões diretas x indiretas embutidas na demanda final ===")
        print(decomp.round(1))
        print()

        res["summary"].to_csv(f"outputs/summary_{year}.csv")
        decomp.to_csv(f"outputs/direct_indirect_{year}.csv")
