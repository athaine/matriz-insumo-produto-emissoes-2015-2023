"""
Decomposição estrutural (SDA) da variação das emissões totais entre dois anos.

T = e' L y   (emissão total = coef. de emissão x inversa de Leontief x demanda final)

Decompõe ΔT = T1 - T0 em três efeitos:
  - Δe : mudança na intensidade de emissão (tecnologia de emissão)
  - ΔL : mudança na estrutura tecnológica/produtiva (matriz de Leontief)
  - Δy : mudança na composição e volume da demanda final

Método: média das duas decomposições polares (Dietzenbacher & Los, 1998),
abordagem padrão na literatura de SDA para 3 determinantes. Para 2 fatores
essa média é uma identidade exata; para 3 fatores (nosso caso: e, L, y) ela
é uma MUITO BOA APROXIMAÇÃO, mas deixa um resíduo de 3ª ordem (0.5 * Δe ΔL
Δy) que normalmente é pequeno. O código reporta esse resíduo explicitamente
(diferença entre soma_efeitos e delta_total) em vez de escondê-lo -- não
tente "fechar" a conta ajustando manualmente um dos efeitos.

ATENÇÃO -- PREÇOS: os valores de e, L e y de cada ano estão em preços
correntes daquele ano (R$ milhões correntes de 2015 e de 2023). Sem
deflacionar a tabela de 2023 para preços de 2015, parte do efeito "Δy" (e,
em menor grau, ΔL) captura inflação/variação de preços relativos, não
variação real de volume/estrutura. Este é um limite explícito do resultado
--- ver README para a leitura correta dos números nesta versão do projeto.
"""
import pandas as pd
import numpy as np

from eeio_model import run_year, total_emission_multiplier, DATA_DIR, OUTPUT_DIR
from load_io import load_final_demand


def sda_decompose(e0, L0, y0, e1, L1, y1) -> dict:
    e0, e1 = e0.align(e1)[0], e1.align(e0)[0]
    y0 = y0.reindex(L0.columns).fillna(0)
    y1 = y1.reindex(L1.columns).fillna(0)

    T0 = e0.values @ L0.values @ y0.values
    T1 = e1.values @ L1.values @ y1.values

    de = e1 - e0
    dL = L1 - L0
    dy = y1 - y0

    efeito_e = 0.5 * (de.values @ L0.values @ y0.values + de.values @ L1.values @ y1.values)
    efeito_L = 0.5 * (e0.values @ dL.values @ y0.values + e1.values @ dL.values @ y1.values)
    efeito_y = 0.5 * (e0.values @ L0.values @ dy.values + e1.values @ L1.values @ dy.values)

    return {
        "T0": T0, "T1": T1, "delta_total": T1 - T0,
        "efeito_intensidade_emissao": efeito_e,
        "efeito_estrutura_produtiva": efeito_L,
        "efeito_demanda_final": efeito_y,
        "soma_efeitos": efeito_e + efeito_L + efeito_y,
        "residuo_3a_ordem": (efeito_e + efeito_L + efeito_y) - (T1 - T0),
    }


def sda_by_sector(e0, L0, y0, e1, L1, y1) -> pd.DataFrame:
    """Mesma decomposição, mas mantendo o resultado por setor (linha = setor
    fornecedor onde a emissão ocorre, antes de somar)."""
    y0 = y0.reindex(L0.columns).fillna(0)
    y1 = y1.reindex(L1.columns).fillna(0)
    de, dL, dy = (e1 - e0), (L1 - L0), (y1 - y0)

    def contrib_e(e_):
        return np.diag(e_.values) @ L0.values @ y0.values, np.diag(e_.values) @ L1.values @ y1.values

    ef_e0, ef_e1 = contrib_e(de)
    efeito_e = 0.5 * (ef_e0 + ef_e1)

    ef_L0 = np.diag(e0.values) @ dL.values @ y0.values
    ef_L1 = np.diag(e1.values) @ dL.values @ y1.values
    efeito_L = 0.5 * (ef_L0 + ef_L1)

    ef_y0 = np.diag(e0.values) @ L0.values @ dy.values
    ef_y1 = np.diag(e1.values) @ L1.values @ dy.values
    efeito_y = 0.5 * (ef_y0 + ef_y1)

    return pd.DataFrame({
        "efeito_intensidade_emissao": efeito_e,
        "efeito_estrutura_produtiva": efeito_L,
        "efeito_demanda_final": efeito_y,
    }, index=L0.index)


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    res15 = run_year(DATA_DIR / "12_tab2_2015.xls", DATA_DIR / "SEEG__2015__-_sub_categoria.csv", "2015")
    res23 = run_year(DATA_DIR / "12_tab2_2023.xls", DATA_DIR / "SEEG__2023__-_subcategorias.csv", "2023")

    y15 = load_final_demand(DATA_DIR / "12_tab2_2015.xls")["demanda_final_total"]
    y23 = load_final_demand(DATA_DIR / "12_tab2_2023.xls")["demanda_final_total"]

    result = sda_decompose(res15["e"], res15["L"], y15, res23["e"], res23["L"], y23)
    print("=== SDA agregada 2015 -> 2023 (tCO2e; PREÇOS CORRENTES, ver aviso no docstring) ===")
    for k, v in result.items():
        print(f"{k:30s}: {v:,.0f}")

    residuo_pct = 100 * result["residuo_3a_ordem"] / result["delta_total"]
    print(f"\nResíduo de 3ª ordem: {result['residuo_3a_ordem']:,.0f} tCO2e "
          f"({residuo_pct:.2f}% do delta total) -- ver docstring do módulo")

    by_sector = sda_by_sector(res15["e"], res15["L"], y15, res23["e"], res23["L"], y23)
    by_sector.index = res15["summary"]["setor"].values
    print("\n=== SDA por setor de origem da emissão ===")
    pd.set_option("display.width", 160)
    print(by_sector.round(0))
    by_sector.to_csv(OUTPUT_DIR / "sda_by_sector.csv")
