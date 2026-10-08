"""Comparación de especificaciones para la sensibilidad por rama al choque de incertidumbre comercial.

Variables de resultado (variación anual, Δ12 log, en el mes t+h):
  produccion, empleo, horas (EMIM, 2018-), exportaciones (Banxico, 2019-), importaciones_eeuu (EE.UU. desde México, Census, 2013-).
Regresión por rama i y horizonte h (−6..−1 placebos; 0..12 efectos):
  Δ12 log y(i,t+h) = c + Σ_l β_l s_{t−l} + controles + e        (β_0 = efecto de interés)
Especificaciones de controles (todas incluyen s_{t−1}):
  E0  macro: Δ12 log IP_EEUU_t, Δ12 log TC_{t−1}, Δ12 log VIX_{t−1}, Δ12 arancel efectivo de la rama en t+h
  E1  E0 + Δ12 de la propia variable en t−1
  E2  E0 + Δ12 de producción, empleo y horas en t−1                       (solo resultados EMIM)
  E3  E2 + Δ12 de exportaciones a EE.UU. (importaciones del Census) en t−1 (solo resultados EMIM)
  E4  E3 con rezagos t−1..t−3                                              (solo resultados EMIM)
  E5  E3 + choque en t−2 y t−3                                             (solo resultados EMIM)
  E3b E2 + Δ12 de exportaciones de Banxico en t−1 (muestra más corta: 2020-)
  T0/T1/T2 para comercio: macro; + propio rezago t−1; + propios rezagos t−1..t−3
Todas las especificaciones de un mismo resultado se estiman en la MISMA muestra (la que exige la más grande del grupo),
salvo E3b, que tiene su propia muestra. Regla de selección fijada antes de ver los efectos:
  1) placebo válido: la respuesta media de las ramas en h = −6..−1 no es significativa (p > 0.10);
  2) entre las válidas, la de menor BIC promedio (mejor ajuste de los controles).
Inferencia: 1,000 permutaciones de la serie del choque, comunes a ramas y horizontes. Heterogeneidad y encogimiento como en 03.

Uso (desde code/Python):  python 04_especificaciones_por_rama.py
Salidas: outputs/tables/especificaciones_resumen.csv, outputs/tables/sensibilidad_por_rama_mejor.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

RAIZ = Path(__file__).resolve().parents[1].parent
RAW = RAIZ / "data/raw"
RNG = np.random.default_rng(20261008)
N_PERM = 1000
H_PRE, H_POST = list(range(-6, 0)), list(range(0, 13))
PANDEMIA = (pd.Timestamp("2020-03-01"), pd.Timestamp("2021-06-01"))
FIN = pd.Timestamp("2026-07-01")

# ------------------------------------------------------------------ datos
base = pd.read_excel(RAIZ / "data/processed/base_incertidumbre_comercial_mexico.xlsx", sheet_name="base_integrada", dtype={"rama": str})
base["mes"] = pd.to_datetime(base.mes)
ramas = sorted(base.rama.unique())
cen = pd.read_csv(RAW / "aranceles/aranceles_mex_naics4.csv", dtype={"naics": str}, parse_dates=["fecha"])
cen = cen[cen.naics.isin(ramas)].rename(columns={"naics": "rama", "fecha": "mes"})
tc_raw = pd.read_excel(RAW / "controles_macroeconomicos/banxico_tipo_cambio_fix_mensual.xlsx", header=None)
f = tc_raw.index[tc_raw[0].astype(str).eq("Fecha")][0]
tc = tc_raw.iloc[f + 1:].dropna()
tc = pd.Series(pd.to_numeric(tc[1]).values, index=pd.to_datetime(tc[0]).dt.to_period("M").dt.to_timestamp()).replace(0, np.nan)
vix = (pd.read_csv(RAW / "controles_macroeconomicos/fred_vix_diario.csv", na_values=[".", ""], parse_dates=["observation_date"])
       .dropna().set_index("observation_date").VIXCLS.resample("MS").mean())
ip = pd.read_csv(RAW / "produccion_estados_unidos/fred_indpro_mensual.csv", parse_dates=["observation_date"]).set_index("observation_date").INDPRO
choque = pd.read_csv(RAIZ / "outputs/tables/choque_tpu_limpio.csv", parse_dates=["mes"]).set_index("mes").choque_principal

meses = pd.date_range("2013-01-01", FIN, freq="MS")
P = pd.MultiIndex.from_product([ramas, meses], names=["rama", "mes"]).to_frame(index=False)
P = P.merge(base[["rama", "mes", "emim_valor_produccion_real", "emim_personal_ocupado", "emim_horas_trabajadas", "expo_valor_real"]],
            on=["rama", "mes"], how="left", validate="one_to_one")
P = P.merge(cen[["rama", "mes", "valor_importado", "tasa_efectiva"]], on=["rama", "mes"], how="left", validate="one_to_one")
P = P.merge(pd.DataFrame({"lip": np.log(ip), "ltc": np.log(tc), "lvix": np.log(vix)}).rename_axis("mes").reset_index(), on="mes", how="left", validate="many_to_one")
ceros = {c: int((P[c] == 0).sum()) for c in ["expo_valor_real", "valor_importado"]}
print("Valores en cero (quedan NA al tomar log):", ceros)
NIV = {"produccion": "emim_valor_produccion_real", "empleo": "emim_personal_ocupado", "horas": "emim_horas_trabajadas",
       "exportaciones": "expo_valor_real", "importaciones_eeuu": "valor_importado"}
for k, v in NIV.items():
    P["l_" + k] = np.log(P[v].where(P[v] > 0))
P["arancel"] = 100 * P.tasa_efectiva
P = P.sort_values(["rama", "mes"]).reset_index(drop=True)

def en_fecha(col, k):
    aux = P[["rama", "mes", col]].assign(mes=P.mes - pd.DateOffset(months=k))
    return P[["rama", "mes"]].merge(aux, on=["rama", "mes"], how="left", validate="one_to_one")[col].values
for c in ["l_" + k for k in NIV] + ["lip", "ltc", "lvix", "arancel"]:
    P["d12_" + c] = P[c] - en_fecha(c, -12)
D12 = lambda k: "d12_l_" + k

MESES_S = pd.date_range("2012-09-01", FIN, freq="MS")
POS = pd.Series(np.arange(len(MESES_S)), index=MESES_S)
s = (choque.reindex(MESES_S)).values
assert not np.isnan(s).any()
PERM = np.array([RNG.permutation(len(MESES_S)) for _ in range(N_PERM)])
S_ALL = np.vstack([s, s[PERM]])                                       # (1 + N_PERM, T)
pos = {l: (P.mes - pd.DateOffset(months=l)).map(POS).fillna(-1).astype(int).values for l in range(4)}

_REZ = {}
def rez(col, l):
    if (col, l) not in _REZ:
        _REZ[(col, l)] = en_fecha(col, -l)
    return _REZ[(col, l)]

def controles(y, spec):
    W = {"ip": P.d12_lip.values, "tc_l1": rez("d12_ltc", 1), "vix_l1": rez("d12_lvix", 1)}
    emim = ["produccion", "empleo", "horas"]
    if spec in ("E1", "T1", "T2"):
        for l in (range(1, 4) if spec == "T2" else [1]):
            W[f"{y}_l{l}"] = rez(D12(y), l)
    if spec in ("E2", "E3", "E4", "E5", "E3b"):
        for v in emim:
            for l in (range(1, 4) if spec == "E4" else [1]):
                W[f"{v}_l{l}"] = rez(D12(v), l)
    if spec in ("E3", "E4", "E5"):
        for l in (range(1, 4) if spec == "E4" else [1]):
            W[f"imp_l{l}"] = rez(D12("importaciones_eeuu"), l)
    if spec == "E3b":
        W["expo_l1"] = rez(D12("exportaciones"), 1)
    return W

_CACHE = {}
def preparar(y, spec, h):
    if (y, spec, h) in _CACHE:
        return _CACHE[(y, spec, h)]
    W = controles(y, spec)
    W["arancel_h"] = rez("d12_arancel", -h)
    yh = rez(D12(y), -h)
    lags_s = [0, 1, 2, 3] if spec == "E5" else [0, 1]
    _CACHE[(y, spec, h)] = (yh, W, lags_s)
    return yh, W, lags_s

ESPECS = {"produccion": ["E0", "E1", "E2", "E3", "E4", "E5"], "empleo": ["E0", "E1", "E2", "E3", "E4", "E5"],
          "horas": ["E0", "E1", "E2", "E3", "E4", "E5"], "exportaciones": ["T0", "T1", "T2"], "importaciones_eeuu": ["T0", "T1", "T2"]}

def estimar(y, spec, excluir_pandemia, muestra_comun):
    """Devuelve, por rama, la media de β_0 en h=0..12 y en h=−6..−1 (real y permutadas), y el BIC medio."""
    out, bics = [], []
    for rama in ramas:
        sel = (P.rama == rama).values
        b = {}
        for h in H_PRE + H_POST:
            yh, W, lags_s = preparar(y, spec, h)
            Wm = np.column_stack([np.ones(len(P)), *W.values()])
            ok = sel & ~np.isnan(yh) & np.all([pos[l] >= 0 for l in lags_s], axis=0)
            usa = ~np.all(np.isnan(Wm[sel]), axis=0)                  # columnas sin ningún dato en la rama (p. ej., arancel en 3328) se omiten
            Wm = Wm[:, usa]
            ok &= ~np.isnan(Wm).any(axis=1)
            if muestra_comun is not None:
                ok &= muestra_comun[h]
            if excluir_pandemia:
                ini = P.mes + pd.DateOffset(months=min(h - 12, -1)); fin = P.mes + pd.DateOffset(months=max(h, 0))
                ok &= ~((ini <= PANDEMIA[1]) & (fin >= PANDEMIA[0])).values
            idx = np.flatnonzero(ok)
            if len(idx) < 30:
                b = None; break
            Q, _ = np.linalg.qr(Wm[idx])
            res = lambda A: A - Q @ (Q.T @ A)
            yt = res(yh[idx])
            Xs = np.stack([res(S_ALL[:, pos[l][idx]].T) for l in lags_s])   # (k, n, 1+N)
            XtX = np.einsum("knd,jnd->dkj", Xs, Xs)
            Xty = np.einsum("knd,n->dk", Xs, yt)
            beta = np.linalg.solve(XtX, Xty[..., None])[..., 0]            # (1+N, k)
            b[h] = beta[:, 0]
            if h >= 0:
                e = yt - Xs[:, :, 0].T @ beta[0]
                n, kk = len(idx), Wm.shape[1] + len(lags_s)
                bics.append(n * np.log(e @ e / n) + kk * np.log(n))
        if b is None:
            continue
        post = 100 * np.mean([b[h] for h in H_POST], axis=0)
        pre = 100 * np.mean([b[h] for h in H_PRE], axis=0)
        out.append(dict(rama=rama, sens=post[0], nulos=post[1:], pre=pre[0], nulos_pre=pre[1:]))
    return pd.DataFrame(out), float(np.mean(bics))

def mascara_comun(y, specs, excluir_pandemia):
    """Filas válidas para TODAS las especificaciones del grupo (para comparar BIC en la misma muestra)."""
    m = {}
    for h in H_PRE + H_POST:
        ok = np.ones(len(P), bool)
        for spec in specs:
            yh, W, lags_s = preparar(y, spec, h)
            Wm = np.column_stack([*W.values()])
            # el arancel puede faltar en toda una rama (3328): no restringe la muestra común
            cols = [c for c in W if c != "arancel_h"]
            ok &= ~np.isnan(yh) & ~np.isnan(np.column_stack([W[c] for c in cols])).any(axis=1)
            ok &= np.all([pos[l] >= 0 for l in lags_s], axis=0)
        m[h] = ok
    return m

def resumen(df):
    """Media común y heterogeneidad (desviaciones con incertidumbre de permutación), y placebo."""
    N = np.vstack(df.nulos.values); b = df.sens.values
    mu, mu0 = b.mean(), N.mean(0)
    D = N - mu0; s2 = D.var(1); Qo = np.sum((b - mu) ** 2 / s2); Qn = np.sum(D ** 2 / s2[:, None], 0)
    Np = np.vstack(df.nulos_pre.values); pre, pre0 = df.pre.mean(), Np.mean(0)
    return dict(efecto_medio=mu, ee=mu0.std(), p=float(np.mean(np.abs(mu0) >= abs(mu))), p_heterogeneidad=float(np.mean(Qn >= Qo)),
                placebo_medio=pre, p_placebo=float(np.mean(np.abs(pre0) >= abs(pre))), ramas=len(df))

filas, guardado = [], {}
for y, specs in ESPECS.items():
    for excl, etq in [(True, "sin pandemia"), (False, "completa")]:
        mc = mascara_comun(y, specs, excl)
        for spec in specs:
            df, bic = estimar(y, spec, excl, mc)
            r = resumen(df); filas.append(dict(variable=y, muestra=etq, especificacion=spec, bic_medio=bic, **r))
            guardado[(y, etq, spec)] = df
            print(f"{y:18s} {etq:12s} {spec:3s} | BIC {bic:9.1f} | efecto {r['efecto_medio']:+.2f} (ee {r['ee']:.2f}, p {r['p']:.2f}) | "
                  f"placebo {r['placebo_medio']:+.2f} (p {r['p_placebo']:.2f}) | heterog. p {r['p_heterogeneidad']:.2f} | ramas {r['ramas']}", flush=True)
        if y in ("produccion", "empleo", "horas"):
            df, bic = estimar(y, "E3b", excl, None)
            r = resumen(df); filas.append(dict(variable=y, muestra=etq, especificacion="E3b (muestra 2020-)", bic_medio=bic, **r))
            print(f"{y:18s} {etq:12s} E3b| BIC {bic:9.1f} (otra muestra) | efecto {r['efecto_medio']:+.2f} (ee {r['ee']:.2f}, p {r['p']:.2f}) | "
                  f"placebo {r['placebo_medio']:+.2f} (p {r['p_placebo']:.2f}) | heterog. p {r['p_heterogeneidad']:.2f}", flush=True)

tab = pd.DataFrame(filas)
comparables = tab[~tab.especificacion.str.startswith("E3b")]
validas = comparables[comparables.p_placebo > 0.10]
mejor = validas.loc[validas.groupby(["variable", "muestra"]).bic_medio.idxmin()]
tab["elegida"] = tab.index.isin(mejor.index)
tab.to_csv(RAIZ / "outputs/tables/especificaciones_resumen.csv", index=False)
print("\nEspecificación elegida (placebo p > 0.10 y menor BIC):")
print(mejor[["variable", "muestra", "especificacion", "efecto_medio", "ee", "p", "p_heterogeneidad", "placebo_medio", "p_placebo"]].round(3).to_string(index=False))

# Sensibilidad por rama con la especificación elegida (encogimiento como en 03)
info = base.groupby("rama").agg(rama_nombre=("rama_nombre", "first"), coef_exportacion=("mip_coef_exportacion_2018", "first"))
res = []
for _, m in mejor.iterrows():
    df = guardado[(m.variable, m.muestra, m.especificacion)].merge(info, left_on="rama", right_index=True)
    N = np.vstack(df.nulos.values); mu0 = N.mean(0); mu = df.sens.mean()
    d, D = df.sens.values - mu, N - mu0; s2 = D.var(1)
    Z = np.column_stack([np.ones(len(df)), df.coef_exportacion - df.coef_exportacion.mean()])
    t2 = 0.0
    for _ in range(500):
        w = 1 / (s2 + t2); g = np.linalg.solve(Z.T @ (Z * w[:, None]), Z.T @ (w * d))
        nuevo = max(0.0, t2 + (np.sum(w * (d - Z @ g) ** 2) - (len(d) - 2)) / np.sum(w))
        if abs(nuevo - t2) < 1e-12: break
        t2 = nuevo
    lam = t2 / (t2 + s2); pred = Z @ g
    post = mu + pred + lam * (d - pred); sd = np.sqrt(mu0.var() + lam * s2)
    res.append(df.drop(columns=["nulos", "nulos_pre"]).assign(variable=m.variable, muestra=m.muestra, especificacion=m.especificacion,
               ee=np.sqrt(s2 + mu0.var()), sens_post=post, sd_post=sd, prob_negativo=norm.cdf(-post / sd), tau=np.sqrt(t2)))
pd.concat(res).to_csv(RAIZ / "outputs/tables/sensibilidad_por_rama_mejor.csv", index=False)
print("Guardado: outputs/tables/especificaciones_resumen.csv y outputs/tables/sensibilidad_por_rama_mejor.csv")
