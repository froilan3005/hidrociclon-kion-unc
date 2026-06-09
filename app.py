# =============================================================================
# app.py v3.0 — Sistema Hidrociclónico Kion — UNIÓN DE NEGOCIOS CORPORATIVOS
# Ing. Froilán Becerra — Jefe de Mantenimiento — Perú — Junio 2026
# Modelo Bradford (Castilho & Medronho, 2000)
# Vistas técnicas ISO 128 · Diámetros comerciales Tri-Clamp SS304
# Exportación DXF (ezdxf) + PDF (reportlab)
# =============================================================================

import streamlit as st
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc
import plotly.graph_objects as go
import pandas as pd
from scipy.optimize import brentq
import ezdxf, io, math

from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Image as RLImage, Table, TableStyle,
                                 PageBreak, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rlcolors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Hidrociclón Kion v3 — UNC",
                   page_icon="⚙️", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp,[data-testid="block-container"]{background-color:#F0F4F8!important}
    .main{background-color:#F0F4F8!important}
    [data-testid="stSidebar"]{background-color:#E2E8F0!important}
    [data-testid="stSidebar"]>div:first-child{background-color:#E2E8F0!important}
    h1{color:#1B3A6B;font-family:Arial,sans-serif;font-size:1.4rem}
    h2,h3{color:#2D5A8E;font-family:Arial,sans-serif}
    .stButton>button{background-color:#1B3A6B!important;color:white!important;
        font-weight:bold!important;border-radius:8px!important;
        padding:.5rem 1.5rem!important;border:none!important;width:100%!important}
    .stButton>button:hover{background-color:#2D5A8E!important}
    [data-testid="stMetric"]{background:#FFFFFF;border:1.5px solid #E2E8F0;
        border-radius:10px;padding:10px 14px;box-shadow:0 2px 5px rgba(0,0,0,.06)}
    [data-testid="stMetricLabel"]{color:#4A5568!important;font-size:.75rem!important}
    [data-testid="stMetricValue"]{color:#1B3A6B!important;font-size:1.2rem!important;font-weight:600!important}
    .stTabs [data-baseweb="tab"]{font-weight:600;color:#2D5A8E}
    .seccion{font-size:.7rem;font-weight:700;letter-spacing:1.5px;
        text-transform:uppercase;color:#718096;margin-bottom:4px;
        border-left:3px solid #2D5A8E;padding-left:8px}
    hr{border-color:#CBD5E0}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
RHO_S = 1517.0
T_GEL = 80.0
HP_TO_KW = 0.74570
ETA_BOMBA = 0.65
BANCOS = {1:4, 2:3, 3:2}
HP_BOMBAS = {1:3, 2:3, 3:2}

# Diámetros comerciales Tri-Clamp SS304 (denominación, OD_mm, ID_mm)
DIAMETROS_TC = [
    ('1/2"',  12.7,  11.0),
    ('3/4"',  19.05, 17.0),
    ('1"',    25.4,  22.0),
    ('1.5"',  38.1,  35.0),
    ('2"',    50.8,  47.5),
    ('2.5"',  63.5,  60.3),
    ('3"',    76.2,  72.9),
]

def seleccionar_DN(d_calc_mm, forzar_15=False):
    """Selecciona el DN Tri-Clamp comercial más pequeño con ID >= d_calc_mm."""
    if forzar_15:
        return ('1.5"', 38.1, 35.0)
    for nombre, od, id_ in DIAMETROS_TC:
        if id_ >= d_calc_mm:
            return (nombre, od, id_)
    return ('3"', 76.2, 72.9)

# Colores
CW='#1B3A6B'; CF='#D6EAF8'; CVF='#AED6F1'
CI='#2471A3'; CO='#1E8449'; CU='#A04000'; CC='#333333'
C_FER='#78909C'; FS=6.5; FI='italic'

# ─────────────────────────────────────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────────────────────────────────────
c0, c1 = st.columns([1, 9])
with c0:
    st.markdown("""<div style="width:56px;height:56px;background:linear-gradient(135deg,#1B3A6B,#2D5A8E);
    border-radius:12px;display:flex;align-items:center;justify-content:center;
    font-size:26px;margin-top:4px">⚙️</div>""", unsafe_allow_html=True)
with c1:
    st.markdown("""<div style="margin-top:2px">
    <div style="font-size:.7rem;font-weight:700;letter-spacing:2px;
         text-transform:uppercase;color:#718096">UNIÓN DE NEGOCIOS CORPORATIVOS — PERÚ</div>
    <h1 style="margin:2px 0 0 0">Sistema Hidrociclónico · Separación de Almidón de Kion · v3.0</h1>
    <div style="font-size:.8rem;color:#4A5568;margin-top:2px">
        Hy38/1100 · SAE 304 · Férulas Tri-Clamp · Diámetros comerciales ·
        Ing. Froilán Becerra — Jefe de Mantenimiento · 2026
    </div></div>""", unsafe_allow_html=True)
st.markdown("<hr style='margin:10px 0 16px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Parámetros de diseño")
    st.markdown("---")
    st.markdown('<div class="seccion">Fluido de proceso</div>', unsafe_allow_html=True)
    rho_f   = st.slider("Densidad jugo ρ_f (kg/m³)", 1010, 1060, 1035, 5)
    mu_mPas = st.slider("Viscosidad μ (mPa·s)", 1.0, 3.0, 1.8, 0.1)
    c_gL    = st.slider("Concentración sólidos (g/L)", 100, 300, 200, 10)
    T_proc  = st.slider("Temperatura proceso (°C)", 10, 40, 22, 1)
    st.markdown("---")
    st.markdown('<div class="seccion">Almidón — fijo (Reyes, 1982)</div>', unsafe_allow_html=True)
    st.info(f"ρ_s = **{RHO_S:.0f} kg/m³** | T_gel = **{T_GEL:.0f}°C**")
    st.markdown("---")
    st.markdown('<div class="seccion">Geometría</div>', unsafe_allow_html=True)
    D_mm       = st.slider("Diámetro D (mm)", 15.0, 80.0, 38.0, 0.5)
    Du_D_ratio = st.slider("Du/D (underflow)", 0.15, 0.30, 0.20, 0.01)
    Do_D_ratio = st.slider("Do/D (overflow)", 0.30, 0.50, 0.40, 0.02)
    alpha_deg  = st.slider("Ángulo cónico α (°)", 8, 20, 12, 1)
    st.markdown("---")
    st.markdown('<div class="seccion">Condición operativa</div>', unsafe_allow_html=True)
    modo = st.radio("Modo de cálculo", ["Fijar ΔP (kPa)", "Fijar v entrada (m/s)"])
    if "ΔP" in modo:
        dP_input = st.slider("Presión de trabajo ΔP (kPa)", 50, 700, 300, 10)
        v_input  = None
    else:
        v_input  = st.slider("Velocidad v (m/s)", 0.3, 10.0, 2.0, 0.1)
        dP_input = None
    st.markdown("---")
    st.markdown('<div class="seccion">Sistema instalado</div>', unsafe_allow_html=True)
    Q_total_lh   = st.slider("Caudal total (L/h)", 500, 3000, 1500, 50)
    n_total_inst = st.number_input("N° ciclones instalados", 1, 30, 9, 1)
    st.markdown("---")
    calcular = st.button("▶ CALCULAR DISEÑO")

# ─────────────────────────────────────────────────────────────────────────────
# MODELO BRADFORD
# ─────────────────────────────────────────────────────────────────────────────
def modelo_bradford(D_mm, Du_D, Do_D, alpha_deg, rho_f, mu_Pas, c_gL, rho_s,
                    modo, dP_kPa=None, v_ms=None, Q_total_lh=1500):
    D = D_mm / 1000.0
    alpha_rad = math.radians(alpha_deg)
    c_gg = c_gL / rho_f
    if modo == "dP":
        dP_Pa = dP_kPa * 1000.0
        def eq_v(v):
            Re = rho_f * v * D / mu_Pas
            Eu = 371.5 * Re**0.116 * math.exp(-2.12 * c_gg)
            return Eu * rho_f * v**2 / 2.0 - dP_Pa
        try:
            v = brentq(eq_v, 0.001, 100.0)
        except:
            return None
    else:
        v = v_ms
    if v <= 0: return None
    Re = rho_f * v * D / mu_Pas
    Eu = 371.5 * Re**0.116 * math.exp(-2.12 * c_gg)
    Rf = 1218.0 * Du_D**4.75 * Eu**(-0.3)
    if not (0.001 < Rf < 0.999): return None
    LHS  = 0.0474 * (math.log(1/Rf)**0.742) * math.exp(8.96 * c_gg)
    Stk  = LHS / Eu
    denom = (rho_s - rho_f) * v
    if denom <= 0: return None
    x50_m = math.sqrt(Stk * 18.0 * mu_Pas * D / denom)
    dP_calc_kPa = Eu * rho_f * v**2 / 2.0 / 1000.0
    Q_cicl_Lh   = v * math.pi/4 * D**2 * 3600.0 * 1000.0
    n_cicl_calc = Q_total_lh / Q_cicl_Lh if Q_cicl_Lh > 0 else float('inf')

    Do_mm  = Do_D  * D_mm;  Du_mm  = Du_D  * D_mm
    Lcy_mm = 2.0   * D_mm;  Lco_mm = (D_mm/2 - Du_mm/2) / math.tan(alpha_rad)
    La_mm  = 10.0;           L_mm   = Lcy_mm + Lco_mm + La_mm
    Lv_mm  = 0.10  * L_mm;  Sa_mm  = math.sqrt(0.05 * D_mm**2)

    # Diámetros comerciales Tri-Clamp
    Do_dn, Do_od, Do_id = seleccionar_DN(Do_mm, forzar_15=True)
    Du_dn, Du_od, Du_id = seleccionar_DN(Du_mm)
    Ent_dn, Ent_od, Ent_id = seleccionar_DN(Sa_mm)

    x_d50 = 20e-6
    Gp_d50 = 1.0 / (1.0 + (x50_m / x_d50)**2.5)
    G_d50  = Rf + (1.0 - Rf) * Gp_d50

    HP_total = sum(HP_BOMBAS.values())
    pot_banco = {}
    for b, n_b in BANCOS.items():
        Q_b = Q_total_lh * HP_BOMBAS[b] / HP_total / 1000.0 / 3600.0
        P_W = dP_calc_kPa * 1000.0 * Q_b / ETA_BOMBA
        pot_banco[b] = {"Q_Lh": Q_b*3.6e6, "P_kW": P_W/1000,
                        "P_HP": P_W/(HP_TO_KW*1000), "nom_HP": HP_BOMBAS[b]}

    Q_tot = Q_total_lh / 1000.0 / 3600.0
    v_lim = 2.5
    d_feed = math.sqrt(4*Q_tot/(math.pi*v_lim))*1000
    d_OF   = math.sqrt(4*Q_tot*(1-Rf)/(math.pi*v_lim))*1000
    d_UF   = math.sqrt(4*Q_tot*Rf/(math.pi*v_lim))*1000
    dn_ = lambda d: seleccionar_DN(d)
    feed_dn,feed_od,feed_id = dn_(d_feed)
    of_dn,of_od,of_id       = seleccionar_DN(d_OF, forzar_15=True)
    uf_dn,uf_od,uf_id       = dn_(d_UF)
    vr_f = Q_tot/(math.pi/4*(feed_id/1000)**2)
    vr_o = Q_tot*(1-Rf)/(math.pi/4*(of_id/1000)**2)
    vr_u = Q_tot*Rf/(math.pi/4*(uf_id/1000)**2)

    return {
        "Re":Re,"Eu":Eu,"Stk":Stk,"Rf":Rf,"c_gg":c_gg,"v":v,
        "dP_kPa":dP_calc_kPa,"Q_cicl_Lh":Q_cicl_Lh,
        "x50_um":x50_m*1e6,"eff_d50":G_d50*100,
        "D":D_mm,"Do":Do_mm,"Du":Du_mm,"Lcy":Lcy_mm,"Lco":Lco_mm,
        "La":La_mm,"L":L_mm,"Lv":Lv_mm,"Sa":Sa_mm,"Sb":Sa_mm,"alpha":alpha_deg,
        "Do_D":Do_D,"Du_D":Du_D,
        "Do_dn":Do_dn,"Do_od":Do_od,"Do_id":Do_id,
        "Du_dn":Du_dn,"Du_od":Du_od,"Du_id":Du_id,
        "Ent_dn":Ent_dn,"Ent_od":Ent_od,"Ent_id":Ent_id,
        "n_cicl_calc":n_cicl_calc,"pot_banco":pot_banco,
        "Q_total_lh":Q_total_lh,"n_total_inst":n_total_inst,
        "feed_dn":feed_dn,"feed_od":feed_od,"of_dn":of_dn,"uf_dn":uf_dn,
        "vr_feed":vr_f,"vr_OF":vr_o,"vr_UF":vr_u,
        "d_feed_mm":d_feed,"d_OF_mm":d_OF,"d_UF_mm":d_UF,
        "T_proc":T_proc,"c_gL_input":c_gL,
        "rho_f_input":rho_f,"mu_input":mu_mPas,
    }

def curva_eficiencia(x50_m, Rf, n=200):
    x_um = np.linspace(1, 120, n)
    x_m  = x_um * 1e-6
    Gp   = 1.0 / (1.0 + (x50_m / x_m)**2.5)
    return x_um, (Rf + (1-Rf)*Gp)*100, Gp*100

# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO
# ─────────────────────────────────────────────────────────────────────────────
if "r" not in st.session_state:
    st.session_state["r"] = None

if calcular:
    with st.spinner("⚙️ Calculando…"):
        modo_c = "dP" if "ΔP" in modo else "v"
        res = modelo_bradford(D_mm, Du_D_ratio, Do_D_ratio, alpha_deg,
                              rho_f, mu_mPas*1e-3, c_gL, RHO_S,
                              modo_c, dP_kPa=dP_input, v_ms=v_input,
                              Q_total_lh=Q_total_lh)
        if res is None:
            st.error("❌ El modelo Bradford no convergió. Ajuste los parámetros.")
        else:
            st.session_state["r"] = res

r = st.session_state["r"]

if r is None:
    st.info("👈 Configure los parámetros y presione **▶ CALCULAR DISEÑO**")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📊 Resultados del modelo Bradford")
cols = st.columns(10)
kpis = [
    ("D principal",      f"{r['D']:.1f} mm",         None),
    ("ΔP hidrociclón",   f"{r['dP_kPa']:.1f} kPa",
     f"{'🟢' if r['dP_kPa']<=400 else '🟡' if r['dP_kPa']<=600 else '🔴'}"),
    ("x'₅₀ corte",       f"{r['x50_um']:.1f} µm",    None),
    ("Rf underflow",     f"{r['Rf']*100:.1f} %",      None),
    ("Vel. entrada",     f"{r['v']:.2f} m/s",
     f"{'🟢' if r['v']<=6 else '🟡' if r['v']<=8 else '🔴'}"),
    ("Q/ciclón",         f"{r['Q_cicl_Lh']:.1f} L/h", None),
    ("N° cicl. calc.",   f"{r['n_cicl_calc']:.1f}",   f"Inst:{r['n_total_inst']}"),
    ("DN Overflow",      f"{r['Do_dn']} ({r['Do_od']:.0f}mm OD)", None),
    ("DN Underflow",     f"{r['Du_dn']} ({r['Du_od']:.0f}mm OD)", None),
    ("DN Entrada",       f"{r['Ent_dn']} ({r['Ent_od']:.0f}mm OD)", None),
]
for col, (lbl, val, dlt) in zip(cols, kpis):
    with col: st.metric(lbl, val, dlt)

st.markdown("<hr style='margin:8px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES DE DIBUJO
# ─────────────────────────────────────────────────────────────────────────────
def _ferula_sec(ax, cx, y, od, alto=4, grosor=5, color=C_FER, zo=5):
    """Sección transversal de férula Tri-Clamp (par de labios)."""
    for signo in [-1, 1]:
        xbase = cx + signo * (od/2)
        xdir  = -signo
        ax.add_patch(plt.Rectangle((xbase + xdir*grosor, y-alto/2),
            grosor, alto, facecolor='#CFD8DC', edgecolor=color, lw=0.6, zorder=zo))

def _cota_v(ax, xc, y1, y2, sym, color=CC):
    ax.plot([xc-2,xc+2],[y1,y1],color=color,lw=0.35,ls=':')
    ax.plot([xc-2,xc+2],[y2,y2],color=color,lw=0.35,ls=':')
    ax.annotate('',xy=(xc,y2),xytext=(xc,y1),
        arrowprops=dict(arrowstyle='<->',color=color,lw=0.55,mutation_scale=5))
    ax.text(xc+2.5,(y1+y2)/2,sym,ha='left',va='center',
            fontsize=FS,color=color,style=FI,fontweight='bold')

def _cota_h(ax, yc, x1, x2, sym, color=CC, above=True):
    ax.plot([x1,x1],[yc-1.5,yc+1.5],color=color,lw=0.35,ls=':')
    ax.plot([x2,x2],[yc-1.5,yc+1.5],color=color,lw=0.35,ls=':')
    ax.annotate('',xy=(x2,yc),xytext=(x1,yc),
        arrowprops=dict(arrowstyle='<->',color=color,lw=0.55,mutation_scale=5))
    off = 3 if above else -3
    ax.text((x1+x2)/2, yc+off, sym, ha='center',
            va='bottom' if above else 'top',
            fontsize=FS, color=color, style=FI, fontweight='bold')

def _cartucho(ax, bx, by, vista, plano, escala="1:1"):
    ax.add_patch(plt.Rectangle((bx,by-34),84,36,
        facecolor='white',edgecolor='#222',lw=0.8,zorder=10))
    for dy in [18,10]:
        ax.plot([bx,bx+84],[by-dy,by-dy],color='#333',lw=0.4,zorder=11)
    ax.text(bx+42,by-2,'UNIÓN DE NEGOCIOS CORPORATIVOS',ha='center',
            fontsize=5.5,fontweight='bold',color=CW,zorder=12)
    ax.text(bx+42,by-12,f'Hidrociclón Kion — {vista}',ha='center',
            fontsize=5,color='#333',zorder=12)
    ax.text(bx+42,by-21,f'{plano} | Esc. {escala} (mm) | SAE 304',ha='center',
            fontsize=4.5,color='#555',zorder=12)
    ax.text(bx+42,by-29,'Ing. F. Becerra | Jun 2026 | Rev.0',ha='center',
            fontsize=4.5,color='#555',zorder=12)

def fig_to_bytes(fig, dpi=200):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf

# ─────────────────────────────────────────────────────────────────────────────
# VISTA 1 — CORTE A-A LONGITUDINAL
# ─────────────────────────────────────────────────────────────────────────────
def fig_longitudinal(r):
    D=r['D']; Do=r['Do']; Du=r['Du']; Lcy=r['Lcy']; Lco=r['Lco']
    La=r['La']; L=r['L']; Lv=r['Lv']; alpha=r['alpha']
    Do_od=r['Do_od']; Du_od=r['Du_od']; Ent_od=r['Ent_od']

    fig, ax = plt.subplots(figsize=(9, 11), facecolor='white')
    ax.set_facecolor('white')
    cx=0; y0=0
    ep_pared = 2.0  # espesor pared SS304

    # ── Eje de simetría ──
    ax.axvline(cx, color='#BBBBBB', lw=0.4, ls=(0,(8,3,2,3)), zorder=1)

    # ── Vórtex finder (pieza desmontable, arriba) ──
    # Exterior VF
    ax.add_patch(plt.Rectangle((-Do/2, y0-Lv), Do, Lv,
        facecolor=CVF, edgecolor=CI, lw=0.9, ls='--', zorder=3, alpha=0.85))
    # Pared del VF
    for signo in [-1, 1]:
        ax.add_patch(plt.Rectangle((signo*(Do/2-ep_pared), y0-Lv),
            ep_pared, Lv, facecolor='#90A4AE', edgecolor=CI, lw=0.4, zorder=4, alpha=0.6))
    # Férula VF en tapa superior
    _ferula_sec(ax, cx, y0, Do_od, alto=4, grosor=5, color=CI, zo=6)

    # ── Cuerpo cilíndrico ──
    # Relleno interior
    ax.add_patch(plt.Rectangle((-D/2+ep_pared, y0), D-2*ep_pared, Lcy,
        facecolor=CF, edgecolor='none', zorder=2))
    # Paredes (izquierda y derecha)
    for signo in [-1, 1]:
        ax.add_patch(plt.Rectangle((signo*(D/2-ep_pared), y0), ep_pared, Lcy,
            facecolor='#90A4AE', edgecolor=CW, lw=0.5, zorder=3))
    # Contorno exterior cilindro
    ax.add_patch(plt.Rectangle((-D/2, y0), D, Lcy,
        facecolor='none', edgecolor=CW, lw=1.5, zorder=4))
    # Tapa superior (con hueco VF)
    ax.plot([-D/2, -Do/2], [y0, y0], color=CW, lw=1.5, zorder=5)
    ax.plot([ Do/2,  D/2], [y0, y0], color=CW, lw=1.5, zorder=5)

    # ── Entrada tangencial circular (vista lateral del tubo tangencial) ──
    # En vista longitudinal (corte A-A): el tubo entra horizontalmente
    # pero su eje es tangente al cuerpo (no radial)
    # El tubo está desplazado D/2 + Ent_od/2 del eje central
    ent_y   = y0 + Lcy * 0.35
    ent_R   = Ent_od / 2        # radio exterior de la conexión
    ent_id  = r['Ent_id'] / 2   # radio interior
    ent_len = ent_R * 4.5       # longitud del tubo visible
    ent_x0  = -D/2 - ent_len    # extremo exterior del tubo
    # Pared superior e inferior del tubo de entrada
    ax.plot([ent_x0, -D/2], [ent_y+ent_R,   ent_y+ent_R],   color=CI, lw=1.0, zorder=4)
    ax.plot([ent_x0, -D/2], [ent_y-ent_R,   ent_y-ent_R],   color=CI, lw=1.0, zorder=4)
    ax.plot([ent_x0, -D/2], [ent_y+ent_id,  ent_y+ent_id],  color=CI, lw=0.4, ls='--', zorder=4)
    ax.plot([ent_x0, -D/2], [ent_y-ent_id,  ent_y-ent_id],  color=CI, lw=0.4, ls='--', zorder=4)
    # Interior del tubo
    ax.fill_between([ent_x0, -D/2], ent_y-ent_id, ent_y+ent_id,
        facecolor=CF, alpha=0.7, zorder=3)
    # Pared del tubo
    ax.fill_between([ent_x0, -D/2], ent_y+ent_id, ent_y+ent_R,
        facecolor='#90A4AE', alpha=0.6, zorder=3)
    ax.fill_between([ent_x0, -D/2], ent_y-ent_R, ent_y-ent_id,
        facecolor='#90A4AE', alpha=0.6, zorder=3)
    # Férula de entrada
    _ferula_sec(ax, ent_x0, ent_y, Ent_od, alto=4, grosor=5, color=CI, zo=6)
    # Flecha de flujo entrada
    ax.annotate('', xy=(-D/2-ent_R, ent_y), xytext=(ent_x0+2, ent_y),
        arrowprops=dict(arrowstyle='->', color=CI, lw=1.5), zorder=7)
    ax.text(ent_x0-2, ent_y, f'Entrada tangencial\nDN {r["Ent_dn"]}\n(eje tangente al cuerpo)',
            ha='right', va='center', fontsize=6, color=CI)

    # ── Férula cilindro–cono ──
    _ferula_sec(ax, cx, y0+Lcy, D+4, alto=5, grosor=6, color=C_FER, zo=5)

    # ── Cuerpo cónico ──
    cone_o = [[-D/2,y0+Lcy],[D/2,y0+Lcy],[Du/2,y0+Lcy+Lco],[-Du/2,y0+Lcy+Lco]]
    ax.add_patch(plt.Polygon(cone_o, facecolor='#C8DCF0', edgecolor=CW, lw=1.5, zorder=2))
    # Pared interior del cono (línea de trazos)
    ax.plot([-D/2+ep_pared, -Du/2+ep_pared*0.5],
            [y0+Lcy, y0+Lcy+Lco], color=CW, lw=0.4, ls='--', zorder=3)
    ax.plot([D/2-ep_pared,   Du/2-ep_pared*0.5],
            [y0+Lcy, y0+Lcy+Lco], color=CW, lw=0.4, ls='--', zorder=3)

    # ── Férula cono–spigot ──
    _ferula_sec(ax, cx, y0+Lcy+Lco, Du_od+8, alto=4, grosor=5, color=C_FER, zo=5)

    # ── Spigot ──
    ax.add_patch(plt.Rectangle((-Du/2, y0+Lcy+Lco), Du, La,
        facecolor='#BCD4E8', edgecolor=CW, lw=1.5, zorder=2))
    # Pared interior spigot
    for signo in [-1, 1]:
        ax.add_patch(plt.Rectangle((signo*(Du/2-ep_pared), y0+Lcy+Lco),
            ep_pared, La, facecolor='#90A4AE', edgecolor=CW, lw=0.4, zorder=3))
    # Férula final spigot
    _ferula_sec(ax, cx, y0+Lcy+Lco+La, Du_od+8, alto=4, grosor=5, color=CU, zo=5)

    # ── Flechas de flujo ──
    ax.annotate('', xy=(cx, y0-Lv-16), xytext=(cx, y0-Lv-2),
        arrowprops=dict(arrowstyle='->', color=CO, lw=2.0), zorder=7)
    ax.text(cx+2, y0-Lv-18, f'Overflow — DN {r["Do_dn"]}',
            ha='left', va='top', fontsize=6, color=CO)
    ax.annotate('', xy=(cx, y0+Lcy+Lco+La+16), xytext=(cx, y0+Lcy+Lco+La+2),
        arrowprops=dict(arrowstyle='->', color=CU, lw=2.0), zorder=7)
    ax.text(cx+2, y0+Lcy+Lco+La+18, f'Underflow — DN {r["Du_dn"]}',
            ha='left', va='bottom', fontsize=6, color=CU)

    # ── COTAS ISO 128 ──
    xd = [D/2+14, D/2+26, D/2+38, D/2+50]
    _cota_v(ax, xd[0], y0-Lv,        y0,                    'Lv')
    _cota_v(ax, xd[1], y0,            y0+Lcy,                'Lcy')
    _cota_v(ax, xd[1], y0+Lcy,        y0+Lcy+Lco,           'Lco')
    _cota_v(ax, xd[0], y0+Lcy+Lco,   y0+Lcy+Lco+La,         'La')
    _cota_v(ax, xd[3], y0,            y0+Lcy+Lco+La,         'L', CW)
    _cota_h(ax, y0-Lv-12, -D/2,  D/2,  f'D={r["D"]:.1f}',   CW,  above=False)
    _cota_h(ax, y0-Lv-20, -Do/2, Do/2, f'Do  DN {r["Do_dn"]}', CI, above=False)
    _cota_h(ax, y0+Lcy+Lco+La+6,
            -Du/2, Du/2, f'Du  DN {r["Du_dn"]}', CU, above=True)
    # Cota entrada
    _cota_v(ax, -D/2-ent_len-12, ent_y-ent_R, ent_y+ent_R,
            f'DN {r["Ent_dn"]}', CI)
    # Ángulo α
    ax.text(-D/4, y0+Lcy+Lco*0.4, 'α',
            ha='right', va='center', fontsize=FS+1,
            color='#8B0000', style=FI, fontweight='bold')
    # Línea corte A-A
    xl = -D/2-ent_len-22
    xr = xd[3]+10
    ax.plot([xl, xr], [y0+Lcy*0.5]*2, color='#CC0000',
            lw=0.6, ls=(0,(8,2,2,2)), zorder=1)
    ax.text(xl-2, y0+Lcy*0.5, 'A', ha='right', va='center',
            fontsize=8, color='#CC0000', fontweight='bold')
    ax.text(xr+2,  y0+Lcy*0.5, 'A', ha='left',  va='center',
            fontsize=8, color='#CC0000', fontweight='bold')
    # Escala gráfica
    sbx=-D/2; sby=y0+Lcy+Lco+La+34
    ax.plot([sbx,sbx+20],[sby,sby],color='#333',lw=1.5)
    ax.plot([sbx,sbx],[sby-1,sby+1],color='#333',lw=1.5)
    ax.plot([sbx+20,sbx+20],[sby-1,sby+1],color='#333',lw=1.5)
    ax.text(sbx+10,sby+2,'20 mm',ha='center',va='bottom',fontsize=6,color='#333')
    # Cartucho
    _cartucho(ax, xd[3]+14, y0+Lcy+Lco, 'Corte A-A (Vista Longitudinal)', 'HK-001-R0')

    ax.invert_yaxis()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-D/2-ent_len-30, xd[3]+105)
    ax.set_ylim(y0+Lcy+Lco+La+50, y0-Lv-30)
    fig.tight_layout(pad=0.4)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# VISTA 2 — CORTE B-B SUPERIOR
# ─────────────────────────────────────────────────────────────────────────────
def fig_superior(r):
    D=r['D']; Do=r['Do']; Do_od=r['Do_od']
    Ent_od=r['Ent_od']; Ent_id=r['Ent_id']
    ep=2.0

    fig, ax = plt.subplots(figsize=(8, 7), facecolor='white')
    ax.set_facecolor('white')
    cx=cy=0.0

    # Pared del cuerpo (anillo)
    ax.add_patch(plt.Circle((cx,cy), D/2, facecolor='#90A4AE', edgecolor=CW, lw=1.5, zorder=2))
    ax.add_patch(plt.Circle((cx,cy), D/2-ep, facecolor=CF, edgecolor=CW, lw=0.5, zorder=3))
    # Vortex finder (línea de trazos)
    ax.add_patch(plt.Circle((cx,cy), Do/2, facecolor=CVF, edgecolor=CI,
        lw=0.8, ls='--', zorder=4, alpha=0.75))
    ax.add_patch(plt.Circle((cx,cy), Do/2-ep, facecolor='white', edgecolor=CI,
        lw=0.4, ls='--', zorder=5, alpha=0.5))
    # Ejes de simetría
    ax.plot([cx-D/2-6,cx+D/2+6],[cy,cy], color='#BBBBBB', lw=0.4, ls=(0,(8,3,2,3)), zorder=1)
    ax.plot([cx,cx],[cy-D/2-6,cy+D/2+6], color='#BBBBBB', lw=0.4, ls=(0,(8,3,2,3)), zorder=1)

    # ── Entrada tangencial CORRECTA en vista planta ──
    # El eje del tubo es tangente al exterior del cuerpo cilíndrico.
    # La pared interior del tubo coincide con la pared exterior del cuerpo.
    # Eje del tubo: X = -(D/2 + Ent_od/2), dirección vertical (Y).
    # El fluido entra tangencialmente, generando el vórtice sin turbulencia de choque.
    import numpy as _np_s
    eje_x   = cx - D/2 - Ent_od/2      # eje del tubo (tangente a la pared exterior)
    y_fin   = cy                         # punto de conexión con el cuerpo
    y_ini   = y_fin + Ent_od * 4.5      # extremo libre del tubo (con férula)

    # Cuerpo del tubo (zona exterior e interior)
    ax.fill_between([eje_x - Ent_od/2, eje_x + Ent_od/2],
        [y_fin]*2, [y_ini]*2, facecolor='#90A4AE', alpha=0.7, zorder=4)
    ax.fill_between([eje_x - Ent_id/2, eje_x + Ent_id/2],
        [y_fin]*2, [y_ini]*2, facecolor=CF, alpha=0.85, zorder=5)
    # Contornos exteriores del tubo
    for xw in [eje_x - Ent_od/2, eje_x + Ent_od/2]:
        ax.plot([xw, xw], [y_fin, y_ini], color=CI, lw=1.2, zorder=6)
    # Paredes interiores (línea de trazos)
    for xw in [eje_x - Ent_id/2, eje_x + Ent_id/2]:
        ax.plot([xw, xw], [y_fin, y_ini], color=CI, lw=0.4, ls='--', zorder=6)
    # Cierre inferior del tubo (línea que une con el cuerpo del ciclón)
    ax.plot([eje_x - Ent_od/2, cx - D/2], [y_fin, y_fin], color=CI, lw=0.8, zorder=6)
    # Arco del cilindro exterior con la abertura tangencial
    theta_gap = _np_s.degrees(_np_s.arctan2(Ent_od/2, D/2)) * 1.1
    t_end   = _np_s.radians(90 + theta_gap)
    t_start = _np_s.radians(90 - theta_gap)
    t_arc   = _np_s.linspace(t_end, t_start + 2*_np_s.pi, 200)
    ax.plot(cx + D/2*_np_s.cos(t_arc), cy + D/2*_np_s.sin(t_arc),
            color=CW, lw=1.5, zorder=7)
    # Redibuja interior
    ax.add_patch(plt.Circle((cx, cy), D/2-ep, facecolor=CF,
        edgecolor=CW, lw=0.5, zorder=3))
    ax.add_patch(plt.Circle((cx,cy), Do/2, facecolor=CVF, edgecolor=CI,
        lw=0.8, ls='--', zorder=4, alpha=0.75))
    ax.add_patch(plt.Circle((cx,cy), Do/2-ep, facecolor='white', edgecolor=CI,
        lw=0.4, ls='--', zorder=5, alpha=0.5))
    # Férula Tri-Clamp en el extremo libre del tubo
    ax.plot([eje_x - Ent_od/2 - 3, eje_x + Ent_od/2 + 3],
            [y_ini, y_ini], color=CI, lw=3.0, zorder=6)
    # Flecha de flujo (el fluido entra fluyendo hacia abajo)
    ax.annotate('', xy=(eje_x, y_fin + Ent_od),
        xytext=(eje_x, y_ini - 2),
        arrowprops=dict(arrowstyle='->', color=CI, lw=1.8), zorder=8)
    ax.text(eje_x - Ent_od/2 - 3, (y_fin + y_ini)/2,
            f'Entrada tangencial\nDN {r["Ent_dn"]}',
            ha='right', va='center', fontsize=6, color=CI)

    # Línea de corte A-A
    ax.plot([-D/2-4, D/2+4], [D/2+8, D/2+8],
            color='#CC0000', lw=0.7, ls=(0,(8,2,2,2)))
    ax.text(-D/2-6, D/2+8, 'A', ha='right', va='center',
            fontsize=7, color='#CC0000', fontweight='bold')
    ax.text( D/2+6, D/2+8, 'A', ha='left',  va='center',
            fontsize=7, color='#CC0000', fontweight='bold')

    # Cotas
    _cota_h(ax, -D/2-10, -D/2, D/2,   f'D={r["D"]:.1f}mm', CW,  above=False)
    _cota_h(ax, -Do/2-6, -Do/2, Do/2, f'Do DN {r["Do_dn"]}', CI, above=False)
    _cota_v(ax,  D/2+12, cy-Ent_od/2, cy+Ent_od/2,
            f'Ø {r["Ent_dn"]}', CI)
    # Cartucho
    _cartucho(ax, D/2+22, D/2+10, 'Corte B-B (Vista Superior — Planta)', 'HK-002-R0')

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-D/2-Ent_od*2-20, D/2+108)
    ax.set_ylim(-D/2-28, D/2+Ent_od*5+15)
    fig.tight_layout(pad=0.4)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# VISTA 3 — DETALLE ENTRADA TANGENCIAL (escala ~3:1)
# ─────────────────────────────────────────────────────────────────────────────
def fig_entrada_tangencial(r):
    D=r['D']; Ent_od=r['Ent_od']; Ent_id=r['Ent_id']; v=r['v']
    sc=3.0
    Dsc=D*sc/2; Ent_od_sc=Ent_od*sc; Ent_id_sc=Ent_id*sc; ep_sc=2.0*sc

    fig, ax = plt.subplots(figsize=(9, 7), facecolor='white')
    ax.set_facecolor('white')
    cx=cy=0.0

    # Arco del cuerpo cilíndrico (sección transversal ampliada)
    theta = np.linspace(100, 260, 100)
    xarc_o = cx + Dsc * np.cos(np.radians(theta))
    yarc_o = cy + Dsc * np.sin(np.radians(theta))
    xarc_i = cx + (Dsc-ep_sc) * np.cos(np.radians(theta))
    yarc_i = cy + (Dsc-ep_sc) * np.sin(np.radians(theta))
    # Pared del cuerpo
    ax.fill(np.concatenate([xarc_o, xarc_i[::-1]]),
            np.concatenate([yarc_o, yarc_i[::-1]]),
            facecolor='#90A4AE', edgecolor=CW, lw=1.2, zorder=2)
    # Interior del cuerpo
    ax.fill(xarc_i, yarc_i, facecolor=CF, alpha=0.4, zorder=1)
    # Contorno exterior
    ax.plot(xarc_o, yarc_o, color=CW, lw=1.5, zorder=3)

    # Tubo de entrada (sección ampliada)
    ent_xf = cx - Dsc + ep_sc*0.5
    ent_x0 = ent_xf - Ent_od_sc * 3.0
    # Pared del tubo
    ax.fill_between([ent_x0, ent_xf],
        cy+Ent_id_sc/2, cy+Ent_od_sc/2, facecolor='#90A4AE', alpha=0.8, zorder=3)
    ax.fill_between([ent_x0, ent_xf],
        cy-Ent_od_sc/2, cy-Ent_id_sc/2, facecolor='#90A4AE', alpha=0.8, zorder=3)
    ax.fill_between([ent_x0, ent_xf],
        cy-Ent_id_sc/2, cy+Ent_id_sc/2, facecolor=CF, alpha=0.7, zorder=3)
    # Líneas de contorno
    ax.plot([ent_x0,ent_xf],[cy+Ent_od_sc/2,cy+Ent_od_sc/2], color=CI, lw=1.2, zorder=4)
    ax.plot([ent_x0,ent_xf],[cy-Ent_od_sc/2,cy-Ent_od_sc/2], color=CI, lw=1.2, zorder=4)
    ax.plot([ent_x0,ent_xf],[cy+Ent_id_sc/2,cy+Ent_id_sc/2], color=CI, lw=0.5, ls='--', zorder=4)
    ax.plot([ent_x0,ent_xf],[cy-Ent_id_sc/2,cy-Ent_id_sc/2], color=CI, lw=0.5, ls='--', zorder=4)
    # Férula (representada como rectángulo doble)
    for signo in [-1, 1]:
        ybase = cy + signo*(Ent_od_sc/2)
        ydir  = signo * ep_sc * 0.7
        ax.add_patch(plt.Rectangle((ent_x0-ep_sc*1.5, ybase),
            ep_sc*1.5, ydir, facecolor='#CFD8DC', edgecolor=CI, lw=0.8, zorder=5))
    # Flechas de flujo
    for frac in [0.25, 0.5, 0.75]:
        fy = cy - Ent_id_sc/2 + Ent_id_sc*frac
        ax.annotate('', xy=(ent_xf-ep_sc, fy), xytext=(ent_x0+Ent_od_sc*0.3, fy),
            arrowprops=dict(arrowstyle='->', color=CI, lw=1.0), zorder=6)
    # Radios de curvatura
    r_u = ep_sc * 1.2
    ax.add_patch(Arc((ent_xf, cy+Ent_od_sc/2+r_u), r_u*2, r_u*2,
        angle=0, theta1=270, theta2=360, color='#E74C3C', lw=0.7, linestyle='--'))
    ax.add_patch(Arc((ent_xf, cy-Ent_od_sc/2-r_u), r_u*2, r_u*2,
        angle=0, theta1=0, theta2=90,   color='#E74C3C', lw=0.7, linestyle='--'))

    # Cotas
    _cota_v(ax, ent_x0-ep_sc*3, cy-Ent_id_sc/2, cy+Ent_id_sc/2,
            f'Ø int\n{r["Ent_id"]:.0f}mm', CI)
    _cota_v(ax, ent_x0-ep_sc*6, cy-Ent_od_sc/2, cy+Ent_od_sc/2,
            f'Ø ext\n{r["Ent_od"]:.1f}mm', CI)
    _cota_h(ax, cy+Ent_od_sc/2+ep_sc*2, ent_x0, ent_xf,
            f'L tubo (ref.)', CI, above=True)
    _cota_v(ax, ent_xf+Dsc+10, cy-ep_sc/2, cy+ep_sc/2, 'e=2mm', '#8B0000')
    _cota_h(ax, cy-Ent_od_sc/2-ep_sc*2,
            cx-Dsc, cx+Dsc, f'D={r["D"]:.1f}mm (ref.)', CW, above=False)

    # Notas técnicas
    nx = cx + Dsc + 8
    ax.text(nx, cy+Ent_od_sc/2+4, 'Notas técnicas:', fontsize=7.5,
            fontweight='bold', color='#222')
    notas = [
        f'DN conexión: {r["Ent_dn"]} Tri-Clamp SS304',
        f'Ø exterior férula: {r["Ent_od"]:.1f} mm',
        f'Ø interior útil: {r["Ent_id"]:.1f} mm',
        f'v entrada = {v:.2f} m/s',
        'Ra interior ≤ 0.4 µm (pulido)',
        'Soldadura TIG ER308L — back purge Ar',
        'Borde entrada: R ≤ 0.2 mm',
        'Espesor pared e = 2.0 mm (SAE 304)',
    ]
    for i, n in enumerate(notas):
        ax.text(nx, cy+Ent_od_sc/2-3-i*7.5, f'• {n}', fontsize=6.5, color='#333')

    _cartucho(ax, nx, cy-Ent_od_sc/2-6,
              'Detalle Entrada Tangencial (Esc. ~3:1)', 'HK-003-R0', '~3:1')

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(ent_x0-ep_sc*9, cx+Dsc+102)
    ax.set_ylim(cy-Ent_od_sc/2-ep_sc*4-30, cy+Ent_od_sc/2+ep_sc*3+20)
    fig.tight_layout(pad=0.4)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# VISTA 4 — ISOMÉTRICA
# ─────────────────────────────────────────────────────────────────────────────
def fig_isometrica(r):
    D=r['D']; Do=r['Do']; Du=r['Du']
    Lcy=r['Lcy']; Lco=r['Lco']; La=r['La']; Lv=r['Lv']
    Ent_od=r['Ent_od']; Do_od=r['Do_od']

    fig, ax = plt.subplots(figsize=(9, 10), facecolor='white')
    ax.set_facecolor('white')

    ang = math.radians(30)
    def iso(x, y, z):
        return (x-y)*math.cos(ang), (x+y)*math.sin(ang) + z

    def elipse_iso(cx, cy, cz, rx, fill, edge, lw=1.0, ls='-', alpha=1.0, zo=2):
        t  = np.linspace(0, 2*math.pi, 80)
        pts = [iso(cx+rx*np.cos(a), cy+rx*0.38*np.sin(a), cz) for a in t]
        ax.fill([p[0] for p in pts], [p[1] for p in pts],
                facecolor=fill, edgecolor=edge, lw=lw, ls=ls, alpha=alpha, zorder=zo)

    def cara_lat(R_t, R_b, zt, zb, fill, edge, lw=1.0, zo=3):
        t = np.linspace(-math.pi/2, math.pi/2, 50)
        pt = [iso(R_t*np.cos(a), R_t*0.38*np.sin(a), zt) for a in t]
        pb = [iso(R_b*np.cos(a), R_b*0.38*np.sin(a), zb) for a in t]
        xi = [p[0] for p in pt] + [p[0] for p in pb[::-1]]
        yi = [p[1] for p in pt] + [p[1] for p in pb[::-1]]
        ax.fill(xi, yi, facecolor=fill, edgecolor=edge, lw=lw, zorder=zo)

    def anillo_iso(cx, cy, cz, r_ext, r_int, fill, edge, lw=0.8, zo=5):
        t = np.linspace(0, 2*math.pi, 80)
        po = [iso(cx+r_ext*np.cos(a), cy+r_ext*0.38*np.sin(a), cz) for a in t]
        pi_ = [iso(cx+r_int*np.cos(a), cy+r_int*0.38*np.sin(a), cz) for a in t]
        ax.fill([p[0] for p in po], [p[1] for p in po],
                facecolor=fill, edgecolor=edge, lw=lw, zorder=zo)
        ax.fill([p[0] for p in pi_], [p[1] for p in pi_],
                facecolor='white', edgecolor=edge, lw=lw*0.6, zorder=zo+1)

    R=D/2; Ro=Do/2; Ru=Du/2; z0=0
    ep=2.0

    # Tapa superior
    elipse_iso(0,0, z0, R, '#C8D8EA', CW, lw=1.2, zo=5)
    elipse_iso(0,0, z0, Ro, CVF, CI, lw=0.8, ls='--', zo=6)
    # Anillo férula VF
    anillo_iso(0,0, z0, Do_od/2+5, Do/2, '#CFD8DC', CI, zo=7)

    # Vórtex finder
    cara_lat(Ro, Ro, z0-Lv, z0, CVF, CI, lw=0.8, zo=4)
    elipse_iso(0,0, z0-Lv, Ro, CVF, CI, lw=0.8, ls='--', alpha=0.85, zo=8)

    # Cilindro
    cara_lat(R, R, z0, z0+Lcy, CF, CW, lw=1.2, zo=3)
    elipse_iso(0,0, z0+Lcy, R, '#B8CCE0', CW, lw=0.7, alpha=0.8, zo=4)
    # Anillo férula cil-cono
    anillo_iso(0,0, z0+Lcy, R+6, R, '#CFD8DC', C_FER, zo=6)

    # Cono
    cara_lat(R, Ru, z0+Lcy, z0+Lcy+Lco, '#C0D5E8', CW, lw=1.2, zo=3)
    elipse_iso(0,0, z0+Lcy+Lco, Ru, '#B0C4D8', CW, lw=0.7, alpha=0.8, zo=4)
    # Anillo férula cono-spigot
    anillo_iso(0,0, z0+Lcy+Lco, Ru+6, Ru, '#CFD8DC', C_FER, zo=6)

    # Spigot
    zs = z0+Lcy+Lco
    cara_lat(Ru, Ru, zs, zs+La, '#B8CCE0', CW, lw=1.2, zo=3)
    elipse_iso(0,0, zs+La, Ru, '#A8BCE8', CW, lw=0.8, zo=4)
    anillo_iso(0,0, zs+La, r['Du_od']/2+4, Ru, '#CFD8DC', CU, zo=6)

    # Entrada tangencial (tubo circular lateral)
    ez = z0 + Lcy*0.35
    er = Ent_od/2
    for dz_off in np.linspace(0, er*0.8, 5):
        a_val = math.pi + math.pi/6
        x0_, y0_ = -R*math.cos(a_val)*0.9, -R*math.sin(a_val)*0.9
        cara_lat(er, er, ez+dz_off, ez+dz_off+er*0.8,
                 '#90A4AE', CI, lw=0.4, zo=4)
    # Tubo entrada simplificado
    t_ent = np.linspace(math.pi/2, 3*math.pi/2, 30)
    for z_off in [0, er*0.7]:
        pts_e = [iso(-R-Ent_od*2+Ent_od*np.cos(a)*0.6,
                      Ent_od*np.sin(a)*0.4, ez+z_off) for a in t_ent]
        ax.plot([p[0] for p in pts_e], [p[1] for p in pts_e],
                color=CI, lw=0.8, zorder=4)
    xi_t, yi_t = iso(-R-Ent_od*2.5, 0, ez+er*0.35)
    ax.annotate('', xy=iso(-R-Ent_od*0.5, 0, ez+er*0.35),
        xytext=(xi_t, yi_t),
        arrowprops=dict(arrowstyle='->', color=CI, lw=1.5), zorder=9)

    # Flechas flujo
    xov,yov = iso(0,0, z0-Lv-10)
    ax.annotate('', xy=(xov,yov+10), xytext=(xov,yov),
        arrowprops=dict(arrowstyle='->', color=CO, lw=1.5), zorder=9)
    ax.text(xov+2, yov+12, f'Overflow\nDN {r["Do_dn"]}', fontsize=6.5, color=CO)
    xuf,yuf = iso(0,0, zs+La+5)
    ax.annotate('', xy=(xuf,yuf-9), xytext=(xuf,yuf),
        arrowprops=dict(arrowstyle='->', color=CU, lw=1.5), zorder=9)
    ax.text(xuf+2, yuf-12, f'Underflow\nDN {r["Du_dn"]}', fontsize=6.5, color=CU)
    ax.text(xi_t-2, yi_t, f'Entrada\nDN {r["Ent_dn"]}',
            fontsize=6.5, color=CI, ha='right')

    # Etiquetas con líneas de referencia
    def etiq_iso(px,py,pz,txt,color,dx=10,dy=8):
        x0,y0_ = iso(px,py,pz)
        ax.annotate(txt, xy=(x0,y0_), xytext=(x0+dx,y0_+dy),
            fontsize=7, color=color, style=FI, fontweight='bold',
            arrowprops=dict(arrowstyle='-', color=color, lw=0.6))

    etiq_iso(R+2, 0, z0+Lcy*0.5,   'D',   CW, 12, 0)
    etiq_iso(Ro+2,0, z0-Lv/2,      'Do',  CI, 12, 0)
    etiq_iso(Ru+2, 0, zs+La/2,     'Du',  CU, 12, 0)
    etiq_iso(R+14, 0, (z0+zs+La)/2,'L',   '#333', 14, 0)
    etiq_iso(R+2,  0, z0+Lcy+Lco/2,'Lco', '#555', 10, 6)

    # Pieza desmontable VF
    xvf, yvf = iso(Ro+8, 0, z0-Lv/2)
    ax.text(xvf+16, yvf+4, '↑ Vórtex finder\n  (pieza desmontable)',
            fontsize=6, color=CI, style=FI,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#EBF5FB',
                      edgecolor=CI, lw=0.5))

    # Cartucho
    xbt, ybt = iso(R+22, -R-14, z0+Lcy)
    ax.text(xbt, ybt+14, 'UNIÓN DE NEGOCIOS CORPORATIVOS',
            fontsize=5.5, fontweight='bold', color=CW)
    ax.text(xbt, ybt+8,  'Vista Isométrica — Hidrociclón Kion Hy38/1100',
            fontsize=5, color='#333')
    ax.text(xbt, ybt+2,  'HK-004-R0 | Sin escala | Jun 2026 | Rev.0',
            fontsize=4.5, color='#555')
    ax.text(xbt, ybt-3,  'Ing. F. Becerra | SAE 304 | Tri-Clamp',
            fontsize=4.5, color='#555')

    ax.set_aspect('equal')
    ax.axis('off')
    all_pts = [iso(x,y,z) for x,y,z in [
        (-R-Ent_od*3.5, 0, ez), (R+36,0,z0-Lv-12), (R+36,0,zs+La+14)]]
    xs=[p[0] for p in all_pts]; ys=[p[1] for p in all_pts]
    ax.set_xlim(min(xs)-22, max(xs)+80)
    ax.set_ylim(min(ys)-18, max(ys)+28)
    fig.tight_layout(pad=0.4)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# VISTA 5 — BANCO COMPLETO (Vista frontal de elevación)
# ─────────────────────────────────────────────────────────────────────────────
def fig_banco_completo(r):
    D=r['D']; Lcy=r['Lcy']; Lco=r['Lco']; La=r['La']; L=r['L']; Lv=r['Lv']
    n_b = BANCOS[1]  # Banco 1 = 4 ciclones
    sep = max(D*1.8, 60.0)  # separación entre ejes
    ancho_total = (n_b-1)*sep + D
    man_R = r['feed_od']/2 + 4     # radio del manifold
    man_y  = -(Lv + 18)            # altura del manifold (arriba)
    cuf_y  = Lcy+Lco+La+18         # altura colector underflow (abajo)

    fig, ax = plt.subplots(figsize=(12, 9), facecolor='white')
    ax.set_facecolor('white')

    # Manifold de alimentación (horizontal arriba)
    ax.add_patch(plt.Rectangle((-D/2-10, man_y-man_R),
        ancho_total+D/2+20, man_R*2,
        facecolor='#B0C4DE', edgecolor=CW, lw=1.0, zorder=2))
    ax.text(-D/2-10+ancho_total/2, man_y,
            f'Manifold alimentación — DN {r["feed_dn"]}',
            ha='center', va='center', fontsize=6.5, color=CW, fontweight='bold')

    # Colector overflow (horizontal, nivel tapa)
    of_y = -Lv - 6
    ax.add_patch(plt.Rectangle((-D/2-6, of_y-4),
        ancho_total+D/2+12, 8,
        facecolor='#D5F5E3', edgecolor=CO, lw=0.8, zorder=2))
    ax.text(-D/2-6 + (ancho_total+D/2+12)/2, of_y,
            f'Colector overflow — DN {r["of_dn"]}',
            ha='center', va='center', fontsize=6, color=CO)

    # Colector underflow (horizontal, abajo)
    ax.add_patch(plt.Rectangle((-D/2-6, cuf_y-4),
        ancho_total+D/2+12, 8,
        facecolor='#FDEBD0', edgecolor=CU, lw=0.8, zorder=2))
    ax.text(-D/2-6 + (ancho_total+D/2+12)/2, cuf_y,
            f'Colector underflow — DN {r["uf_dn"]}',
            ha='center', va='center', fontsize=6, color=CU)

    # 4 ciclones
    for i in range(n_b):
        cx_i = i * sep
        y0=0

        # Tubo bajante desde manifold
        ax.plot([cx_i, cx_i], [man_y, y0-Lv],
                color=CI, lw=1.2, zorder=3)

        # Vórtex finder
        ax.add_patch(plt.Rectangle((cx_i-r['Do']/2, y0-Lv), r['Do'], Lv,
            facecolor=CVF, edgecolor=CI, lw=0.7, ls='--', zorder=3, alpha=0.7))
        # Cilindro
        ax.add_patch(plt.Rectangle((cx_i-D/2, y0), D, Lcy,
            facecolor=CF, edgecolor=CW, lw=1.2, zorder=2))
        # Cono
        cone_pts = [[cx_i-D/2,y0+Lcy],[cx_i+D/2,y0+Lcy],
                    [cx_i+r['Du']/2,y0+Lcy+Lco],[cx_i-r['Du']/2,y0+Lcy+Lco]]
        ax.add_patch(plt.Polygon(cone_pts,
            facecolor='#C8DCF0', edgecolor=CW, lw=1.2, zorder=2))
        # Spigot
        ax.add_patch(plt.Rectangle((cx_i-r['Du']/2, y0+Lcy+Lco), r['Du'], La,
            facecolor='#BCD4E8', edgecolor=CW, lw=1.2, zorder=2))
        # Número de ciclón
        ax.text(cx_i, y0+Lcy/2, f'#{i+1}',
                ha='center', va='center', fontsize=7,
                color=CW, fontweight='bold')
        # Entrada tangencial (indicada con flecha)
        ax.annotate('', xy=(cx_i-D/2-1, y0+Lcy*0.35),
            xytext=(cx_i-D/2-r['Ent_od']*2, y0+Lcy*0.35),
            arrowprops=dict(arrowstyle='->', color=CI, lw=1.2), zorder=4)

    # Cotas del banco
    y_cota_sup = man_y - man_R - 12
    _cota_h(ax, y_cota_sup, 0, (n_b-1)*sep, f'Paso entre ciclones = {sep:.0f} mm', CC)
    _cota_h(ax, y_cota_sup-10, -D/2, (n_b-1)*sep+D/2,
            f'Ancho total banco 1 = {ancho_total:.0f} mm', CW, above=False)
    _cota_v(ax, (n_b-1)*sep+D/2+16, 0, Lcy+Lco+La,
            f'H ciclón = {L:.0f} mm', CW)

    # Título
    ax.text(ancho_total/2-D/2, cuf_y+28,
            f'BANCO 1 — {n_b}× Hy38/1100 — Vista Frontal de Elevación',
            ha='center', va='bottom', fontsize=9, fontweight='bold', color=CW)
    ax.text(ancho_total/2-D/2, cuf_y+20,
            f'Q banco 1 = {r["pot_banco"][1]["Q_Lh"]:.0f} L/h  |  SAE 304  |  Tri-Clamp  |  Jun 2026',
            ha='center', va='bottom', fontsize=7, color='#555')

    ax.invert_yaxis()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-D/2-30, (n_b-1)*sep+D/2+100)
    ax.set_ylim(Lcy+Lco+La+45, man_y-man_R-28)
    fig.tight_layout(pad=0.4)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑAS DE VISTAS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📐 Vistas técnicas del hidrociclón — ISO 128")
tabs = st.tabs([
    "📏 Corte A-A (Longitudinal)",
    "🔭 Corte B-B (Superior)",
    "🔍 Detalle entrada tangencial",
    "🧊 Vista isométrica",
    "🏭 Banco completo",
])

bufs = {}
figs_funcs = [
    ('longitudinal', fig_longitudinal),
    ('superior',     fig_superior),
    ('entrada',      fig_entrada_tangencial),
    ('isometrica',   fig_isometrica),
    ('banco',        fig_banco_completo),
]
nombres_png = [
    "HK-001-Longitudinal.png",
    "HK-002-Superior.png",
    "HK-003-Entrada.png",
    "HK-004-Isometrica.png",
    "HK-Banco1-Vista-Frontal.png",
]

for tab, (key, func), nombre in zip(tabs, figs_funcs, nombres_png):
    with tab:
        fig_ = func(r)
        buf_ = fig_to_bytes(fig_, dpi=200)
        bufs[key] = buf_
        st.image(buf_, use_container_width=True)
        st.download_button(f"⬇ PNG — {nombre}", buf_.getvalue(),
                           nombre, "image/png", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABLA DE COTAS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📋 Tabla de cotas — Diámetros comerciales Tri-Clamp SS304")

tabla_cotas = [
    {"Símbolo":"D",   "Parámetro":"Diámetro principal cuerpo",      "Calc.(mm)":f"{r['D']:.1f}",   "DN Tri-Clamp":"Mecanizado",             "OD férula":"—",                     "ID útil":"—",                    "Tolerancia":"±0.10","Estado":"✅"},
    {"Símbolo":"Do",  "Parámetro":"Diámetro overflow (vórtex)",      "Calc.(mm)":f"{r['Do']:.1f}",  "DN Tri-Clamp":f'{r["Do_dn"]}',          "OD férula":f'{r["Do_od"]:.1f} mm',  "ID útil":f'{r["Do_id"]:.1f} mm',"Tolerancia":"±0.05","Estado":"✅"},
    {"Símbolo":"Du",  "Parámetro":"Diámetro underflow (spigot)",     "Calc.(mm)":f"{r['Du']:.1f}",  "DN Tri-Clamp":f'{r["Du_dn"]}',          "OD férula":f'{r["Du_od"]:.1f} mm',  "ID útil":f'{r["Du_id"]:.1f} mm',"Tolerancia":"±0.05","Estado":"✅"},
    {"Símbolo":"Ø_e", "Parámetro":"Diámetro entrada tangencial",     "Calc.(mm)":f"{r['Sa']:.1f}",  "DN Tri-Clamp":f'{r["Ent_dn"]}',         "OD férula":f'{r["Ent_od"]:.1f} mm', "ID útil":f'{r["Ent_id"]:.1f} mm',"Tolerancia":"±0.05","Estado":"✅"},
    {"Símbolo":"Lcy", "Parámetro":"Longitud cilíndrica",             "Calc.(mm)":f"{r['Lcy']:.1f}", "DN Tri-Clamp":"—",                      "OD férula":"—",                     "ID útil":"—",                    "Tolerancia":"±0.50","Estado":"✅"},
    {"Símbolo":"Lco", "Parámetro":"Longitud cónica",                 "Calc.(mm)":f"{r['Lco']:.1f}", "DN Tri-Clamp":"—",                      "OD férula":"—",                     "ID útil":"—",                    "Tolerancia":"±0.50","Estado":"✅"},
    {"Símbolo":"La",  "Parámetro":"Longitud spigot (apex)",          "Calc.(mm)":f"{r['La']:.1f}",  "DN Tri-Clamp":"—",                      "OD férula":"—",                     "ID útil":"—",                    "Tolerancia":"±0.20","Estado":"✅"},
    {"Símbolo":"L",   "Parámetro":"Longitud total",                  "Calc.(mm)":f"{r['L']:.1f}",   "DN Tri-Clamp":"—",                      "OD férula":"—",                     "ID útil":"—",                    "Tolerancia":"±0.50","Estado":"✅"},
    {"Símbolo":"Lv",  "Parámetro":"Longitud vórtex finder",          "Calc.(mm)":f"{r['Lv']:.1f}",  "DN Tri-Clamp":"—",                      "OD férula":"—",                     "ID útil":"—",                    "Tolerancia":"±0.30","Estado":"✅"},
    {"Símbolo":"α",   "Parámetro":"Ángulo semi-cónico",              "Calc.(mm)":f"{r['alpha']}°",  "DN Tri-Clamp":"—",                      "OD férula":"—",                     "ID útil":"—",                    "Tolerancia":"±0.5°","Estado":"✅" if 10<=r['alpha']<=15 else "⚠️"},
]
df_cotas = pd.DataFrame(tabla_cotas)
st.dataframe(df_cotas, use_container_width=True, hide_index=True, height=420)
csv_c = df_cotas.to_csv(index=False, encoding='utf-8-sig')
st.download_button("⬇ Descargar tabla CSV", csv_c,
                   "cotas_hidrociclon_kion.csv", "text/csv",
                   use_container_width=True)
st.markdown("<hr style='margin:12px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CURVA EFICIENCIA + BANCOS
# ─────────────────────────────────────────────────────────────────────────────
col_e, col_b = st.columns(2)
with col_e:
    st.markdown("#### 📈 Curva G(x)")
    x_um,G_pct,Gp_pct = curva_eficiencia(r['x50_um']*1e-6, r['Rf'])
    fig_eff = go.Figure()
    fig_eff.add_trace(go.Scatter(x=x_um,y=G_pct,fill='tozeroy',
        fillcolor='rgba(43,108,176,.1)',line=dict(color='#2B6CB0',width=2),
        name='G(x)',hovertemplate='x=%{x:.1f}µm G=%{y:.1f}%<extra></extra>'))
    fig_eff.add_trace(go.Scatter(x=x_um,y=Gp_pct,
        line=dict(color='#38A169',width=1.5,dash='dash'),name="G'(x)"))
    fig_eff.add_vline(x=r['x50_um'],line=dict(color='#C53030',width=1.5,dash='dot'),
        annotation_text=f"x'₅₀={r['x50_um']:.1f}µm",
        annotation=dict(font=dict(color='#C53030',size=10)))
    fig_eff.add_vline(x=20,line=dict(color='#D97706',width=1.2,dash='longdash'),
        annotation_text='D₅₀ kion',annotation=dict(font=dict(color='#D97706',size=10)))
    fig_eff.update_layout(
        xaxis=dict(title='x (µm)',type='log',range=[0,np.log10(120)],gridcolor='#EDF2F7'),
        yaxis=dict(title='G(x) (%)',range=[0,102],gridcolor='#EDF2F7'),
        plot_bgcolor='white',paper_bgcolor='white',
        legend=dict(orientation='h',y=1.02,font=dict(size=9)),
        margin=dict(l=50,r=20,t=20,b=50),height=300)
    st.plotly_chart(fig_eff, use_container_width=True)

with col_b:
    st.markdown("#### 🏭 Distribución de potencia por banco")
    Q_v=[r['pot_banco'][b]['Q_Lh'] for b in BANCOS]
    P_r=[r['pot_banco'][b]['P_kW'] for b in BANCOS]
    P_n=[HP_BOMBAS[b]*HP_TO_KW for b in BANCOS]
    labs=[f"Banco {b} ({BANCOS[b]}×Hy38)" for b in BANCOS]
    fig_bk=go.Figure()
    fig_bk.add_trace(go.Bar(name='Q (L/h)',x=labs,y=Q_v,
        marker_color=['#2B6CB0','#276749','#C05621'],
        text=[f"{q:.0f}" for q in Q_v],textposition='outside',yaxis='y1'))
    fig_bk.add_trace(go.Bar(name='P req. (kW)',x=labs,y=P_r,
        marker_color=[('#276749' if r['pot_banco'][b]['P_HP']<=HP_BOMBAS[b] else '#C53030') for b in BANCOS],
        text=[f"{p:.2f}" for p in P_r],textposition='outside',yaxis='y2'))
    fig_bk.add_trace(go.Scatter(name='P nominal (kW)',x=labs,y=P_n,
        mode='markers+lines',marker=dict(symbol='diamond',size=8,color='#D97706'),
        line=dict(color='#D97706',width=1.5,dash='dot'),yaxis='y2'))
    fig_bk.update_layout(barmode='group',plot_bgcolor='white',paper_bgcolor='white',
        yaxis=dict(title='Q (L/h)',gridcolor='#EDF2F7',
                   title_font=dict(color='#2B6CB0'),tickfont=dict(color='#2B6CB0')),
        yaxis2=dict(title='P (kW)',overlaying='y',side='right',
                    title_font=dict(color='#C05621'),tickfont=dict(color='#C05621')),
        legend=dict(orientation='h',y=1.02,font=dict(size=9)),
        margin=dict(l=50,r=50,t=20,b=40),height=300)
    st.plotly_chart(fig_bk, use_container_width=True)

st.markdown("<hr style='margin:12px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIONES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("#### ✅ Verificaciones operativas")
chks=[
    ("Vel. entrada ≤ 8 m/s",         f"{r['v']:.2f} m/s",
     "🟢 OK" if r['v']<=6 else ("🟡" if r['v']<=8 else "🔴")),
    ("ΔP ≤ 700 kPa (Pentax)",        f"{r['dP_kPa']:.1f} kPa",
     "🟢 OK" if r['dP_kPa']<=400 else ("🟡" if r['dP_kPa']<=700 else "🔴")),
    ("Vel. tubería ≤ 3 m/s (SS304)", f"{r['vr_feed']:.2f} m/s",
     "🟢 OK" if r['vr_feed']<=3 else "🔴"),
    ("T proceso ≪ 80°C (gel.)",      f"{r['T_proc']}°C",
     "🟢 OK" if r['T_proc']<50 else "🟡"),
    ("Conc. feed 150–250 g/L",       f"{r['c_gL_input']} g/L",
     "🟢 OK" if 150<=r['c_gL_input']<=250 else "🟡"),
    ("Rf < 40%",                     f"{r['Rf']*100:.1f}%",
     "🟢 OK" if r['Rf']<0.25 else ("🟡" if r['Rf']<0.40 else "🔴")),
]
df_chk=pd.DataFrame(chks,columns=["Verificación","Valor","Estado"])
st.dataframe(df_chk,use_container_width=True,hide_index=True,height=250)
st.markdown("<hr style='margin:12px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GENERACIÓN DXF
# ─────────────────────────────────────────────────────────────────────────────
def generar_dxf(r):
    doc = ezdxf.new('R2010')
    doc.header['$INSUNITS'] = 4  # mm
    msp = doc.modelspace()
    CAPAS = {
        'CONTORNO':(7,50), 'EJES':(1,18), 'COTAS':(2,18),
        'OCULTO':(3,18),   'FERULAS':(4,35),'FLUJO':(5,25),
        'TEXTO':(7,18),    'CARTUCHO':(7,35),
    }
    for nombre,(color,lw) in CAPAS.items():
        lay=doc.layers.new(nombre)
        lay.color=color
        lay.lineweight=lw

    D=r['D']; Do=r['Do']; Du=r['Du']; Lcy=r['Lcy']; Lco=r['Lco']
    La=r['La']; Lv=r['Lv']; ep=2.0; cx=0; y0=0

    def pline(pts, layer, closed=False):
        p=msp.add_lwpolyline(pts,dxfattribs={'layer':layer})
        if closed: p.close()

    def line(p1,p2,layer):
        msp.add_line(p1,p2,dxfattribs={'layer':layer})

    def txt(pos,texto,h,layer,align='LEFT'):
        msp.add_text(texto,dxfattribs={'layer':layer,'height':h,'insert':pos})

    def ferula_dxf(cx,y,od,alto=4,grosor=5):
        for sg in [-1,1]:
            xb=cx+sg*(od/2)
            xd=-sg
            pline([(xb+xd*grosor,y-alto/2),(xb,y-alto/2),
                   (xb,y+alto/2),(xb+xd*grosor,y+alto/2),
                   (xb+xd*grosor,y-alto/2)],'FERULAS',closed=False)

    # ── Eje de simetría ──
    line((cx,y0-Lv-25),(cx,y0+Lcy+Lco+La+25),'EJES')

    # ── Vórtex finder ──
    pline([(-Do/2,y0-Lv),(-Do/2,y0),(Do/2,y0),(Do/2,y0-Lv),(-Do/2,y0-Lv)],'OCULTO')
    ferula_dxf(cx, y0, r['Do_od'], alto=4, grosor=5)

    # ── Cilindro ──
    pline([(-D/2,y0),(D/2,y0),(D/2,y0+Lcy),(-D/2,y0+Lcy),(-D/2,y0)],'CONTORNO',True)
    # Tapa (con hueco VF)
    line((-D/2,y0),(-Do/2,y0),'CONTORNO')
    line((Do/2,y0),(D/2,y0),'CONTORNO')
    # Paredes interiores (oculto)
    line((-D/2+ep,y0),(-D/2+ep,y0+Lcy),'OCULTO')
    line((D/2-ep,y0),(D/2-ep,y0+Lcy),'OCULTO')
    ferula_dxf(cx, y0+Lcy, D+4, alto=5, grosor=6)

    # ── Entrada tangencial ──
    er=r['Ent_od']/2; ei=r['Ent_id']/2
    ent_y=y0+Lcy*0.35; ent_x0=-D/2-er*5
    line((ent_x0,-ent_y+er),(-D/2,-ent_y+er),'CONTORNO')
    line((ent_x0,-ent_y-er),(-D/2,-ent_y-er),'CONTORNO')
    line((ent_x0,-ent_y+ei),(-D/2,-ent_y+ei),'OCULTO')
    line((ent_x0,-ent_y-ei),(-D/2,-ent_y-ei),'OCULTO')
    ferula_dxf(ent_x0, -ent_y, r['Ent_od'], alto=4, grosor=5)

    # ── Cono ──
    pline([(-D/2,y0+Lcy),(D/2,y0+Lcy),(Du/2,y0+Lcy+Lco),
           (-Du/2,y0+Lcy+Lco),(-D/2,y0+Lcy)],'CONTORNO')
    ferula_dxf(cx, y0+Lcy+Lco, Du+8, alto=4, grosor=5)

    # ── Spigot ──
    pline([(-Du/2,y0+Lcy+Lco),(Du/2,y0+Lcy+Lco),(Du/2,y0+Lcy+Lco+La),
           (-Du/2,y0+Lcy+Lco+La),(-Du/2,y0+Lcy+Lco)],'CONTORNO')
    ferula_dxf(cx, y0+Lcy+Lco+La, r['Du_od']+4, alto=4, grosor=5)

    # ── Flechas flujo (líneas) ──
    line((cx,-(y0-Lv-2)),(cx,-(y0-Lv-18)),'FLUJO')
    line((cx,y0+Lcy+Lco+La+2),(cx,y0+Lcy+Lco+La+18),'FLUJO')

    # ── Cotas como entidades DIMENSION ──
    try:
        dimstyle = doc.dimstyles.new('ISO25')
        dimstyle.dxf.dimtxt = 2.5
        dimstyle.dxf.dimasz = 2.0
        dimstyle.dxf.dimdec = 1
    except Exception:
        dimstyle_name = 'EZDXF'
    else:
        dimstyle_name = 'ISO25'

    xd1=D/2+14; xd2=D/2+26; xd3=D/2+50

    def dim_h(p1x,p2x,y_dim,texto=''):
        try:
            d=msp.add_linear_dim(base=(0,y_dim),p1=(p1x,y_dim-5),p2=(p2x,y_dim-5),
                dimstyle=dimstyle_name,override={'dimtxt':2.5,'dimdec':1})
            d.render()
        except Exception: pass

    def dim_v(x_dim,y1,y2,texto=''):
        try:
            d=msp.add_linear_dim(base=(x_dim,0),p1=(x_dim-5,y1),p2=(x_dim-5,y2),
                angle=90,dimstyle=dimstyle_name,override={'dimtxt':2.5,'dimdec':1})
            d.render()
        except Exception: pass

    dim_h(-D/2, D/2, -(y0-Lv-12))
    dim_h(-Do/2, Do/2, -(y0-Lv-20))
    dim_h(-Du/2, Du/2, y0+Lcy+Lco+La+8)
    dim_v(xd1, -(y0-Lv), 0)
    dim_v(xd2, 0, y0+Lcy)
    dim_v(xd2, y0+Lcy, y0+Lcy+Lco)
    dim_v(xd1, y0+Lcy+Lco, y0+Lcy+Lco+La)
    dim_v(xd3, 0, y0+Lcy+Lco+La)

    # ── Textos ──
    txt((-D/2-3, -(y0-Lv)/2-2),
        f'DN {r["Do_dn"]} - Do={r["Do"]:.1f}mm', 2.2, 'TEXTO')
    txt((-Du/2-3, y0+Lcy+Lco+La+12),
        f'DN {r["Du_dn"]} - Du={r["Du"]:.1f}mm', 2.2, 'TEXTO')
    txt((ent_x0-5, -ent_y+er+4),
        f'DN {r["Ent_dn"]} - Entrada', 2.2, 'TEXTO')

    # ── Cartucho ISO ──
    bx=xd3+15; by_c=y0+Lcy+Lco
    pline([(bx,by_c-35),(bx+86,by_c-35),(bx+86,by_c+2),(bx,by_c+2),(bx,by_c-35)],
          'CARTUCHO')
    for dy in [19,11]:
        line((bx,by_c-dy),(bx+86,by_c-dy),'CARTUCHO')
    txt((bx+2,by_c-3),  'UNION DE NEGOCIOS CORPORATIVOS',3.0,'TEXTO')
    txt((bx+2,by_c-13), f'Hidrociclon Kion - Corte A-A | D={r["D"]:.1f}mm',2.5,'TEXTO')
    txt((bx+2,by_c-22), f'HK-001-R0 | Esc. 1:1 (mm) | SAE 304 | Tri-Clamp',2.0,'TEXTO')
    txt((bx+2,by_c-30), f'Ing. F. Becerra | Jun 2026 | Rev.0',2.0,'TEXTO')

    # Serializar a StringIO → BytesIO
    sbuf = io.StringIO()
    doc.write(sbuf)
    return io.BytesIO(sbuf.getvalue().encode('utf-8'))

# ─────────────────────────────────────────────────────────────────────────────
# GENERACIÓN PDF
# ─────────────────────────────────────────────────────────────────────────────
def gen_pdf_taller(r, figs_bytes):
    buf_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buf_pdf, pagesize=landscape(A3),
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    azul = rlcolors.HexColor('#1B3A6B')
    T  = ParagraphStyle('T',  parent=styles['Title'],   fontSize=16,textColor=azul,alignment=TA_CENTER)
    H  = ParagraphStyle('H',  parent=styles['Heading2'],fontSize=12,textColor=azul)
    N  = ParagraphStyle('N',  parent=styles['Normal'],  fontSize=8, leading=12)
    P2 = ParagraphStyle('P2', parent=styles['Normal'],  fontSize=7, leading=10)
    story = []

    # Carátula
    story += [Spacer(1,25*mm),
              Paragraph("UNIÓN DE NEGOCIOS CORPORATIVOS", T),
              Paragraph("Planta de Procesamiento de Jengibre (Kion) — Perú", H),
              HRFlowable(width='100%',thickness=2,color=azul,spaceAfter=8)]
    story.append(Paragraph("PLANOS TÉCNICOS DE FABRICACIÓN — Hidrociclón Hy38/1100", H))

    meta_data = [
        ["Responsable","Ing. Froilán Becerra — Jefe de Mantenimiento"],
        ["Material","Acero Inoxidable SAE 304 — Conexiones Tri-Clamp Sanitario"],
        ["Modelo","Hy38/1100 — Bradford (Castilho & Medronho, 2000)"],
        ["DN Overflow",f'{r["Do_dn"]} — OD={r["Do_od"]:.1f}mm ID={r["Do_id"]:.1f}mm'],
        ["DN Underflow",f'{r["Du_dn"]} — OD={r["Du_od"]:.1f}mm ID={r["Du_id"]:.1f}mm'],
        ["DN Entrada",f'{r["Ent_dn"]} — OD={r["Ent_od"]:.1f}mm ID={r["Ent_id"]:.1f}mm'],
        ["Capacidad",f'{r["Q_total_lh"]} L/h — {r["n_total_inst"]} ciclones'],
        ["Fecha","Junio 2026 — Rev.0"],
    ]
    t_meta = Table(meta_data, colWidths=[50*mm,120*mm])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),azul),('TEXTCOLOR',(0,0),(-1,0),rlcolors.white),
        ('BACKGROUND',(0,0),(0,-1),rlcolors.HexColor('#EBF5FB')),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),8),
        ('GRID',(0,0),(-1,-1),0.4,rlcolors.HexColor('#CBD5E0')),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5),
    ]))
    story += [Spacer(1,6*mm), t_meta, PageBreak()]

    # Planos
    plano_info = [
        ('HK-001-R0 — Corte A-A (Vista Longitudinal)', 'longitudinal'),
        ('HK-002-R0 — Vista Superior (Planta B-B)',    'superior'),
        ('HK-003-R0 — Detalle Entrada Tangencial',     'entrada'),
        ('HK-004-R0 — Vista Isométrica',               'isometrica'),
    ]
    for titulo, key in plano_info:
        story.append(Paragraph(titulo, H))
        story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
        img_buf = figs_bytes[key]
        img_buf.seek(0)
        story.append(RLImage(img_buf, width=240*mm, height=165*mm))
        story.append(PageBreak())

    # Tabla de cotas
    story.append(Paragraph("Tabla de cotas — Diámetros comerciales Tri-Clamp SS304", H))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    enc = ["Símbolo","Parámetro","Calculado (mm)","DN Tri-Clamp","OD férula","ID útil","Tolerancia","Estado"]
    dat = [[d["Símbolo"],d["Parámetro"],d["Calc.(mm)"],d["DN Tri-Clamp"],
            d["OD férula"],d["ID útil"],d["Tolerancia"],d["Estado"]]
           for d in tabla_cotas]
    t_cotas = Table([enc]+dat, colWidths=[16*mm,62*mm,26*mm,26*mm,22*mm,22*mm,22*mm,16*mm])
    t_cotas.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),azul),('TEXTCOLOR',(0,0),(-1,0),rlcolors.white),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),7.5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[rlcolors.HexColor('#F0F4F8'),rlcolors.white]),
        ('GRID',(0,0),(-1,-1),0.4,rlcolors.HexColor('#CBD5E0')),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
    ]))
    story.append(t_cotas)

    doc.build(story)
    buf_pdf.seek(0)
    return buf_pdf

