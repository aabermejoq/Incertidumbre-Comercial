"""Sensibilidad de cada rama a un choque limpio de incertidumbre comercial.

Paso 1. Choque limpio (VAR recursivo mensual, 1990-2026). Variables en logaritmos:
        producción industrial de EE.UU., VIX y TPU, con 6 rezagos.
        - Choque A (principal, conservador): innovación del TPU ortogonal a los rezagos de todo y a los valores
          contemporáneos de las demás variables (TPU al final del orden de Cholesky).
        - Choque B (robustez): innovación del TPU ortogonal solo a los rezagos (TPU primero en el orden).
        Ambos se estandarizan con su desviación estándar de 2018-01 a 2026-07.
Paso 2. Local projection por rama (h = 0..12), con controles propios de la rama:
        log y(t+h) − log y(t−1) = c + mes calendario + β_h s_t + θ s_{t−1} + ρ1 Δlog y(t−1) + ρ2 Δlog y(t−2)
                                  + Δ12 log IP_EEUU_t + Δ12 log TC_{t−1} + Δ12 log VIX_{t−1}
                                  + Δ arancel efectivo de la rama (t−1 → t+h) + Δ log días hábiles + e
        Sensibilidad de la rama = promedio de β_h en h = 0..12 (% de cambio en el nivel por 1 desv. est.).
        Error estándar y valor p por permutación de la serie del choque (1,000 permutaciones comunes).
Paso 3. Encogimiento empírico de Bayes: β̂_i ~ N(θ_i, s_i²), θ_i ~ N(Z_i'γ, τ²), con Z = [1, coeficiente de
        exportación MIP 2018, arancel efectivo medio 2018-2019]. τ² por Paule-Mandel. Posterior por rama:
        media, desviación estándar, intervalo al 90% y probabilidad de efecto negativo.

Uso (desde code/Python):  python 03_sensibilidad_por_rama.py
Salidas: outputs/tables/choque_tpu_limpio.csv, outputs/tables/sensibilidad_por_rama.csv
"""
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

RAIZ = Path(__file__).resolve().parents[1].parent
RAW = RAIZ / "data/raw"
RNG = np.random.default_rng(20261008)
N_PERM, P_VAR, H = 1000, 6, list(range(13))
PANDEMIA = (pd.Timestamp("2020-03-01"), pd.Timestamp("2021-06-01"))
VENTANA = (pd.Timestamp("2018-01-01"), pd.Timestamp("2026-07-01"))

# ---------------------------------------------------------------- Paso 1: series mensuales y choque limpio
def mensual(s):
    s.index = pd.to_datetime(s.index).to_period("M").to_timestamp()
    return s.astype(float)

tpu = mensual(pd.read_excel(RAW / "incertidumbre/tpu_caldara_iacoviello.xlsx", sheet_name="TPU_MONTHLY").set_index("DATE").TPU)
vix_d = pd.read_csv(RAW / "controles_macroeconomicos/fred_vix_diario.csv", na_values=[".", ""], parse_dates=["observation_date"])
vix = vix_d.dropna().set_index("observation_date").VIXCLS.resample("MS").mean()
ip = mensual(pd.read_csv(RAW / "produccion_estados_unidos/fred_indpro_mensual.csv", parse_dates=["observation_date"]).set_index("observation_date").INDPRO)

V = pd.DataFrame({"ip": ip, "vix": vix, "tpu": tpu}).dropna()
OTRAS = ["ip", "vix"]
V = np.log(V)
X = pd.concat({f"{c}_l{l}": V[c].shift(l) for c in V for l in range(1, P_VAR + 1)}, axis=1)
d = pd.concat([V, X], axis=1).dropna()
rez = sm.OLS(d.tpu, sm.add_constant(d[X.columns])).fit()
contemp = sm.OLS(d.tpu, sm.add_constant(d[list(X.columns) + OTRAS])).fit()
choques = pd.DataFrame({"choque_A_tpu_ultimo": contemp.resid, "choque_B_tpu_primero": rez.resid})
viejo = pd.read_csv(RAIZ / "outputs/tables/sorpresa_tpu.csv", parse_dates=["mes"]).set_index("mes").sorpresa_tpu
en_v = choques.loc[VENTANA[0]:VENTANA[1]]
ESC = en_v.std()
choques_std = choques / ESC
print(f"VAR: {d.index.min():%Y-%m} a {d.index.max():%Y-%m} ({len(d)} meses), {P_VAR} rezagos")
print(f"R² TPU solo con rezagos: {rez.rsquared:.3f}; con valores contemporáneos de IP y VIX: {contemp.rsquared:.3f}")
print("Parte de la innovación del TPU explicada por las otras variables en el mismo mes:",
      f"{1 - contemp.resid.var() / rez.resid.var():.1%}")
