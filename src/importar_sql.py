
import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# 1. Caminho do CSV tratado
caminho_csv = "data/processed/corinthians_2025_tratado.csv"

# 2. Carregar os dados
df = pd.read_csv(caminho_csv)

# 3. Preparar as datas
def converter_data(valor):
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return pd.to_datetime(valor, format=formato)
        except (ValueError, TypeError):
            continue
    return pd.NaT

df["Data"] = df["Data"].apply(converter_data)

if df["Data"].isna().any():
    raise ValueError("Existem datas inválidas no CSV. Verifique antes de importar.")

# 4. Converter público para número
df["Presença"] = (
    df["Presença"]
    .astype("string")
    .str.replace(".", "", regex=False)
)

df["Presença"] = pd.to_numeric(df["Presença"], errors="coerce")

# 5. Selecionar e renomear colunas para o SQL Server
df_sql = df[
    [
        "Data", "Comp", "Local", "Resultado",
        "GF", "GA", "Oponente", "Poss",
        "Presença", "Formação", "Árbitro"
    ]
].copy()

df_sql = df_sql.rename(columns={
    "Comp": "Competicao",
    "Local": "Mando",
    "GF": "Gols_Marcados",
    "GA": "Gols_Sofridos",
    "Oponente": "Adversario",
    "Poss": "Posse_Bola",
    "Presença": "Publico",
    "Formação": "Formacao",
    "Árbitro": "Arbitro"
})

# 6. Conectar ao SQL Server
url = URL.create(
    "mssql+pyodbc",
    host="localhost",
    database="CorinthiansAnalytics",
    query={
        "driver": "ODBC Driver 17 for SQL Server",
        "trusted_connection": "yes"
    }
)

engine = create_engine(url)

# 7. Verificar se já existem registros
with engine.connect() as conexao:
    quantidade = conexao.exec_driver_sql(
        "SELECT COUNT(*) FROM dbo.Partidas"
    ).scalar()

if quantidade > 0:
    raise RuntimeError(
        f"A tabela já possui {quantidade} registros. "
        "Importação cancelada para evitar duplicidade."
    )

# 8. Importar os dados
df_sql.to_sql(
    "Partidas",
    con=engine,
    schema="dbo",
    if_exists="append",
    index=False
)

print(f"Importação concluída! {len(df_sql)} partidas enviadas.")
