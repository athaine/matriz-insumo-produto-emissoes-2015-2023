"""
Comparação relativa entre 2015 e 2023 -- rankings, participações (%) e
variação de posição no encadeamento produtivo e nas emissões.

Por que "relativo" e não "em R$"? Porque razões, participações (%) e
rankings são adimensionais / normalizados dentro de cada ano -- não exigem
que as duas tabelas estejam na mesma base de preços para serem comparáveis
entre si. É a parte da comparação 2015-2023 que os dados atuais sustentam
sem nenhuma ressalva sobre inflação.
"""
import pandas as pd
from eeio_model import run_year


def relative_comparison(res15: dict, res23: dict) -> pd.DataFrame:
    s15 = res15["summary"].copy()
    s23 = res23["summary"].copy()

    df = pd.DataFrame({"setor": s15["setor"]})

    # participação (%) de cada setor na emissão direta total do ano
    df["participacao_emissao_2015_%"] = 100 * s15["emissao_direta_tCO2e"] / s15["emissao_direta_tCO2e"].sum()
    df["participacao_emissao_2023_%"] = 100 * s23["emissao_direta_tCO2e"] / s23["emissao_direta_tCO2e"].sum()
    df["variacao_participacao_p.p."] = df["participacao_emissao_2023_%"] - df["participacao_emissao_2015_%"]

    # ranking de encadeamento para trás (quanto maior, mais "puxa" a cadeia)
    df["ranking_encadeamento_2015"] = s15["encadeamento_para_tras"].rank(ascending=False).astype(int)
    df["ranking_encadeamento_2023"] = s23["encadeamento_para_tras"].rank(ascending=False).astype(int)
    df["variacao_ranking_encadeamento"] = df["ranking_encadeamento_2015"] - df["ranking_encadeamento_2023"]

    # ranking do multiplicador total de emissão (tCO2e por R$ de demanda final atendida)
    df["ranking_mult_emissao_2015"] = s15["multiplicador_emissao_total"].rank(ascending=False).astype(int)
    df["ranking_mult_emissao_2023"] = s23["multiplicador_emissao_total"].rank(ascending=False).astype(int)
    df["variacao_ranking_mult_emissao"] = df["ranking_mult_emissao_2015"] - df["ranking_mult_emissao_2023"]

    # setor-chave permanece setor-chave?
    df["setor_chave_2015"] = s15["setor_chave"].values
    df["setor_chave_2023"] = s23["setor_chave"].values
    df["permanece_setor_chave"] = df["setor_chave_2015"] & df["setor_chave_2023"]

    return df.round(2)


if __name__ == "__main__":
    res15 = run_year("data/raw/12_tab2_2015.xls", "data/raw/SEEG__2015__-_sub_categoria.csv", "2015")
    res23 = run_year("data/raw/12_tab2_2023.xls", "data/raw/SEEG__2023__-_subcategorias.csv", "2023")

    comp = relative_comparison(res15, res23)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(comp.to_string(index=False))
    comp.to_csv("outputs/comparacao_relativa_2015_2023.csv", index=False)
