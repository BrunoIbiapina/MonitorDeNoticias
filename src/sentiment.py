
from __future__ import annotations
import pandas as pd

POS = {
    "avanco","avanço","sucesso","beneficio","inovacao","oportunidade","melhoria",
    "positivo","crescimento","lider","premio","recorde","aprovado","parceria",
    "investimento","emprego","eficiencia","seguranca","educacao","saude","desenvolvimento"
}
NEG = {
    "crise","queda","fracasso","falha","problema","risco","ameaça","ameaca","vulneravel",
    "negativo","crime","golpe","investigacao","vazamento","demissao","corte","perda","atraso",
    "erro","polêmica","polemica","prejuizo","ineficiencia"
}

SENTIMENT_ORDER = ["Positivo", "Neutro", "Negativo"]

def score_text(text: str) -> int:
    if not text:
        return 0
    tokens = set(text.split())
    pos = len(tokens.intersection(POS))
    neg = len(tokens.intersection(NEG))
    return pos - neg

def to_label(score: int) -> str:
    if score > 0: return "Positivo"
    if score < 0: return "Negativo"
    return "Neutro"

def classify_text_series(series: pd.Series) -> pd.Series:
    return series.fillna("").map(score_text).map(to_label)