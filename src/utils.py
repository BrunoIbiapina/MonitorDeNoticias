from collections import Counter
from typing import Optional

def sentiment_counts(series):
    try:
        return dict(Counter(series.dropna().tolist()))
    except Exception:
        try:
            return dict(Counter(list(series)))
        except Exception:
            return {}

def add_clickable_links(df, title_col: str, link_col: str, new_col: str = "title_link"):
    import pandas as pd
    try:
        out = df.copy()
        def _mk(row):
            t = row.get(title_col)
            l = row.get(link_col)
            t = t if isinstance(t, str) and t.strip() else "(sem título)"
            l = l if isinstance(l, str) and l.strip() else ""
            return f"[{t}]({l})" if l else t
        out[new_col] = out.apply(_mk, axis=1)
        return out
    except Exception:
        try:
            out = pd.DataFrame(df)
            out[new_col] = out[title_col].fillna("(sem título)")
            return out
        except Exception:
            return df

def make_wordcloud_image(text: str, width: int = 900, height: int = 500) -> Optional["Image.Image"]:
    if not text or not isinstance(text, str):
        text = "sem dados"
    try:
        from wordcloud import WordCloud
        wc = WordCloud(width=width, height=height, background_color="white")
        image = wc.generate(text).to_image()
        return image
    except Exception:
        return None