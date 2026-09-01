#!/usr/bin/env python3
"""
Importa a escala de plantonistas de uma planilha Excel/CSV para o banco do Zabbix.

Fluxo:
  1. le a planilha indicada em config.ini
  2. reconhece as colunas (aceita variacoes de nome / acentos)
  3. valida datas, campos obrigatorios e sobreposicao de periodos
  4. substitui todo o conteudo da tabela plantonista_escala (DELETE + INSERT numa transacao)

Uso:
  python importar_escala.py
"""

import configparser
import sys
import unicodedata
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

CONFIG_PATH = Path(__file__).with_name("config.ini")

# Variacoes de nome de coluna aceitas -> nome canonico usado no banco.
COLMAP = {
    "nome": "nome",
    "plantonista": "nome",
    "responsavel": "nome",
    "data inicio": "data_inicio",
    "data de inicio": "data_inicio",
    "data inicial": "data_inicio",
    "inicio": "data_inicio",
    "data fim": "data_final",
    "data final": "data_final",
    "data de fim": "data_final",
    "data termino": "data_final",
    "fim": "data_final",
    "celular": "celular",
    "telefone": "celular",
    "telefone ativo": "celular",
    "fone": "celular",
    "aplicacao": "aplicacao",
    "aplicativo": "aplicacao",
    "sistema": "aplicacao",
    "app": "aplicacao",
}

REQUIRED = ["nome", "data_inicio", "data_final", "celular", "aplicacao"]


def slug(texto: str) -> str:
    """minusculas, sem acento, espacos colapsados."""
    texto = str(texto).strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def carregar_config() -> configparser.ConfigParser:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"ERRO: configuracao nao encontrada: {CONFIG_PATH}\n"
            "Copie config.example.ini para config.ini e ajuste os valores."
        )
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_PATH, encoding="utf-8")
    return cfg


def ler_planilha(caminho: str, aba) -> pd.DataFrame:
    p = Path(caminho)
    if not p.exists():
        sys.exit(f"ERRO: planilha nao encontrada: {p}")

    ext = p.suffix.lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        df = pd.read_excel(p, sheet_name=(aba or 0), dtype=str)
    elif ext == ".csv":
        df = pd.read_csv(p, dtype=str, sep=None, engine="python")
    else:
        sys.exit(f"ERRO: formato nao suportado: {ext}")

    renomear = {}
    for col in df.columns:
        canon = COLMAP.get(slug(col))
        if canon:
            renomear[col] = canon
    df = df.rename(columns=renomear)

    faltando = [c for c in REQUIRED if c not in df.columns]
    if faltando:
        sys.exit(
            f"ERRO: colunas ausentes na planilha: {faltando}\n"
            f"Colunas encontradas: {list(df.columns)}"
        )

    return df[REQUIRED].copy()


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all")

    for c in ("nome", "celular", "aplicacao"):
        df[c] = df[c].fillna("").astype(str).str.strip()

    for c in ("data_inicio", "data_final"):
        df[c] = pd.to_datetime(df[c], dayfirst=True, errors="coerce").dt.date

    problemas = []
    for i, r in df.iterrows():
        linha = i + 2  # +1 cabecalho, +1 base-1
        if not r["nome"]:
            problemas.append(f"linha {linha}: nome vazio")
        if not r["aplicacao"]:
            problemas.append(f"linha {linha}: aplicacao vazia")
        if not r["celular"]:
            problemas.append(f"linha {linha}: celular vazio")
        if pd.isna(r["data_inicio"]):
            problemas.append(f"linha {linha}: data inicio invalida")
        if pd.isna(r["data_final"]):
            problemas.append(f"linha {linha}: data final invalida")
        if (
            not pd.isna(r["data_inicio"])
            and not pd.isna(r["data_final"])
            and r["data_final"] < r["data_inicio"]
        ):
            problemas.append(f"linha {linha}: data final anterior a data inicio")

    if problemas:
        sys.exit("ERRO: planilha com problemas:\n  - " + "\n  - ".join(problemas))

    return df.reset_index(drop=True)


def checar_sobreposicao(df: pd.DataFrame) -> list[str]:
    avisos = []
    for app, g in df.groupby("aplicacao"):
        g = g.sort_values("data_inicio").reset_index(drop=True)
        for i in range(1, len(g)):
            if g.loc[i, "data_inicio"] <= g.loc[i - 1, "data_final"]:
                avisos.append(
                    f'"{app}": {g.loc[i - 1, "nome"]} '
                    f'({g.loc[i - 1, "data_inicio"]} a {g.loc[i - 1, "data_final"]}) '
                    f'sobrepoe {g.loc[i, "nome"]} '
                    f'({g.loc[i, "data_inicio"]} a {g.loc[i, "data_final"]})'
                )
    return avisos


def gravar(df: pd.DataFrame, url: str, sobreposicao_fatal: bool) -> None:
    avisos = checar_sobreposicao(df)
    if avisos:
        msg = "sobreposicao de periodos:\n  - " + "\n  - ".join(avisos)
        if sobreposicao_fatal:
            sys.exit("ERRO: " + msg)
        print("AVISO: " + msg)

    registros = df.to_dict("records")
    engine = create_engine(url)
    with engine.begin() as cx:
        cx.execute(text("DELETE FROM plantonista_escala"))
        if registros:
            cx.execute(
                text(
                    "INSERT INTO plantonista_escala "
                    "(nome, data_inicio, data_final, celular, aplicacao) "
                    "VALUES (:nome, :data_inicio, :data_final, :celular, :aplicacao)"
                ),
                registros,
            )
    print(f"OK: {len(registros)} registro(s) importado(s).")


def main() -> None:
    cfg = carregar_config()
    caminho = cfg.get("planilha", "caminho")
    aba = cfg.get("planilha", "aba", fallback="").strip() or None
    url = cfg.get("banco", "url")
    sobreposicao_fatal = cfg.getboolean("opcoes", "sobreposicao_fatal", fallback=False)

    df = ler_planilha(caminho, aba)
    df = normalizar(df)
    gravar(df, url, sobreposicao_fatal)


if __name__ == "__main__":
    main()