# ─────────────────────────────────────────────────────────────────────────────
# BOTONES DE EXPORTACIÓN
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📄 Exportar documentos")
col_d, col_p1, col_p2 = st.columns(3)

with col_d:
    st.markdown("""**📐 Archivo DXF — AutoCAD**
    Plano técnico con capas ISO (CONTORNO, EJES, COTAS, FERULAS…)
    Compatible con AutoCAD 2010 o superior""")
    if st.button("⬇ Generar DXF (AutoCAD)", key="btn_dxf"):
        with st.spinner("Generando DXF…"):
            try:
                dxf_buf = generar_dxf(r)
                st.download_button("📥 Descargar HK-001-Hidrociclon.dxf",
                    dxf_buf.getvalue(),
                    "HK-001-Hidrociclon-Kion.dxf",
                    "application/dxf",
                    use_container_width=True)
            except Exception as e:
                st.error(f"Error DXF: {e}")

with col_p1:
    st.markdown("""**🔧 PDF Taller — A3 horizontal**
    Planos de fabricación con diámetros comerciales
    y notas técnicas SS304""")
    if st.button("⬇ Generar PDF Taller (A3)", key="btn_pdf_taller"):
        with st.spinner("Generando PDF taller…"):
            try:
                figs_b = {}
                for key, func in figs_funcs[:4]:
                    f=func(r); figs_b[key]=fig_to_bytes(f,300)
                pdf_buf = gen_pdf_taller(r, figs_b)
                st.download_button("📥 Descargar PDF Taller",
                    pdf_buf.getvalue(),
                    "HK-Taller-Hidrociclon-Kion.pdf",
                    "application/pdf",
                    use_container_width=True)
            except Exception as e:
                st.error(f"Error PDF: {e}")