print("Coeficientes contemporáneos (log):", contemp.params[OTRAS].round(3).to_dict(), "| valores p:", contemp.pvalues[OTRAS].round(3).to_dict())
print("1 desv. est. del choque (2018-2026), en log:", choques.loc[VENTANA[0]:VENTANA[1]].std().round(3).to_dict())
print("Correlaciones 2018-2026:", pd.concat([en_v, viejo.rename("sorpresa_anterior")], axis=1).dropna().corr().round(3).iloc[0].to_dict())
choques_std.rename_axis("mes").to_csv(RAIZ / "outputs/tables/choque_tpu_limpio.csv")

# ---------------------------------------------------------------- Paso 2: LP por rama
base = pd.read_excel(RAIZ / "data/processed/base_incertidumbre_comercial_mexico.xlsx", sheet_name="base_integrada", dtype={"rama": str})
base["mes"] = pd.to_datetime(base.mes)
base = base.sort_values(["rama", "mes"]).reset_index(drop=True)

def pascua(a):
    b, c = divmod(a, 100); d_, e = divmod(b, 4); f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * (a % 19) + b - d_ - g + 15) % 30; i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a % 19 + 11 * h + 22 * l) // 451
    return date(a, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)
def lunes_n(a, mes, n):
    d0 = date(a, mes, 1); return d0 + timedelta(days=(7 - d0.weekday()) % 7 + 7 * (n - 1))
fer = set()
for a in range(2015, 2028):
    fer |= {date(a, 1, 1), lunes_n(a, 2, 1), lunes_n(a, 3, 3), date(a, 5, 1), date(a, 9, 16), lunes_n(a, 11, 3), date(a, 12, 25),
            pascua(a) - timedelta(days=3), pascua(a) - timedelta(days=2)}
fer |= {date(2018, 12, 1), date(2024, 10, 1)}
dias = pd.date_range("2015-01-01", "2027-12-31", freq="D")
LDH = np.log(pd.Series([(x.weekday() < 5) and (x.date() not in fer) for x in dias], index=dias).resample("MS").sum().astype(float))

def en_fecha(col, k):
    aux = base[["rama", "mes", col]].assign(mes=base.mes - pd.DateOffset(months=k))
    return base[["rama", "mes"]].merge(aux, on=["rama", "mes"], how="left", validate="one_to_one")[col].values

NIV = {"produccion": "emim_valor_produccion_real", "empleo": "emim_personal_ocupado", "horas": "emim_horas_trabajadas"}
for k, v in NIV.items():
    base["l_" + k] = np.log(base[v].astype(float))
    base["dl1_" + k] = base["l_" + k] - en_fecha("l_" + k, -1)
base["arancel_pp"] = 100 * base.eeuu_imp_mx_tasa_efectiva
for c, v in [("lip", "eeuu_ip_total"), ("ltc", "tc_fix"), ("lvix", "vix_promedio_mensual")]:
    base[c] = np.log(base[v])
    base["d12_" + c] = base[c] - en_fecha(c, -12)

MESES_S = pd.date_range(VENTANA[0] - pd.DateOffset(months=2), VENTANA[1], freq="MS")
POS = pd.Series(np.arange(len(MESES_S)), index=MESES_S)
PERM = np.array([RNG.permutation(len(MESES_S)) for _ in range(N_PERM)])
p0 = base.mes.map(POS).fillna(-1).astype(int).values
p1 = (base.mes - pd.DateOffset(months=1)).map(POS).fillna(-1).astype(int).values
CAL = pd.get_dummies(base.mes.dt.month, prefix="m", drop_first=True, dtype=float).values

