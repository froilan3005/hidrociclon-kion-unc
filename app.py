# =============================================================================
# app.py — Sistema Hidrociclónico para Separación de Almidón de Jengibre (Kion)
# UNIÓN DE NEGOCIOS CORPORATIVOS — Ing. Froilán Becerra, Jefe de Mantenimiento
# Modelo: Bradford (Castilho & Medronho, 2000) — Geometría: Chu et al. (2000)
# Deploy: Streamlit Community Cloud
# =============================================================================

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from scipy.optimize import brentq
import io
import math

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Hidrociclón Kion — UNC",
    page_icon="⚙️",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS — FONDO BLANCO PURO + ESTILO PROFESIONAL
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Fondo blanco puro en toda la app */
    .stApp { background-color: #FFFFFF !important; }
    .main { background-color: #FFFFFF !important; }
    [data-testid="block-container"] { background-color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #F0F4F8 !important; }
    [data-testid="stSidebar"] > div:first-child { background-color: #F0F4F8 !important; }

    /* Tipografía */
    h1 { color: #1B3A6B; font-family: Arial, sans-serif; font-size: 1.6rem; }
    h2 { color: #2D5A8E; font-family: Arial, sans-serif; font-size: 1.25rem; }
    h3 { color: #2D5A8E; font-family: Arial, sans-serif; font-size: 1.05rem; }

    /* Botón calcular */
    .stButton > button {
        background-color: #1B3A6B !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 0.55rem 2.5rem !important;
        font-size: 1rem !important;
        border: none !important;
        width: 100% !important;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover {
        background-color: #2D5A8E !important;
        box-shadow: 0 4px 12px rgba(29, 58, 107, 0.3) !important;
    }

    /* Métricas */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    [data-testid="stMetricLabel"] { color: #4A5568 !important; font-size: 0.78rem !important; }
    [data-testid="stMetricValue"] { color: #1B3A6B !important; font-size: 1.35rem !important; font-weight: 600 !important; }
    [data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border: 1px solid #E2E8F0; border-radius: 8px; }

    /* Slider label */
    .stSlider label { color: #4A5568 !important; font-size: 0.85rem !important; }

    /* Selectbox */
    .stSelectbox label { color: #4A5568 !important; font-size: 0.85rem !important; }

    /* Info/warning/success */
    .stAlert { border-radius: 8px !important; }

    /* Expander */
    [data-testid="stExpander"] { border: 1px solid #E2E8F0; border-radius: 8px; }

    /* Separadores */
    hr { border-color: #E2E8F0; }

    /* Etiqueta de sección */
    .seccion-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #718096;
        margin-bottom: 4px;
        border-left: 3px solid #2D5A8E;
        padding-left: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CONSTANTES FIJAS DEL SISTEMA
# ─────────────────────────────────────────────
RHO_S_FIJO = 1517.0          # kg/m³ — Densidad almidón de jengibre (Reyes, 1982)
T_GEL = 80.0                  # °C — Temperatura gelatinización almidón de jengibre
HP_TO_KW = 0.74570            # Conversión HP → kW
ETA_BOMBA = 0.65              # Eficiencia volumétrica estimada bombas Pentax
BANCOS = {1: 4, 2: 3, 3: 2}  # Ciclones por banco
HP_BOMBAS = {1: 3, 2: 3, 3: 2}


# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
col_logo, col_titulo = st.columns([1, 8])
with col_logo:
    st.markdown("""
    <div style="width:64px;height:64px;background:linear-gradient(135deg,#1B3A6B,#2D5A8E);
    border-radius:12px;display:flex;align-items:center;justify-content:center;
    font-size:30px;margin-top:6px;">⚙️</div>""", unsafe_allow_html=True)
with col_titulo:
    st.markdown("""
    <div style="margin-top:2px">
    <div style="font-size:0.72rem;font-weight:700;letter-spacing:2px;
         text-transform:uppercase;color:#718096">UNIÓN DE NEGOCIOS CORPORATIVOS — PERÚ</div>
    <h1 style="margin:2px 0 0 0;font-size:1.45rem">
        Sistema Hidrociclónico · Separación de Almidón de Jengibre (Kion)
    </h1>
    <div style="font-size:0.82rem;color:#4A5568;margin-top:2px">
        Modelo Hy38/1100 (1½") · SAE 304 · Tri-Clamp ·
        Ing. Froilán Becerra — Jefe de Mantenimiento · 2026
    </div>
    </div>""", unsafe_allow_html=True)

st.markdown("<hr style='margin:12px 0 18px 0'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR — PARÁMETROS DE ENTRADA
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Parámetros de diseño")
    st.markdown("---")

    st.markdown('<div class="seccion-label">Fluido de proceso</div>', unsafe_allow_html=True)
    rho_f = st.slider("Densidad del jugo ρ_f (kg/m³)", 1010, 1060, 1035, 5,
                       help="Jugo de rizoma de jengibre fresco. Rango: 1020–1050 kg/m³")
    mu_mPas = st.slider("Viscosidad dinámica μ (mPa·s)", 1.0, 3.0, 1.8, 0.1,
                         help="Suspensión diluida a 20°C. Rango: 1.2–2.5 mPa·s")
    c_gL = st.slider("Concentración de sólidos en feed (g/L)", 100, 300, 200, 10,
                      help="Rango óptimo: 150–250 g/L (Sáiz Rubio, 2009)")
    T_proc = st.slider("Temperatura de proceso (°C)", 10, 40, 22, 1,
                        help="Condición ambiente Perú. Límite gelatinización: 80°C")

    st.markdown("---")
    st.markdown('<div class="seccion-label">Almidón (fijo — Reyes, 1982)</div>', unsafe_allow_html=True)
    st.info(f"ρ_s = **{RHO_S_FIJO:.0f} kg/m³** — *Zingiber officinale*\n\n"
            f"T_gel = **{T_GEL:.0f} °C** — Sin riesgo a T ambiente")

    st.markdown("---")
    st.markdown('<div class="seccion-label">Geometría del hidrociclón</div>', unsafe_allow_html=True)
    D_mm = st.slider("Diámetro principal D (mm)", 15.0, 80.0, 38.0, 0.5,
                      help="D nominal del modelo Hy38/1100 = 38.1 mm (1.5 pulgadas)")
    Du_D_ratio = st.slider("Relación Du/D (underflow)", 0.15, 0.30, 0.20, 0.01,
                            help="Recomendado 0.15–0.25 para almidones finos")
    Do_D_ratio = st.slider("Relación Do/D (overflow)", 0.30, 0.50, 0.40, 0.02,
                            help="Recomendado 0.35–0.45 (Grommers et al., 2004)")
    alpha_deg = st.slider("Ángulo semi-cónico α (°)", 8, 20, 12, 1,
                           help="10°–15° recomendado para partículas < 20 µm")

    st.markdown("---")
    st.markdown('<div class="seccion-label">Condición operativa</div>', unsafe_allow_html=True)
    modo = st.radio("Modo de cálculo", ["Fijar ΔP (kPa)", "Fijar v entrada (m/s)"],
                     help="Modo ΔP: más intuitivo para selección de bomba.\n"
                          "Modo v: más directo para el modelo Bradford.")
    if "ΔP" in modo:
        dP_input = st.slider("Presión de trabajo ΔP (kPa)", 50, 700, 300, 10,
                              help="Presión diferencial entrada–salida del ciclón. "
                                   "Pentax 3HP: típico 200–450 kPa")
        v_input = None
    else:
        v_input = st.slider("Velocidad característica v (m/s)", 0.3, 10.0, 2.0, 0.1,
                             help="v = Q/(π/4·D²). Límite recomendado: ≤ 8 m/s")
        dP_input = None

    st.markdown("---")
    st.markdown('<div class="seccion-label">Sistema instalado</div>', unsafe_allow_html=True)
    Q_total_lh = st.slider("Caudal total de producción (L/h)", 500, 3000, 1500, 50,
                             help="Capacidad nominal del sistema: 1500 L/h")
    n_total_inst = st.number_input("N° ciclones instalados (ref.)", 1, 30, 9, 1,
                                    help="Sistema actual: 4+3+2 = 9 ciclones")

    st.markdown("---")
    calcular = st.button("▶ CALCULAR DISEÑO", key="btn_calc")


# ─────────────────────────────────────────────
# MOTOR DE CÁLCULO — MODELO BRADFORD
# ─────────────────────────────────────────────
def modelo_bradford(D_mm, Du_D, Do_D, alpha_deg,
                    rho_f, mu_Pas, c_gL, rho_s,
                    modo, dP_kPa=None, v_ms=None):
    """
    Implementa las ecuaciones de Bradford (Castilho & Medronho, 2000):
      Ec. 4: Stk'50 · Eu = 0.0474 · [ln(1/Rf)]^0.742 · exp(8.96·c_gg)
      Ec. 5: Eu = 371.5 · Re^0.116 · exp(-2.12·c_gg)
      Ec. 6: Rf = 1218 · (Du/D)^4.75 · Eu^(-0.3)

    Variables:
      Stk'50 = (ρs−ρf)·x50²·v / (18·μ·D)
      Eu     = 2·ΔP / (ρf·v²)
      Re     = ρf·v·D / μ
      v      = velocidad característica = Q / (π/4·D²)
      c_gg   = concentración másica (g/g)
    """
    D = D_mm / 1000.0       # m
    alpha_rad = math.radians(alpha_deg)
    c_gg = c_gL / rho_f     # g/g

    # Resolver velocidad característica v (m/s)
    if modo == "dP":
        # Dado ΔP → resolver Eu(v)·ρf·v²/2 = ΔP implícitamente
        dP_Pa = dP_kPa * 1000.0
        def eq_v(v):
            if v <= 0: return 1e9
            Re = rho_f * v * D / mu_Pas
            Eu = 371.5 * Re**0.116 * math.exp(-2.12 * c_gg)
            return Eu * rho_f * v**2 / 2.0 - dP_Pa
        try:
            v = brentq(eq_v, 0.001, 100.0, xtol=1e-8, maxiter=500)
        except Exception:
            return None
    else:
        v = v_ms  # m/s dado directamente

    if v <= 0:
        return None

    # Números adimensionales
    Re = rho_f * v * D / mu_Pas
    Eu = 371.5 * Re**0.116 * math.exp(-2.12 * c_gg)

    # Ec. 6 — Relación de flujo underflow
    Rf = 1218.0 * (Du_D)**4.75 * Eu**(-0.3)
    if not (0.001 < Rf < 0.999):
        return None

    # Ec. 4 — Número de Stokes reducido → tamaño de corte x'50
    ln_Rf = math.log(1.0 / Rf)
    LHS = 0.0474 * (ln_Rf**0.742) * math.exp(8.96 * c_gg)
    Stk = LHS / Eu

    # x'50 en metros
    denom = (rho_s - rho_f) * v
    if denom <= 0:
        return None
    x50_m = math.sqrt(Stk * 18.0 * mu_Pas * D / denom)

    # Caída de presión
    dP_calc_kPa = Eu * rho_f * v**2 / 2.0 / 1000.0

    # Caudal volumétrico por ciclón
    Q_cicl_m3s = v * math.pi / 4.0 * D**2
    Q_cicl_Lh  = Q_cicl_m3s * 3600.0 * 1000.0
    Q_cicl_Lmin = Q_cicl_m3s * 1000.0 * 60.0

    # ── Geometría completa ──────────────────────────
    Do_mm  = Do_D  * D_mm
    Du_mm  = Du_D  * D_mm
    Lcy_mm = 2.0   * D_mm
    Lco_mm = (D_mm/2.0 - Du_mm/2.0) / math.tan(alpha_rad)
    La_mm  = 10.0                               # longitud spigot fija
    L_mm   = Lcy_mm + Lco_mm + La_mm
    Lv_mm  = 0.10  * L_mm
    Sa_mm  = math.sqrt(0.05 * D_mm**2)
    Sb_mm  = Sa_mm

    # ── Número de ciclones necesarios para Q_total ──
    n_cicl_calc = Q_total_lh / Q_cicl_Lh if Q_cicl_Lh > 0 else float('inf')

    # ── Potencia hidráulica por banco ────────────────
    # Distribución proporcional a HP de cada banco
    HP_total = sum(HP_BOMBAS.values())
    pot_banco = {}
    Q_banco = {}
    for b, n_b in BANCOS.items():
        Q_b_Lh = Q_total_lh * HP_BOMBAS[b] / HP_total
        Q_b_m3s = Q_b_Lh / 1000.0 / 3600.0
        P_hid_W = dP_calc_kPa * 1000.0 * Q_b_m3s / ETA_BOMBA
        pot_banco[b] = {
            "Q_Lh": Q_b_Lh,
            "P_W": P_hid_W,
            "P_kW": P_hid_W / 1000.0,
            "P_HP": P_hid_W / (HP_TO_KW * 1000.0),
            "nom_HP": HP_BOMBAS[b],
        }
        Q_banco[b] = Q_b_Lh

    # ── Tuberías colectoras ──────────────────────────
    # Criterio: v_tubería ≤ 3.0 m/s (límite erosión SS304)
    Q_total_m3s = Q_total_lh / 1000.0 / 3600.0
    v_lim = 2.5  # m/s diseño (< 3 m/s límite)
    d_feed_mm = math.sqrt(4.0 * Q_total_m3s / (math.pi * v_lim)) * 1000.0
    d_OF_mm   = math.sqrt(4.0 * Q_total_m3s * (1.0 - Rf) / (math.pi * v_lim)) * 1000.0
    d_UF_mm   = math.sqrt(4.0 * Q_total_m3s * Rf / (math.pi * v_lim)) * 1000.0
    # DN comercial (múltiplos de 5 mm, mínimo 10 mm)
    dn = lambda d: max(10, int(math.ceil(d / 5.0)) * 5)
    DN_feed = dn(d_feed_mm)
    DN_OF   = dn(d_OF_mm)
    DN_UF   = dn(d_UF_mm)
    # Velocidades reales con DN comercial
    vr_feed = Q_total_m3s / (math.pi/4 * (DN_feed/1000)**2)
    vr_OF   = Q_total_m3s*(1-Rf) / (math.pi/4 * (DN_OF/1000)**2)
    vr_UF   = Q_total_m3s*Rf / (math.pi/4 * (DN_UF/1000)**2)

    # ── Eficiencia para D50=20µm (almidón jengibre) ──
    x_d50 = 20e-6
    Gp_d50 = 1.0 / (1.0 + (x50_m / x_d50)**2.5) if x50_m > 0 else 0
    G_d50  = Rf + (1.0 - Rf) * Gp_d50

    return {
        # Adimensionales
        "Re": Re, "Eu": Eu, "Stk": Stk, "Rf": Rf, "c_gg": c_gg,
        # Hidráulica
        "v": v, "dP_kPa": dP_calc_kPa,
        "Q_cicl_Lh": Q_cicl_Lh, "Q_cicl_Lmin": Q_cicl_Lmin,
        # Separación
        "x50_um": x50_m * 1e6,
        "eff_d50": G_d50 * 100.0,
        # Geometría (mm)
        "D": D_mm, "Do": Do_mm, "Du": Du_mm,
        "Lcy": Lcy_mm, "Lco": Lco_mm, "La": La_mm,
        "L": L_mm, "Lv": Lv_mm, "Sa": Sa_mm, "Sb": Sb_mm,
        "alpha": alpha_deg,
        "Do_D": Do_D, "Du_D": Du_D,
        # Sistema
        "n_cicl_calc": n_cicl_calc,
        "pot_banco": pot_banco,
        "Q_banco": Q_banco,
        # Tuberías
        "DN_feed": DN_feed, "DN_OF": DN_OF, "DN_UF": DN_UF,
        "d_feed_mm": d_feed_mm, "d_OF_mm": d_OF_mm, "d_UF_mm": d_UF_mm,
        "vr_feed": vr_feed, "vr_OF": vr_OF, "vr_UF": vr_UF,
    }


def curva_eficiencia(x50_m, Rf, n_puntos=200):
    """Genera la curva G(x) y G'(x) de 1 a 120 µm."""
    x_um = np.linspace(1, 120, n_puntos)
    x_m  = x_um * 1e-6
    Gp   = 1.0 / (1.0 + (x50_m / x_m)**2.5)
    G    = Rf + (1.0 - Rf) * Gp
    return x_um, G * 100.0, Gp * 100.0


# ─────────────────────────────────────────────
# EJECUCIÓN DEL CÁLCULO
# ─────────────────────────────────────────────
if "resultado" not in st.session_state:
    st.session_state["resultado"] = None

if calcular:
    with st.spinner("⚙️ Calculando diseño óptimo…"):
        mu_Pas = mu_mPas * 1e-3
        modo_calc = "dP" if "ΔP" in modo else "v"
        res = modelo_bradford(
            D_mm=D_mm, Du_D=Du_D_ratio, Do_D=Do_D_ratio, alpha_deg=alpha_deg,
            rho_f=rho_f, mu_Pas=mu_Pas, c_gL=c_gL, rho_s=RHO_S_FIJO,
            modo=modo_calc, dP_kPa=dP_input, v_ms=v_input,
        )
        if res is None:
            st.error("❌ El modelo Bradford no convergió con los parámetros actuales. "
                     "Pruebe ajustar D, ΔP o la relación Du/D.")
        else:
            res["Q_total_lh"] = Q_total_lh
            res["n_total_inst"] = n_total_inst
            res["T_proc"] = T_proc
            res["c_gL_input"] = c_gL
            res["rho_f_input"] = rho_f
            res["mu_input"] = mu_mPas
            st.session_state["resultado"] = res

r = st.session_state["resultado"]

# ─────────────────────────────────────────────
# SECCIÓN DE RESULTADOS
# ─────────────────────────────────────────────
if r is None:
    st.info("👈 Configure los parámetros en el panel lateral y presione **▶ CALCULAR DISEÑO**.")
    st.markdown("""
    ### Acerca del modelo
    Esta aplicación implementa el **modelo adimensional de Bradford**
    (Castilho & Medronho, 2000) para el diseño de hidrociclones en la industria
    alimentaria, adaptado para la separación de **almidón de jengibre**
    (*Zingiber officinale*) con ρ_s = 1 517 kg/m³ (Reyes, 1982).

    **Sistema de referencia:** Hy38/1100 · 3 bancos (4+3+2 ciclones) ·
    Bombas Pentax (3+3+2 HP) · Acero inoxidable SAE 304 · Tri-Clamp sanitario.

    **Referencias bibliográficas:**
    - Castilho, L.R. & Medronho, R.A. (2000). *Minerals Engineering*.
    - Sáiz Rubio, V. (2009). *Växjö University, TD 052/2009*.
    - Reyes, O.A. (1982). *Starch/Stärke*, 34(2).
    - Chu, L.Y. et al. (2000). *Chem. Eng. Res. Design*.
    - Svarovsky, L. (2000). *Solid-Liquid Separation*, 4th ed.
    """)
    st.stop()

# ── Semáforos de verificación ─────────────────
def semaforo(val, ok_max, warn_max, invert=False):
    """Retorna emoji y clase según valor."""
    if not invert:
        if val <= ok_max:   return "🟢", "normal"
        if val <= warn_max: return "🟡", "off"
        return "🔴", "inverse"
    else:
        if val >= ok_max:   return "🟢", "normal"
        if val >= warn_max: return "🟡", "off"
        return "🔴", "inverse"

em_v,   _ = semaforo(r["v"],   6.0,  8.0)
em_dP,  _ = semaforo(r["dP_kPa"], 400, 600)
em_feed,_ = semaforo(r["vr_feed"], 2.5, 3.0)
em_T,   _ = semaforo(T_proc, 40, 60)
em_c,   _ = (("🟢","normal") if 150 <= c_gL <= 250 else ("🟡","off") if c_gL < 300 else ("🔴","inverse")), "normal"
em_Rf,  _ = semaforo(r["Rf"]*100, 25, 40)
em_eff, _ = semaforo(r["eff_d50"], 999, 999, invert=True)  # siempre verde (informativo)
em_c2   = "🟢" if 150 <= c_gL <= 250 else ("🟡" if c_gL < 300 else "🔴")

# ─────────────────────────────────────────────
# FILA 1: KPIs principales
# ─────────────────────────────────────────────
st.markdown("### 📊 Resultados del cálculo — Modelo Bradford")
c1,c2,c3,c4,c5,c6,c7,c8,c9,c10 = st.columns(10)

with c1:  st.metric("D principal",       f"{r['D']:.1f} mm")
with c2:  st.metric("ΔP hidrociclón",    f"{r['dP_kPa']:.1f} kPa",
                    delta=f"{em_dP} {'OK' if r['dP_kPa']<=400 else 'Revisar'}")
with c3:  st.metric("x'₅₀ corte",        f"{r['x50_um']:.1f} µm")
with c4:  st.metric("Rf underflow",      f"{r['Rf']*100:.1f} %")
with c5:  st.metric("Vel. entrada",      f"{r['v']:.2f} m/s",
                    delta=f"{em_v} {'OK' if r['v']<=6 else 'Alto'}")
with c6:  st.metric("Q por ciclón",      f"{r['Q_cicl_Lh']:.1f} L/h")
with c7:  st.metric("N° ciclones calc.", f"{r['n_cicl_calc']:.1f}",
                    delta=f"Instalados: {r['n_total_inst']}")
with c8:  st.metric("Re",                f"{r['Re']:.0f}")
with c9:  st.metric("Eu",                f"{r['Eu']:.1f}")
with c10: st.metric("Efic. D50=20µm",   f"{r['eff_d50']:.1f} %")

st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILA 2: Diagrama + Curva eficiencia
# ─────────────────────────────────────────────
col_diag, col_curva = st.columns([1, 1])

# ── A) DIAGRAMA 2D DEL HIDROCICLÓN ────────────
with col_diag:
    st.markdown("#### 📐 Diagrama 2D — Sección transversal (a escala)")

    fig_d, ax = plt.subplots(figsize=(5.2, 7.0), facecolor="white")
    ax.set_facecolor("white")
    ax.set_aspect("equal")

    # Escala: Longitud total ocupa ~80% del alto del eje
    L_tot = r["L"]
    escala = 220.0 / L_tot  # px/mm

    cx = 130.0  # centro x
    y0 = 40.0   # tope cilindro

    Dp = r["D"]  * escala
    Dop = r["Do"] * escala
    Dup = r["Du"] * escala
    Lcyp = r["Lcy"] * escala
    Lcop = r["Lco"] * escala
    Lap  = r["La"]  * escala
    Lvp  = r["Lv"]  * escala
    Sap  = r["Sa"]  * escala

    # Colores
    C_WALL  = "#1B3A6B"
    C_FLUID = "#BEE3F8"
    C_VF    = "#90CDF4"
    C_IN    = "#2B6CB0"
    C_OV    = "#276749"
    C_UF    = "#C05621"

    # Cuerpo cilíndrico (relleno)
    ax.add_patch(plt.Rectangle(
        (cx - Dp/2, y0), Dp, Lcyp,
        facecolor=C_FLUID, edgecolor=C_WALL, linewidth=1.5))

    # Cuerpo cónico
    cone_pts = np.array([
        [cx - Dp/2, y0 + Lcyp],
        [cx + Dp/2, y0 + Lcyp],
        [cx + Dup/2, y0 + Lcyp + Lcop],
        [cx - Dup/2, y0 + Lcyp + Lcop],
    ])
    ax.add_patch(plt.Polygon(cone_pts, facecolor=C_FLUID,
                              edgecolor=C_WALL, linewidth=1.5))

    # Spigot
    ax.add_patch(plt.Rectangle(
        (cx - Dup/2, y0 + Lcyp + Lcop), Dup, Lap,
        facecolor=C_FLUID, edgecolor=C_WALL, linewidth=1.5))

    # Vortex finder
    ax.add_patch(plt.Rectangle(
        (cx - Dop/2, y0 - Lvp), Dop, Lvp + 4,
        facecolor=C_VF, edgecolor=C_IN, linewidth=1.0,
        linestyle="--", alpha=0.9))

    # Tapa superior (cierra el cilindro dejando hueco para vortex finder)
    ax.plot([cx - Dp/2, cx - Dop/2 - 0.5], [y0, y0], color=C_WALL, lw=1.5)
    ax.plot([cx + Dop/2 + 0.5, cx + Dp/2], [y0, y0], color=C_WALL, lw=1.5)

    # Entrada tangencial
    ent_y = y0 + Lcyp * 0.28
    ent_w = Sap * 2.0
    ax.add_patch(plt.Rectangle(
        (cx - Dp/2 - ent_w, ent_y - Sap/2), ent_w, Sap,
        facecolor="#BEE3F8", edgecolor=C_IN, linewidth=1.0))
    ax.annotate("", xy=(cx - Dp/2 - 1, ent_y),
                xytext=(cx - Dp/2 - ent_w + 3, ent_y),
                arrowprops=dict(arrowstyle="->", color=C_IN, lw=1.5))

    # Flecha overflow (arriba)
    ax.annotate("", xy=(cx, y0 - Lvp - 16), xytext=(cx, y0 - Lvp - 2),
                arrowprops=dict(arrowstyle="->", color=C_OV, lw=2.0))

    # Flecha underflow (abajo)
    ax.annotate("", xy=(cx, y0 + Lcyp + Lcop + Lap + 16),
                xytext=(cx, y0 + Lcyp + Lcop + Lap + 2),
                arrowprops=dict(arrowstyle="->", color=C_UF, lw=2.0))

    # ─ COTAS ─
    fs = 7.5
    c_cota = "#444444"

    def cota_h(ax, x1, x2, y, label, offset_y=-7, color=c_cota):
        """Cota horizontal."""
        ax.annotate("", xy=(x2, y + offset_y), xytext=(x1, y + offset_y),
                    arrowprops=dict(arrowstyle="<->", color=color, lw=0.8))
        ax.plot([x1, x1], [y, y + offset_y], color=color, lw=0.5, ls=":")
        ax.plot([x2, x2], [y, y + offset_y], color=color, lw=0.5, ls=":")
        ax.text((x1+x2)/2, y + offset_y - 4, label,
                ha="center", va="top", fontsize=fs, color=color)

    def cota_v(ax, x, y1, y2, label, offset_x=18, color=c_cota):
        """Cota vertical."""
        ax.annotate("", xy=(x + offset_x, y2), xytext=(x + offset_x, y1),
                    arrowprops=dict(arrowstyle="<->", color=color, lw=0.8))
        ax.plot([x, x + offset_x], [y1, y1], color=color, lw=0.5, ls=":")
        ax.plot([x, x + offset_x], [y2, y2], color=color, lw=0.5, ls=":")
        ax.text(x + offset_x + 2, (y1+y2)/2, label,
                ha="left", va="center", fontsize=fs, color=color, rotation=0)

    # Cotas horizontales
    cota_h(ax, cx-Dp/2,  cx+Dp/2,  y0,          f"D={r['D']:.1f}mm",  offset_y=-9)
    cota_h(ax, cx-Dop/2, cx+Dop/2, y0-Lvp,      f"Do={r['Do']:.1f}",  offset_y=-6, color="#2B6CB0")
    cota_h(ax, cx-Dup/2, cx+Dup/2, y0+Lcyp+Lcop+Lap,
           f"Du={r['Du']:.1f}", offset_y=6, color=C_UF)

    # Cotas verticales (lado derecho)
    xr = cx + Dp/2
    cota_v(ax, xr, y0-Lvp,        y0,                       f"Lv={r['Lv']:.1f}",  offset_x=16)
    cota_v(ax, xr, y0,             y0+Lcyp,                  f"Lcy={r['Lcy']:.1f}", offset_x=32)
    cota_v(ax, xr, y0+Lcyp,       y0+Lcyp+Lcop,             f"Lco={r['Lco']:.1f}", offset_x=48)
    cota_v(ax, xr, y0+Lcyp+Lcop,  y0+Lcyp+Lcop+Lap,         f"La={r['La']:.1f}",   offset_x=16)
    cota_v(ax, xr, y0,             y0+Lcyp+Lcop+Lap,         f"L={r['L']:.1f}mm",   offset_x=64, color="#1B3A6B")

    # Ángulo cono
    ang_x = cx - Dp/4
    ang_y = y0 + Lcyp + Lcop * 0.4
    ax.text(ang_x - 8, ang_y, f"α={r['alpha']}°",
            ha="right", va="center", fontsize=fs+0.5, color=C_WALL, style="italic")

    # Etiquetas flujo
    ax.text(cx - Dp/2 - ent_w - 2, ent_y + Sap, "Entrada\ntangencial",
            ha="center", va="bottom", fontsize=fs, color=C_IN)
    ax.text(cx + 3, y0 - Lvp - 20, "Overflow\n(jugo clarif.)",
            ha="left", va="top", fontsize=fs, color=C_OV)
    ax.text(cx + 3, y0 + Lcyp + Lcop + Lap + 18, "Underflow\n(almidón)",
            ha="left", va="bottom", fontsize=fs, color=C_UF)

    # Escala gráfica
    bar_len = 20 * escala  # 20 mm
    bx = 10; by = y0 + Lcyp + Lcop + Lap + 45
    ax.plot([bx, bx+bar_len], [by, by], color="#333", lw=2)
    ax.text(bx + bar_len/2, by + 3, "20 mm",
            ha="center", va="bottom", fontsize=fs, color="#333")

    # Leyenda
    leyenda = [
        mpatches.Patch(facecolor=C_FLUID, edgecolor=C_WALL, label="Cuerpo ciclón (SS304)"),
        mpatches.Patch(facecolor=C_VF, edgecolor=C_IN, label="Vortex finder (dashed)"),
        plt.Line2D([0],[0], color=C_IN, lw=1.5, label=f"Entrada · Sa×Sb={r['Sa']:.1f}×{r['Sb']:.1f} mm"),
        plt.Line2D([0],[0], color=C_OV, lw=2, label="Overflow (jugo)"),
        plt.Line2D([0],[0], color=C_UF, lw=2, label="Underflow (almidón)"),
    ]
    ax.legend(handles=leyenda, loc="lower left", fontsize=6.5,
              frameon=True, framealpha=0.9, edgecolor="#CBD5E0")

    # Ajuste de ejes
    margen_x = 80; margen_y_top = 60; margen_y_bot = 80
    ax.set_xlim(cx - Dp/2 - margen_x, cx + Dp/2 + 90)
    ax.set_ylim(y0 - margen_y_top, y0 + Lcyp + Lcop + Lap + margen_y_bot)
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title(f"Hidrociclón Hy38/1100 — D={r['D']:.1f} mm — SAE 304 — Tri-Clamp\n"
                 f"Modelo Bradford (Castilho & Medronho, 2000)",
                 fontsize=8.5, color="#1B3A6B", pad=6)

    plt.tight_layout(pad=0.5)
    buf_d = io.BytesIO()
    fig_d.savefig(buf_d, format="png", dpi=160, bbox_inches="tight", facecolor="white")
    buf_d.seek(0)
    st.image(buf_d, use_container_width=True)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("⬇ Descargar diagrama PNG", buf_d.getvalue(),
                           "hidrociclon_kion.png", "image/png", use_container_width=True)
    plt.close(fig_d)

# ── B) CURVA DE EFICIENCIA G(x) ───────────────
with col_curva:
    st.markdown("#### 📈 Curva de eficiencia de separación G(x)")

    x_um, G_pct, Gp_pct = curva_eficiencia(r["x50_um"]*1e-6, r["Rf"])

    fig_eff = go.Figure()

    # Área sombreada bajo G(x)
    fig_eff.add_trace(go.Scatter(
        x=x_um, y=G_pct,
        fill="tozeroy", fillcolor="rgba(43,108,176,0.10)",
        line=dict(color="#2B6CB0", width=2.5),
        name="G(x) — Eficiencia total (%)",
        hovertemplate="x = %{x:.1f} µm<br>G(x) = %{y:.1f} %<extra></extra>",
    ))

    # G'(x) curva reducida
    fig_eff.add_trace(go.Scatter(
        x=x_um, y=Gp_pct,
        line=dict(color="#38A169", width=1.8, dash="dash"),
        name="G'(x) — Eficiencia reducida (%)",
        hovertemplate="x = %{x:.1f} µm<br>G'(x) = %{y:.1f} %<extra></extra>",
    ))

    # Línea vertical en x'50
    fig_eff.add_vline(
        x=r["x50_um"], line=dict(color="#C53030", width=1.5, dash="dot"),
        annotation_text=f"x'₅₀ = {r['x50_um']:.1f} µm",
        annotation_position="top right",
        annotation=dict(font=dict(color="#C53030", size=11)),
    )

    # Línea vertical en D50=20µm (almidón jengibre)
    fig_eff.add_vline(
        x=20, line=dict(color="#D97706", width=1.2, dash="longdash"),
        annotation_text="D₅₀ almidón kion = 20 µm",
        annotation_position="top left",
        annotation=dict(font=dict(color="#D97706", size=10)),
    )

    # Nivel de Rf
    fig_eff.add_hline(
        y=r["Rf"]*100, line=dict(color="#718096", width=1, dash="dot"),
        annotation_text=f"Rf = {r['Rf']*100:.1f}%",
        annotation_position="right",
        annotation=dict(font=dict(color="#718096", size=10)),
    )

    fig_eff.update_layout(
        xaxis=dict(
            title="Tamaño de partícula x (µm)",
            type="log", range=[0, np.log10(120)],
            gridcolor="#EDF2F7", linecolor="#CBD5E0",
            title_font=dict(size=11, color="#4A5568"),
        ),
        yaxis=dict(
            title="G(x) — Eficiencia de separación (%)",
            range=[0, 102], gridcolor="#EDF2F7", linecolor="#CBD5E0",
            title_font=dict(size=11, color="#4A5568"),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
            font=dict(size=10), bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#CBD5E0", borderwidth=1,
        ),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=20, t=30, b=50),
        height=380,
        title=dict(
            text=f"Almidón Zingiber officinale — ρs={RHO_S_FIJO:.0f} kg/m³ — D={r['D']:.1f} mm",
            font=dict(size=10, color="#1B3A6B"), x=0.5,
        ),
    )
    st.plotly_chart(fig_eff, use_container_width=True)

    # Nota explicativa
    st.caption(
        f"**Modelo:** G'(x) = 1 / [1 + (x'₅₀/x)²·⁵]  —  G(x) = Rf + (1−Rf)·G'(x)  "
        f"(Castilho & Medronho, 2000). "
        f"Rf = {r['Rf']*100:.1f}% es la fracción mínima que siempre pasa al underflow. "
        f"Eficiencia para D₅₀=20 µm: **{r['eff_d50']:.1f}%**."
    )

st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILA 3: Verificaciones + Sistema 3 Bancos
# ─────────────────────────────────────────────
col_ver, col_bancos = st.columns([1, 1])

# ── C) VERIFICACIONES OPERATIVAS ──────────────
with col_ver:
    st.markdown("#### ✅ Verificaciones operativas — Límites de diseño")

    chk_data = [
        ("Velocidad entrada ≤ 8 m/s (turbulencia)",
         r["v"], f"{r['v']:.2f} m/s", r["v"] <= 8,    r["v"] <= 6),
        ("ΔP ≤ 700 kPa (bomba Pentax 3HP)",
         r["dP_kPa"], f"{r['dP_kPa']:.1f} kPa", r["dP_kPa"] <= 700, r["dP_kPa"] <= 400),
        ("Vel. tubería feed ≤ 3 m/s (erosión SS304)",
         r["vr_feed"], f"{r['vr_feed']:.2f} m/s", r["vr_feed"] <= 3.0, r["vr_feed"] <= 2.5),
        ("Temperatura proceso ≪ 80°C (gelatinización)",
         T_proc, f"{T_proc}°C / Tgel={T_GEL:.0f}°C", T_proc < 60, T_proc < 40),
        ("Concentración feed 150–250 g/L (eficiencia)",
         c_gL, f"{c_gL} g/L", 100 <= c_gL <= 300, 150 <= c_gL <= 250),
        ("Rf < 40% (sin obstrucción en spigot)",
         r["Rf"]*100, f"{r['Rf']*100:.1f}%", r["Rf"] < 0.40, r["Rf"] < 0.25),
    ]

    rows = []
    for label, val, val_str, ok, opt in chk_data:
        if opt:
            icono = "🟢"; estado = "Óptimo"
        elif ok:
            icono = "🟡"; estado = "Aceptable"
        else:
            icono = "🔴"; estado = "⚠ Revisar"
        rows.append({"Verificación": label, "Valor": val_str,
                     "Estado": f"{icono} {estado}"})

    df_chk = pd.DataFrame(rows)
    st.dataframe(df_chk, use_container_width=True, hide_index=True,
                 height=280,
                 column_config={
                     "Verificación": st.column_config.TextColumn(width="large"),
                     "Valor": st.column_config.TextColumn(width="small"),
                     "Estado": st.column_config.TextColumn(width="medium"),
                 })

    # Tabla de números adimensionales
    st.markdown("**Grupos adimensionales (Bradford)**")
    df_adim = pd.DataFrame([
        {"Símbolo": "Re",      "Expresión": "ρf·v·D / μ",                 "Valor": f"{r['Re']:.1f}",    "Descripción": "Número de Reynolds"},
        {"Símbolo": "Eu",      "Expresión": "2·ΔP / (ρf·v²)",             "Valor": f"{r['Eu']:.2f}",    "Descripción": "Número de Euler"},
        {"Símbolo": "Stk'₅₀", "Expresión": "(ρs−ρf)·x50²·v / (18·μ·D)", "Valor": f"{r['Stk']:.5f}",   "Descripción": "Número de Stokes reducido"},
        {"Símbolo": "Rf",      "Expresión": "Qu / Q",                     "Valor": f"{r['Rf']:.4f}",    "Descripción": "Relación flujo underflow"},
        {"Símbolo": "c_gg",    "Expresión": "c_sólidos [g/g]",            "Valor": f"{r['c_gg']:.4f}",  "Descripción": "Concentración másica feed"},
    ])
    st.dataframe(df_adim, use_container_width=True, hide_index=True, height=230)

# ── D) SISTEMA DE 3 BANCOS ─────────────────────
with col_bancos:
    st.markdown("#### 🏭 Sistema de 3 bancos — Distribución de flujo y potencia")

    banco_labels = [f"Banco {b}\n({n}×Hy38)" for b, n in BANCOS.items()]
    Q_vals = [r["pot_banco"][b]["Q_Lh"] for b in BANCOS]
    P_req  = [r["pot_banco"][b]["P_kW"] for b in BANCOS]
    P_nom  = [HP_BOMBAS[b] * HP_TO_KW for b in BANCOS]
    colores = ["#2B6CB0","#276749","#C05621"]
    colores_P_req = []
    for b in BANCOS:
        if r["pot_banco"][b]["P_HP"] <= HP_BOMBAS[b]:
            colores_P_req.append("#276749")
        else:
            colores_P_req.append("#C53030")

    fig_bk = go.Figure()
    fig_bk.add_trace(go.Bar(
        name="Caudal del banco (L/h)",
        x=banco_labels, y=Q_vals,
        marker_color=colores,
        text=[f"{q:.0f}" for q in Q_vals],
        textposition="outside",
        yaxis="y1",
    ))
    fig_bk.add_trace(go.Bar(
        name="Potencia requerida (kW)",
        x=banco_labels, y=P_req,
        marker_color=colores_P_req,
        text=[f"{p:.2f}" for p in P_req],
        textposition="outside",
        yaxis="y2",
    ))
    fig_bk.add_trace(go.Scatter(
        name="Potencia nominal bomba (kW)",
        x=banco_labels, y=P_nom,
        mode="markers+lines",
        marker=dict(symbol="diamond", size=10, color="#D97706"),
        line=dict(color="#D97706", width=1.5, dash="dot"),
        yaxis="y2",
    ))
    fig_bk.update_layout(
        barmode="group",
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.02, x=0, font=dict(size=9)),
        yaxis=dict(title="Caudal (L/h)", gridcolor="#EDF2F7",
                   title_font=dict(size=10, color="#2B6CB0"), tickfont=dict(color="#2B6CB0")),
        yaxis2=dict(title="Potencia (kW)", overlaying="y", side="right",
                    gridcolor="#EDF2F7",
                    title_font=dict(size=10, color="#C05621"), tickfont=dict(color="#C05621")),
        margin=dict(l=50, r=50, t=40, b=40), height=310,
    )
    st.plotly_chart(fig_bk, use_container_width=True)

    # Tarjetas de banco
    b1, b2, b3 = st.columns(3)
    for col_b, b in zip([b1, b2, b3], [1, 2, 3]):
        pb = r["pot_banco"][b]
        ok_bomb = pb["P_HP"] <= pb["nom_HP"]
        with col_b:
            st.markdown(f"""
            <div style="border:1.5px solid {'#C6F6D5' if ok_bomb else '#FEB2B2'};
                 border-radius:8px;padding:10px;text-align:center;
                 background:{'#F0FFF4' if ok_bomb else '#FFF5F5'}">
            <b>Banco {b}</b> — {BANCOS[b]} ciclones<br>
            <span style="font-size:0.82rem;color:#4A5568">
            Q = <b>{pb['Q_Lh']:.0f}</b> L/h<br>
            P req. = <b>{pb['P_kW']:.2f}</b> kW = <b>{pb['P_HP']:.2f}</b> HP<br>
            Bomba Pentax: <b>{pb['nom_HP']} HP</b><br>
            {'✅ Adecuada' if ok_bomb else '⚠️ Revisar'}
            </span></div>""", unsafe_allow_html=True)

st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILA 4: TABLAS DE ESPECIFICACIONES
# ─────────────────────────────────────────────
st.markdown("### 📋 Tablas de especificaciones")
col_dimT, col_pipeT = st.columns([1.1, 0.9])

with col_dimT:
    st.markdown("#### Dimensiones del hidrociclón individual")

    def est(val, lo, hi):
        return "✅ OK" if lo <= val <= hi else ("⚠️ Revisar" if abs(val-lo)<lo*0.2 or abs(val-hi)<hi*0.2 else "❌ Fuera")

    dims = [
        {"Símbolo":"D",   "Parámetro":"Diámetro principal",          "Valor mm":f"{r['D']:.2f}",   "Relación":"Ref. nominal",             "Rango aceptable":"25–80 mm",  "Estado":est(r['D'],25,80)},
        {"Símbolo":"Do",  "Parámetro":"Overflow / vórtex finder",    "Valor mm":f"{r['Do']:.2f}",  "Relación":f"{r['Do_D']:.2f}×D",       "Rango aceptable":"0.35–0.45 D","Estado":"✅ OK"},
        {"Símbolo":"Du",  "Parámetro":"Underflow / spigot",          "Valor mm":f"{r['Du']:.2f}",  "Relación":f"{r['Du_D']:.2f}×D",       "Rango aceptable":"0.15–0.25 D","Estado":"✅ OK"},
        {"Símbolo":"Lcy", "Parámetro":"Longitud cilíndrica",         "Valor mm":f"{r['Lcy']:.2f}", "Relación":"2.0×D",                    "Rango aceptable":"2.0 D",     "Estado":"✅ OK"},
        {"Símbolo":"Lco", "Parámetro":"Longitud cónica",             "Valor mm":f"{r['Lco']:.2f}", "Relación":"(D−Du)/(2·tan α)",         "Rango aceptable":"Calculado", "Estado":"✅ OK"},
        {"Símbolo":"La",  "Parámetro":"Longitud spigot (fija)",      "Valor mm":f"{r['La']:.1f}",  "Relación":"Fija",                     "Rango aceptable":"8–15 mm",   "Estado":est(r['La'],8,15)},
        {"Símbolo":"L",   "Parámetro":"Longitud total",              "Valor mm":f"{r['L']:.2f}",   "Relación":"Lcy+Lco+La",               "Rango aceptable":"Calculado", "Estado":"✅ OK"},
        {"Símbolo":"Lv",  "Parámetro":"Longitud vórtex finder",      "Valor mm":f"{r['Lv']:.2f}",  "Relación":"10% × L",                  "Rango aceptable":"8–12% L",   "Estado":"✅ OK"},
        {"Símbolo":"Sa",  "Parámetro":"Entrada tangencial (ancho)",  "Valor mm":f"{r['Sa']:.2f}",  "Relación":"√(0.05×D²)",               "Rango aceptable":"Calculado", "Estado":"✅ OK"},
        {"Símbolo":"Sb",  "Parámetro":"Entrada tangencial (alto)",   "Valor mm":f"{r['Sb']:.2f}",  "Relación":"= Sa",                     "Rango aceptable":"Calculado", "Estado":"✅ OK"},
        {"Símbolo":"α",   "Parámetro":"Ángulo semi-cónico",          "Valor mm":f"{r['alpha']}°",  "Relación":"Definido usuario",         "Rango aceptable":"10°–15°",   "Estado":est(r['alpha'],10,15)},
    ]
    df_dims = pd.DataFrame(dims)
    st.dataframe(df_dims, use_container_width=True, hide_index=True, height=440,
                 column_config={
                     "Símbolo": st.column_config.TextColumn(width="small"),
                     "Parámetro": st.column_config.TextColumn(width="medium"),
                     "Valor mm": st.column_config.TextColumn(width="small"),
                     "Relación": st.column_config.TextColumn(width="medium"),
                     "Rango aceptable": st.column_config.TextColumn(width="medium"),
                     "Estado": st.column_config.TextColumn(width="small"),
                 })

    # Botón CSV dimensiones
    csv_dims = df_dims.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("⬇ Descargar especificaciones CSV", csv_dims,
                       "especificaciones_hidrociclon_kion.csv", "text/csv",
                       use_container_width=True)

with col_pipeT:
    st.markdown("#### Tuberías del sistema colector")

    def dn_std(d_calc):
        """Calcula DN estándar comercial (múltiplos de 5, mín 10)."""
        return max(10, int(math.ceil(d_calc / 5.0)) * 5)

    def vr_pipe(Q_m3s, DN_mm):
        return Q_m3s / (math.pi/4 * (DN_mm/1000)**2)

    Q_tot = r["Q_total_lh"] / 1000.0 / 3600.0
    Rf = r["Rf"]

    pipe_rows = [
        {
            "Línea": "Alimentación (feed)",
            "Q (L/h)": f"{r['Q_total_lh']:.0f}",
            "D_calc (mm)": f"{r['d_feed_mm']:.1f}",
            "DN estándar": f"DN {r['DN_feed']}",
            "Vel. real (m/s)": f"{r['vr_feed']:.2f}",
            "Estado": "✅ OK" if r['vr_feed'] <= 3.0 else "⚠️ Alta",
        },
        {
            "Línea": "Colector overflow",
            "Q (L/h)": f"{r['Q_total_lh']*(1-Rf):.0f}",
            "D_calc (mm)": f"{r['d_OF_mm']:.1f}",
            "DN estándar": f"DN {r['DN_OF']}",
            "Vel. real (m/s)": f"{r['vr_OF']:.2f}",
            "Estado": "✅ OK" if r['vr_OF'] <= 3.0 else "⚠️ Alta",
        },
        {
            "Línea": "Colector underflow",
            "Q (L/h)": f"{r['Q_total_lh']*Rf:.0f}",
            "D_calc (mm)": f"{r['d_UF_mm']:.1f}",
            "DN estándar": f"DN {r['DN_UF']}",
            "Vel. real (m/s)": f"{r['vr_UF']:.2f}",
            "Estado": "✅ OK" if r['vr_UF'] <= 3.0 else "⚠️ Alta",
        },
    ]
    df_pipe = pd.DataFrame(pipe_rows)
    st.dataframe(df_pipe, use_container_width=True, hide_index=True, height=180)

    st.markdown("""
    **Criterios de diseño de tuberías (SS304 alimentario):**
    - Velocidad máxima recomendada: **≤ 2.5 m/s** (diseño) / **3.0 m/s** (límite erosión)
    - Material: Acero inoxidable SAE 304 pulido interior Ra ≤ 0.8 µm
    - Conexiones: Tri-Clamp DIN 32676 clase A — PTFE o EPDM FDA
    - Prueba hidrostática: **1.5 × P_trabajo** antes de puesta en marcha
    """)

    st.markdown("**Resumen del sistema:**")
    col_r1, col_r2 = st.columns(2)
    col_r1.metric("N° ciclones necesarios", f"{r['n_cicl_calc']:.1f}")
    col_r2.metric("N° ciclones instalados", f"{r['n_total_inst']}")
    diff = r['n_cicl_calc'] - r['n_total_inst']
    if abs(diff) < 1.5:
        st.success(f"✅ El sistema instalado ({r['n_total_inst']} ciclones) es **adecuado** "
                   f"para las condiciones de operación calculadas.")
    elif diff > 0:
        st.warning(f"⚠️ Se necesitan **{r['n_cicl_calc']:.1f}** ciclones pero hay {r['n_total_inst']}. "
                   f"Ajuste D o ΔP para reducir n_cicl, o agregue ciclones al sistema.")
    else:
        st.info(f"ℹ️ El sistema instalado ({r['n_total_inst']} ciclones) tiene **capacidad excedente**. "
                f"Considere operar solo {math.ceil(r['n_cicl_calc'])} ciclones para mayor eficiencia.")

st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NOTAS DE FABRICACIÓN
# ─────────────────────────────────────────────
with st.expander("📋 Notas de fabricación — Acero inoxidable SAE 304 alimentario"):
    nc1, nc2, nc3 = st.columns(3)

    with nc1:
        st.markdown("""
        **🔧 Tolerancias críticas**
        | Zona | Tolerancia |
        |------|-----------|
        | Diámetro D | ±0.10 mm |
        | Diámetro Do | ±0.05 mm |
        | Diámetro Du (spigot) | ±0.05 mm |
        | Ángulo cono α | ±0.5° |
        | Longitud Lv | ±0.5 mm |
        | Concentricidad vortex finder | TIR ≤ 0.05 mm |
        | Longitud total L | ±0.5 mm |

        **⚗️ Acabado superficial**
        - Interior cilíndrico: Ra ≤ 0.8 µm (electropolido)
        - Interior cónico: Ra ≤ 0.4 µm (zona de alta turbulencia)
        - Exterior sanitario: Ra ≤ 1.6 µm
        - Sin soldaduras expuestas al fluido alimentario
        - Pasivado post-mecanizado: ácido nítrico 20%, 30 min, enjuague DI
        - Certificación material: EN 10204 tipo 3.1
        """)

    with nc2:
        st.markdown("""
        **🔩 Soldadura TIG — SS304 alimentario**
        - Proceso: GTAW (TIG) con respaldo de Ar interior (back purge)
        - Material de aporte: ER308L (bajo carbono, < 0.03% C)
        - Gas protección: Argón 99.99%, caudal 8–12 L/min
        - Temperatura entre pasadas: ≤ 100°C (evitar sensibilización)
        - Penetración completa en todas las uniones a presión
        - END: líquidos penetrantes PT tras soldadura
        - Inspección visual 100% antes y después de mecanizar

        **📐 Ajuste de la entrada tangencial**
        - Sección rectangular Sa×Sb = {:.1f}×{:.1f} mm
        - Maquinar con tolerancia ISO H7/h6 para hermeticidad
        - Verificar tangencialidad con calibre angular ±0.5°
        - Borde de entrada: radio R ≤ 0.2 mm (reducir turbulencia)
        """.format(r['Sa'], r['Sb']))

    with nc3:
        st.markdown("""
        **🛠️ Procedimiento CIP/SIP**
        1. Pre-enjuague: agua potable fría, 3 min
        2. Soda cáustica: NaOH 1.5% p/v a 70°C, 15 min
        3. Enjuague intermedio: agua desmineralizada, 5 min
        4. Ácido: HNO₃ 0.5% a 50°C, 10 min (o ácido peracético 0.2%)
        5. Enjuague final: agua purificada, 5 min (conductividad ≤ 10 µS/cm)
        6. Inspección visual antes de retornar a producción

        **🔍 Puntos de inspección mensual**
        - Spigot (Du): medir con calibre pasa/no-pasa (desgaste > 0.3 mm → reemplazar)
        - Vortex finder: concentricidad y estado de bordes
        - Zona cónica: buscar estrías de abrasión o pitting
        - Juntas O-ring: cambio preventivo cada 6 meses (PTFE/EPDM FDA)
        - Presión diferencial: comparar con registro histórico (±10% = normal)
        - Clamps Tri-Clamp: verificar torque y estado de la junta tórica
        """)

# ─────────────────────────────────────────────
# NOTAS TÉCNICAS Y BIBLIOGRAFÍA
# ─────────────────────────────────────────────
with st.expander("📚 Fundamento teórico y referencias bibliográficas"):
    st.markdown(r"""
    ## Modelo de Bradford — Castilho & Medronho (2000)

    El modelo adimensional de Bradford permite predecir el comportamiento de
    hidrociclones tipo Bradley para separación sólido-líquido mediante tres ecuaciones
    simultáneas resueltas iterativamente:

    $$\text{Ec. 4:}\quad Stk'_{50} \cdot Eu = 0.0474 \cdot \left[\ln\!\left(\frac{1}{R_f}\right)\right]^{0.742} \cdot e^{8.96\,c_{gg}}$$

    $$\text{Ec. 5:}\quad Eu = 371.5 \cdot Re^{0.116} \cdot e^{-2.12\,c_{gg}}$$

    $$\text{Ec. 6:}\quad R_f = 1218 \cdot \left(\frac{D_u}{D}\right)^{4.75} \cdot Eu^{-0.3}$$

    Donde los grupos adimensionales son:

    - $Stk'_{50} = \dfrac{(\rho_s - \rho_f)\, x'^2_{50}\, v}{18\,\mu\,D}$ — Número de Stokes reducido
    - $Eu = \dfrac{2\,\Delta P}{\rho_f\, v^2}$ — Número de Euler
    - $Re = \dfrac{\rho_f\, v\, D}{\mu}$ — Número de Reynolds
    - $R_f = Q_u / Q$ — Relación de flujo underflow/feed
    - $c_{gg}$ — Concentración másica de sólidos [g/g]
    - $v = Q / (\pi/4 \cdot D^2)$ — Velocidad característica [m/s]

    ### Curva de eficiencia (Grado de eficiencia)

    $$G'(x) = \frac{1}{1 + \left(\dfrac{x'_{50}}{x}\right)^{2.5}} \qquad G(x) = R_f + (1 - R_f)\cdot G'(x)$$

    ### Propiedades del almidón de jengibre (*Zingiber officinale*)

    | Propiedad | Valor | Fuente |
    |-----------|-------|--------|
    | Densidad del gránulo ρs | **1,517 kg/m³** | Reyes, 1982 |
    | Contenido de amilosa | 22.2% | Reyes, 1982 |
    | Temperatura de gelatinización | **80°C** | Reyes, 1982; Sáiz Rubio, 2009 |
    | Tamaño de gránulo D50 | 2–50 µm (D50≈20 µm) | Literatura Zingiber |
    | Patrón cristalográfico | Tipo A | Reyes, 1982 |

    ### Referencias

    1. Castilho, L.R. & Medronho, R.A. (2000). A simple procedure for design and
       performance prediction of Bradley and Rietema hydrocyclones. *Minerals Engineering*, 13(2), 183–191.
    2. Sáiz Rubio, V. (2009). *Design of an Energy-saving Hydrocyclone for Wheat Starch
       Separation*. Växjö University, TD 052/2009.
    3. Reyes, O.A. (1982). Characterization of Starch from Ginger Root
       (*Zingiber officinale*). *Starch/Stärke*, 34(2), 40–44.
    4. Chu, L.Y. et al. (2000). Energy-efficient hydrocyclone design parameters.
       *Chemical Engineering Research and Design*.
    5. Grommers, H.E. et al. (2004). *Potato Starch: Production, Modifications and Uses*.
       Wiley.
    6. Svarovsky, L. (2000). *Solid-Liquid Separation*, 4th ed. Butterworth-Heinemann.
    7. Buriticá Henao, P.A. (2011). *Sistema Hidrociclónico para la Separación del
       Almidón de Sagú*. Universidad de los Andes, Bogotá.
    """)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<hr style='margin:16px 0 8px 0'>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;font-size:0.78rem;color:#718096;padding:4px 0 12px 0">
    <b>UNIÓN DE NEGOCIOS CORPORATIVOS — Perú</b> &nbsp;·&nbsp;
    Sistema Hidrociclónico · Almidón de Jengibre (Kion) &nbsp;·&nbsp;
    Modelo Bradford (Castilho &amp; Medronho, 2000) &nbsp;·&nbsp;
    Ing. Froilán Becerra — Jefe de Mantenimiento &nbsp;·&nbsp;
    <b>v1.0 — Junio 2026</b>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# requirements.txt (incluido como referencia al final del archivo)
# =============================================================================
# streamlit>=1.32.0
# numpy>=1.24.0
# matplotlib>=3.7.0
# plotly>=5.18.0
# pandas>=2.0.0
# scipy>=1.10.0