with col_p2:
    st.markdown("""**📋 Resumen rápido — verificaciones**
    Exporta la tabla de cotas y verificaciones
    en formato CSV""")
    if st.button("⬇ Exportar CSV completo", key="btn_csv"):
        df_exp = pd.concat([
            df_cotas,
            pd.DataFrame([{"Símbolo":"—","Parámetro":"—","Calc.(mm)":"—",
                           "DN Tri-Clamp":"—","OD férula":"—","ID útil":"—",
                           "Tolerancia":"—","Estado":"—"}]),
            df_chk.rename(columns={"Verificación":"Símbolo","Valor":"Calc.(mm)",
                                    "Estado":"Estado"})
        ], ignore_index=True)
        st.download_button("📥 Descargar CSV",
            df_exp.to_csv(index=False,encoding='utf-8-sig'),
            "HK-Especificaciones-Completas.csv","text/csv",
            use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# NOTAS DE FABRICACIÓN
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("📋 Notas de fabricación — SAE 304 Sanitario"):
    n1,n2,n3=st.columns(3)
    with n1:
        st.markdown("""**🔧 Tolerancias críticas**
| Zona | Tolerancia |
|------|-----------|
| Diámetro D | ±0.10 mm |
| Do (overflow) | ±0.05 mm |
| Du (spigot) | ±0.05 mm |
| Ángulo α | ±0.5° |
| Longitud Lv | ±0.30 mm |
| Concentricidad VF | TIR ≤ 0.05 mm |
| Asiento férulas | ±0.05 mm |""")
    with n2:
        st.markdown(f"""**⚗️ Conexiones Tri-Clamp SS304**
- Overflow: DN {r['Do_dn']} — OD {r['Do_od']:.1f}mm
- Underflow: DN {r['Du_dn']} — OD {r['Du_od']:.1f}mm
- Entrada: DN {r['Ent_dn']} — OD {r['Ent_od']:.1f}mm
- Juntas: PTFE o EPDM FDA-grado
- Clamps: DIN 32676 clase A
- Prueba hidrostática: 1.5×P_trabajo""")
    with n3:
        st.markdown("""**🛠️ CIP/SIP**
1. Enjuague agua fría, 3 min
2. NaOH 1.5%, 70°C, 15 min
3. Enjuague DI, 5 min
4. Ácido peracético 0.2%, 10 min
5. Enjuague final ≤10 µS/cm
- Spigot: revisar desgaste mensual
- O-rings: cambio c/6 meses""")

# FOOTER
st.markdown("<hr style='margin:14px 0 8px 0'>", unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center;font-size:.76rem;color:#718096;padding:4px 0 10px">
    <b>UNIÓN DE NEGOCIOS CORPORATIVOS — Perú</b> · Sistema Hidrociclónico · Almidón de Kion ·
    Modelo Bradford (Castilho & Medronho, 2000) · DN comerciales Tri-Clamp SS304 ·
    Ing. Froilán Becerra · <b>v3.0 — Junio 2026</b>
</div>""", unsafe_allow_html=True)

# requirements.txt
# streamlit>=1.32.0
# numpy>=1.24.0
# matplotlib>=3.7.0
# plotly>=5.18.0
# pandas>=2.0.0
# scipy>=1.10.0
# reportlab>=4.0.0
# ezdxf>=1.0.0
