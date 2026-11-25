import pandas as pd
from pathlib import Path

# Localização do projeto
raiz = Path(__file__).resolve().parents[1]

# Caminho do arquivo CSV
caminho = raiz / "data" / "raw" / "corinthians_2025.csv"

# Importação dos dados
df = pd.read_csv(
    caminho,
    encoding="utf-8-sig",
    dtype={"Data": "string", "Presença": "string"}
)

print("=" * 50)
print("CORINTHIANS ANALYTICS 2025")
print("AUDITORIA DA BASE DE DADOS")
print("=" * 50)

# Dimensões da base
print("\n1. DIMENSÕES")
print(f"Linhas: {df.shape[0]}")
print(f"Colunas: {df.shape[1]}")

# Estrutura
print("\n2. ESTRUTURA DAS COLUNAS")
df.info()

# Competições
print("\n3. COMPETIÇÕES")
print(df["Comp"].value_counts(dropna=False))

# Resultados
print("\n4. RESULTADOS")
print(df["Resultado"].value_counts(dropna=False))

# Dados ausentes
print("\n5. DADOS AUSENTES")
print(df.isnull().sum())

# Partidas duplicadas
print("\n6. POSSÍVEIS DUPLICATAS")
duplicadas = df.duplicated(
    subset=["Data", "Comp", "Oponente"],
    keep=False
)
print(df[duplicadas])

print("\nAuditoria concluída!")

# 7. VALIDACAO DOS RESULTADOS

print("\n7. VALIDACAO DOS PLACARES")

def conferir_resultado(linha):
    gf = linha["GF"]
    ga = linha["GA"]
    resultado = linha["Resultado"]

    if gf > ga:
        esperado = "W"
    elif gf == ga:
        esperado = "D"
    else:
        esperado = "L"

    return resultado == esperado


df["resultado_confere"] = df.apply(
    conferir_resultado,
    axis=1
)

print(df["resultado_confere"].value_counts())

print("\nPARTIDAS COM POSSIVEIS INCONSISTENCIAS:")

inconsistencias = df[df["resultado_confere"] == False]

print(
    inconsistencias[
        ["Data", "Comp", "Oponente", "GF", "GA", "Resultado"]
    ]
)

# 8. ANALISE DA COLUNA LOCAL

print("\n8. VALORES DA COLUNA LOCAL")

print(df["Local"].value_counts(dropna=False))

# 9. PADRONIZACAO DO MANDO DE CAMPO

df["Local"] = df["Local"].replace({
    "Início": "Mandante",
    "Afastado": "Visitante"
})

print("\n9. MANDO DE CAMPO PADRONIZADO")
print(df["Local"].value_counts())

# 10. ANALISE DOS HORARIOS

print("\n10. HORARIOS DAS PARTIDAS")

print(df["Tempo"].value_counts().sort_index())

# 11. PADRONIZACAO DOS HORARIOS

df["Tempo"] = df["Tempo"].str.replace(
    "h", ":", regex=False
)

print("\n11. HORARIOS PADRONIZADOS")
print(df["Tempo"].value_counts().sort_index())

# 12. INVESTIGACAO DE HORARIOS COM PARENTESES

print("\n12. PARTIDAS COM HORARIOS ALTERNATIVOS")

horarios_alternativos = df[
    df["Tempo"].str.contains(r"\(", na=False)
]

print(
    horarios_alternativos[
        ["Data", "Comp", "Oponente", "Tempo"]
    ]
)

# 13. SEPARACAO DOS FUSOS HORARIOS

df["Tempo_original"] = df["Tempo"]

df["Tempo_local"] = df["Tempo"].str.extract(
    r"^(\d{2}:\d{2})"
)

df["Tempo_Brasilia"] = df["Tempo"].str.extract(
    r"\((\d{2}:\d{2})\)"
)

df["Tempo_Brasilia"] = df["Tempo_Brasilia"].fillna(
    df["Tempo_local"]
)

print("\n13. HORARIOS SEPARADOS")

print(
    df.loc[
        df["Tempo_original"].str.contains(r"\(", na=False),
        ["Oponente", "Tempo_local", "Tempo_Brasilia"]
    ]
)

# 14. ANALISE DOS NOMES DOS ADVERSARIOS

print("\n14. ADVERSARIOS CADASTRADOS")

for adversario in sorted(df["Oponente"].unique()):
    print(adversario)

# 15. PADRONIZACAO DOS ADVERSARIOS

df["Oponente"] = df["Oponente"].replace({
    "ar Huracán": "Huracán",
    "co América Cali": "América de Cali",
    "comprar Corrida": "Racing Club",
    "ec Barcelona": "Barcelona SC",
    "ve UCV": "UCV"
})

print("\n15. ADVERSARIOS PADRONIZADOS")

for adversario in sorted(df["Oponente"].unique()):
    print(adversario)

# 16. ANALISE DAS FORMACOES TATICAS

print("\n16. FORMACOES UTILIZADAS PELO CORINTHIANS")

print(df["Formação"].value_counts())

# 17. PADRONIZACAO DAS FORMACOES

df["Formação"] = df["Formação"].str.replace(
    "◆", "", regex=False
).str.strip()

print("\n17. FORMACOES PADRONIZADAS")

print(df["Formação"].value_counts())

# 18. DESEMPENHO POR FORMACAO

desempenho_formacao = df.groupby("Formação").agg(
    Jogos=("Resultado", "count"),
    Vitorias=("Resultado", lambda x: (x == "W").sum()),
    Empates=("Resultado", lambda x: (x == "D").sum()),
    Derrotas=("Resultado", lambda x: (x == "L").sum()),
    Gols_Marcados=("GF", "sum"),
    Gols_Sofridos=("GA", "sum")
)

desempenho_formacao["Aproveitamento_%"] = (
    (desempenho_formacao["Vitorias"] * 3 +
     desempenho_formacao["Empates"]) /
    (desempenho_formacao["Jogos"] * 3) * 100
).round(2)

desempenho_formacao = desempenho_formacao.sort_values(
    by="Aproveitamento_%",
    ascending=False
)

print("\n18. DESEMPENHO POR FORMACAO")
print(desempenho_formacao)

# 19. GRAFICO DE APROVEITAMENTO POR FORMACAO

import matplotlib.pyplot as plt

desempenho_formacao = desempenho_formacao.sort_values(
    by="Aproveitamento_%"
)

plt.figure(figsize=(10, 6))

plt.barh(
    desempenho_formacao.index,
    desempenho_formacao["Aproveitamento_%"]
)

plt.title("Aproveitamento por Formação - Corinthians 2025")
plt.xlabel("Aproveitamento (%)")
plt.ylabel("Formação")

plt.tight_layout()
plt.show()

# 20. EXPORTACAO DAS ANALISES

pasta_saida = raiz / "data" / "processed"

pasta_saida.mkdir(parents=True, exist_ok=True)

desempenho_formacao.to_csv(
    pasta_saida / "desempenho_formacao.csv",
    encoding="utf-8-sig"
)

df.to_csv(
    pasta_saida / "corinthians_2025_tratado.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n20. ARQUIVOS EXPORTADOS COM SUCESSO!")

