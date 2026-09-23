"""
Leitura e limpeza da Tabela de Usos de Bens e Serviços (IBGE, 12 setores).

O arquivo .xls original tem 3 abas relevantes para este projeto:
  - "CI"      : consumo intermediário das atividades (matriz 12x12, em R$ milhões)
  - "demanda" : componentes da demanda final por produto/setor
  - "VA"      : componentes do valor adicionado por atividade

As demais abas (2m02, 2n02, 2o02) são resíduo de um template antigo (nível 56
setores, ano 2001) e não são usadas aqui.
"""
import pandas as pd
import numpy as np

SECTOR_NAMES = {
    "01": "Agropecuária",
    "02": "Indústrias extrativas",
    "03": "Indústrias de transformação",
    "04": "Eletricidade e gás, água, esgoto, gestão de resíduos",
    "05": "Construção",
    "06": "Comércio",
    "07": "Transporte, armazenagem e correio",
    "08": "Informação e comunicação",
    "09": "Atividades financeiras, seguros e serviços relacionados",
    "10": "Atividades imobiliárias",
    "11": "Outras atividades de serviços",
    "12": "Administração, defesa, saúde e educação públicas",
}
SECTOR_CODES = list(SECTOR_NAMES.keys())


def load_ci_matrix(xls_path: str) -> pd.DataFrame:
    """Retorna a matriz de consumo intermediário (12x12), setor-linha x setor-coluna,
    com códigos '01'..'12' como índice e colunas."""
    raw = pd.read_excel(xls_path, sheet_name="CI", header=None)
    # linhas de dados: 5 a 16 (12 setores); colunas de dados: 2 a 13 (12 setores)
    data = raw.iloc[5:17, 2:14].apply(pd.to_numeric, errors="coerce")
    data.index = SECTOR_CODES
    data.columns = SECTOR_CODES
    data.index.name = "setor_linha"
    data.columns.name = "setor_coluna"
    return data


def load_total_output(xls_path: str) -> pd.Series:
    """Retorna o Valor da Produção (VBP) por setor/atividade, a partir da aba VA.

    IMPORTANTE: a coluna 'Total do produto' da aba CI é o total de DEMANDA pelo
    PRODUTO (linha), não a produção total da ATIVIDADE (coluna) que compra os
    insumos. Usar essa coluna como denominador de a_ij = z_ij / x_j gera
    coeficientes técnicos inconsistentes (ex.: soma > 1 para Construção e
    Comércio, cujo produto é majoritariamente absorvido por FBCF/margens e não
    reflete o valor total produzido pela atividade). O denominador correto é
    'Valor da produção' (VBP), disponível na aba VA.
    """
    raw = pd.read_excel(xls_path, sheet_name="VA", header=None)
    # localizar a linha "Valor da produção" na coluna 0
    row_idx = raw[raw[0] == "Valor da produção"].index[0]
    total = raw.iloc[row_idx, 1:13].apply(pd.to_numeric, errors="coerce")
    total.index = SECTOR_CODES
    total.name = "producao_total"
    return total


def load_final_demand(xls_path: str) -> pd.DataFrame:
    """Retorna os componentes de demanda final por setor."""
    raw = pd.read_excel(xls_path, sheet_name="demanda", header=None)
    cols = [
        "exportacao", "consumo_governo", "consumo_isflsf",
        "consumo_familias", "fbcf", "variacao_estoque",
        "demanda_final_total", "demanda_total",
    ]
    data = raw.iloc[5:17, 2:10].apply(pd.to_numeric, errors="coerce")
    data.index = SECTOR_CODES
    data.columns = cols
    return data


def build_technical_coefficients(ci: pd.DataFrame, total_output: pd.Series) -> pd.DataFrame:
    """Matriz de coeficientes técnicos A = Z * diag(1/x).
    ci: matriz de consumo intermediário (linha=setor fornecedor, coluna=setor comprador)
    total_output: produção total por setor (usada como x, no denominador, por coluna)
    """
    x_inv = 1.0 / total_output.replace(0, np.nan)
    A = ci.multiply(x_inv, axis=1).fillna(0)
    return A


def leontief_inverse(A: pd.DataFrame) -> pd.DataFrame:
    I = np.eye(len(A))
    L = np.linalg.inv(I - A.values)
    return pd.DataFrame(L, index=A.index, columns=A.columns)


if __name__ == "__main__":
    for year, path in [(2015, "data/raw/12_tab2_2015.xls"), (2023, "data/raw/12_tab2_2023.xls")]:
        ci = load_ci_matrix(path)
        x = load_total_output(path)
        A = build_technical_coefficients(ci, x)
        L = leontief_inverse(A)
        print(f"--- {year} ---")
        print("Soma dos coeficientes técnicos por setor (deve ser < 1):")
        print(A.sum(axis=0).round(3))