PRECOMP = {}
for k in NIV:
    W = {"dl1_l1": en_fecha("dl1_" + k, -1), "dl1_l2": en_fecha("dl1_" + k, -2), "ip": base.d12_lip.values,
         "tc_l1": en_fecha("d12_ltc", -1), "vix_l1": en_fecha("d12_lvix", -1)}
    PRECOMP[k] = {h: dict(W=W, y=en_fecha("l_" + k, h) - en_fecha("l_" + k, -1),
                          ar=en_fecha("arancel_pp", h) - en_fecha("arancel_pp", -1),
                          dh=((base.mes + pd.DateOffset(months=h)).map(LDH) - (base.mes - pd.DateOffset(months=1)).map(LDH)).values)
                  for h in H}

def sensibilidad_rama(rama, y, s, excluir_pandemia):
    sel = (base.rama == rama).values
    S = np.vstack([s, s[PERM]])
    b_real, b_perm, n_h = [], [], []
    for h in H:
        P = PRECOMP[y][h]
        cols = [np.ones(len(base)), CAL.T, *P["W"].values(), P["dh"]]
        usa_ar = not np.all(np.isnan(P["ar"][sel]))
        if usa_ar:
            cols.append(P["ar"])
        Wm = np.column_stack([np.atleast_2d(c).T if np.ndim(c) == 1 else c.T for c in cols])
        ok = sel & ~np.isnan(P["y"]) & ~np.isnan(Wm).any(axis=1) & (p1 >= 0) & (p0 >= 0)
        if excluir_pandemia:
            ini, fin = base.mes - pd.DateOffset(months=1), base.mes + pd.DateOffset(months=h)
            ok &= ~((ini <= PANDEMIA[1]) & (fin >= PANDEMIA[0])).values
        idx = np.flatnonzero(ok)
        if len(idx) < 40:
            return None
        Q, _ = np.linalg.qr(Wm[idx])
        res = lambda A: A - Q @ (Q.T @ A)
        yt = res(P["y"][idx])
        X0, X1 = res(S[:, p0[idx]].T), res(S[:, p1[idx]].T)
        a, b, c = (X0 * X0).sum(0), (X0 * X1).sum(0), (X1 * X1).sum(0)
        d0, d1 = (X0 * yt[:, None]).sum(0), (X1 * yt[:, None]).sum(0)
        beta = (c * d0 - b * d1) / (a * c - b * b)
        b_real.append(beta[0]); b_perm.append(beta[1:]); n_h.append(len(idx))
    est = 100 * np.mean(b_real)
    nulos = 100 * np.mean(b_perm, axis=0)
    return dict(sens=est, se=nulos.std(), p_perm=float(np.mean(np.abs(nulos) >= abs(est))), meses_h0=n_h[0], meses_h12=n_h[-1],
                usa_control_arancel=usa_ar, nulos=nulos, **{f"b_h{h}": 100 * b for h, b in zip(H, b_real)})

# ---------------------------------------------------------------- Paso 3: encogimiento empírico de Bayes
info = base.groupby("rama").agg(rama_nombre=("rama_nombre", "first"), coef_exportacion=("mip_coef_exportacion_2018", "first"))
info["arancel_medio_2018_2019"] = base[base.mes.dt.year.isin([2018, 2019])].groupby("rama").arancel_pp.mean()

def eb(df):
    """Sensibilidad = media común + desviación propia. Los errores de las ramas están correlacionados (mismo choque,
    mismos meses), así que la incertidumbre de ambas piezas sale de las permutaciones comunes, que conservan esa
    correlación. El encogimiento (Paule-Mandel) se aplica a las desviaciones."""
    b = df.sens.values
    N = np.vstack(df.nulos.values)                       # (ramas, permutaciones)
    mu, mu_null = b.mean(), N.mean(axis=0)
    se_mu, p_mu = mu_null.std(), float(np.mean(np.abs(mu_null) >= abs(mu)))
    dlt, D = b - mu, N - mu_null
    s2 = D.var(axis=1)
    Qobs = np.sum(dlt ** 2 / s2)
    Qnull = np.sum(D ** 2 / s2[:, None], axis=0)
    p_het = float(np.mean(Qnull >= Qobs))
    Z = np.column_stack([np.ones(len(df)), df.coef_exportacion - df.coef_exportacion.mean(),
                         df.arancel_medio_2018_2019.fillna(df.arancel_medio_2018_2019.median()) - df.arancel_medio_2018_2019.mean()])
    k, t2 = Z.shape[1], 0.0
    for _ in range(500):
        w = 1 / (s2 + t2)
        Vg = np.linalg.inv(Z.T @ (Z * w[:, None])); g = Vg @ (Z.T @ (w * dlt))
        Qs = np.sum(w * (dlt - Z @ g) ** 2)
        nuevo = max(0.0, t2 + (Qs - (len(b) - k)) / np.sum(w))
        if abs(nuevo - t2) < 1e-12:
            break
        t2 = nuevo
    w = 1 / (s2 + t2); Vg = np.linalg.inv(Z.T @ (Z * w[:, None])); g = Vg @ (Z.T @ (w * dlt))
    pred = Z @ g
    lam = t2 / (t2 + s2)
    d_post = pred + lam * (dlt - pred)
    v_post = lam * s2 + (1 - lam) ** 2 * np.einsum("ij,jk,ik->i", Z, Vg, Z)
    out = df.drop(columns="nulos").assign(se=np.sqrt(s2 + se_mu ** 2), desviacion=dlt, se_desviacion=np.sqrt(s2),
                                          peso_dato_propio=lam, sens_post=mu + d_post, sd_post=np.sqrt(se_mu ** 2 + v_post))
    out["ic90_inf"], out["ic90_sup"] = out.sens_post - 1.645 * out.sd_post, out.sens_post + 1.645 * out.sd_post
    out["prob_negativo"] = norm.cdf(-out.sens_post / out.sd_post)
    meta = dict(mu=mu, se_mu=se_mu, p_mu=p_mu, tau=np.sqrt(t2), gamma=g, se_gamma=np.sqrt(np.diag(Vg)), Q=Qobs, p_het=p_het, gl=len(b) - 1)
    return out, meta

filas, metas = [], {}
for choque in ["choque_A_tpu_ultimo", "choque_B_tpu_primero"]:
    s = choques_std[choque].reindex(MESES_S).values
    assert not np.isnan(s).any()
    for y in NIV:
        for excl, etiqueta in [(True, "sin pandemia"), (False, "completa")]:
            r = [dict(rama=ra, **f) for ra in sorted(base.rama.unique()) if (f := sensibilidad_rama(ra, y, s, excl)) is not None]
            df = pd.DataFrame(r).merge(info, left_on="rama", right_index=True)
            out, meta = eb(df)
            metas[(choque, y, etiqueta)] = meta
            filas.append(out.assign(choque=choque, variable=y, muestra=etiqueta))
            print(f"{choque[:9]} | {y:10s} | {etiqueta:12s} | media común {meta['mu']:+.2f} (ee {meta['se_mu']:.2f}, p {meta['p_mu']:.2f}) | "
                  f"heterogeneidad: Q = {meta['Q']:.0f} (gl {meta['gl']}), p perm = {meta['p_het']:.3f}, τ = {meta['tau']:.2f} | "
                  f"γ export = {meta['gamma'][1]:+.2f} (ee {meta['se_gamma'][1]:.2f}), γ arancel = {meta['gamma'][2]:+.2f} (ee {meta['se_gamma'][2]:.2f}) | "
                  f"P(neg)>0.9: {(out.prob_negativo > .9).sum()}, P(neg)<0.1: {(out.prob_negativo < .1).sum()}", flush=True)
res = pd.concat(filas, ignore_index=True)
cols = ["choque", "variable", "muestra", "rama", "rama_nombre", "coef_exportacion", "arancel_medio_2018_2019", "sens", "se", "p_perm",
        "desviacion", "se_desviacion", "peso_dato_propio", "sens_post", "sd_post", "ic90_inf", "ic90_sup", "prob_negativo",
        "meses_h0", "meses_h12", "usa_control_arancel", *[f"b_h{h}" for h in H]]
res[cols].sort_values(["choque", "variable", "muestra", "sens_post"]).to_csv(RAIZ / "outputs/tables/sensibilidad_por_rama.csv", index=False)
print("Guardado: outputs/tables/sensibilidad_por_rama.csv y outputs/tables/choque_tpu_limpio.csv")
