# =============================================================================
# app.py v2.0 — Sistema Hidrociclónico — Separación de Almidón de Kion
# UNIÓN DE NEGOCIOS CORPORATIVOS — Ing. Froilán Becerra, Jefe de Mantenimiento
# Modelo Bradford (Castilho & Medronho, 2000) — 4 vistas técnicas — PDF taller/informe
# Deploy: Streamlit Community Cloud
# =============================================================================

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc
import plotly.graph_objects as go
import pandas as pd
from scipy.optimize import brentq
import io, math

from reportlab.lib.pagesizes import A3, A4, landscape, portrait
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Image as RLImage, Table, TableStyle, PageBreak,
                                 HRFlowable, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rlcolors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Hidrociclón Kion — UNC",
                   page_icon="⚙️", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp,[data-testid="block-container"]{background-color:#F0F4F8!important}
    .main{background-color:#F0F4F8!important}
    [data-testid="stSidebar"]{background-color:#E2E8F0!important}
    [data-testid="stSidebar"]>div:first-child{background-color:#E2E8F0!important}
    /* Cards blancos */
    [data-testid="stVerticalBlock"]>[data-testid="stVerticalBlock"]{
        background:#FFFFFF;border-radius:10px;padding:4px}
    h1{color:#1B3A6B;font-family:Arial,sans-serif;font-size:1.45rem}
    h2,h3{color:#2D5A8E;font-family:Arial,sans-serif}
    .stButton>button{background-color:#1B3A6B!important;color:white!important;
        font-weight:bold!important;border-radius:8px!important;
        padding:.55rem 2rem!important;font-size:.95rem!important;
        border:none!important;width:100%!important}
    .stButton>button:hover{background-color:#2D5A8E!important}
    .btn-verde>button{background-color:#276749!important}
    [data-testid="stMetric"]{background:#FFFFFF;border:1.5px solid #E2E8F0;
        border-radius:10px;padding:10px 14px;
        box-shadow:0 2px 5px rgba(0,0,0,.06)}
    [data-testid="stMetricLabel"]{color:#4A5568!important;font-size:.78rem!important}
    [data-testid="stMetricValue"]{color:#1B3A6B!important;font-size:1.3rem!important;font-weight:600!important}
    .stTabs [data-baseweb="tab"]{font-weight:600;color:#2D5A8E}
    .stTabs [aria-selected="true"]{border-bottom:3px solid #1B3A6B!important}
    .seccion{font-size:.72rem;font-weight:700;letter-spacing:1.5px;
        text-transform:uppercase;color:#718096;margin-bottom:4px;
        border-left:3px solid #2D5A8E;padding-left:8px}
    hr{border-color:#CBD5E0}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
RHO_S = 1517.0
T_GEL = 80.0
HP_TO_KW = 0.74570
ETA_BOMBA = 0.65
BANCOS = {1:4, 2:3, 3:2}
HP_BOMBAS = {1:3, 2:3, 3:2}

TOLERANCIAS = {
    'D':'±0.10','Do':'±0.05','Du':'±0.05','Lcy':'±0.50',
    'Lco':'±0.50','La':'±0.20','L':'±0.50','Lv':'±0.30',
    'Sa':'±0.10','Sb':'±0.10','alpha':'±0.5°',
}

# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
c0,c1 = st.columns([1,9])
with c0:
    st.markdown("""<div style="width:58px;height:58px;background:linear-gradient(135deg,#1B3A6B,#2D5A8E);
    border-radius:12px;display:flex;align-items:center;justify-content:center;
    font-size:28px;margin-top:4px">⚙️</div>""", unsafe_allow_html=True)
with c1:
    st.markdown("""<div style="margin-top:2px">
    <div style="font-size:.7rem;font-weight:700;letter-spacing:2px;
         text-transform:uppercase;color:#718096">UNIÓN DE NEGOCIOS CORPORATIVOS — PERÚ</div>
    <h1 style="margin:2px 0 0 0">Sistema Hidrociclónico · Separación de Almidón de Jengibre (Kion)</h1>
    <div style="font-size:.82rem;color:#4A5568;margin-top:2px">
        Modelo Hy38/1100 (1½") · SAE 304 · Tri-Clamp ·
        Ing. Froilán Becerra — Jefe de Mantenimiento · 2026
    </div></div>""", unsafe_allow_html=True)
st.markdown("<hr style='margin:10px 0 16px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
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
    st.markdown('<div class="seccion">Geometría del hidrociclón</div>', unsafe_allow_html=True)
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

# ─────────────────────────────────────────────
# MODELO BRADFORD
# ─────────────────────────────────────────────
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
    Lv_mm  = 0.10  * L_mm;  Sa_mm  = math.sqrt(0.05 * D_mm**2);  Sb_mm = Sa_mm
    x_d50  = 20e-6
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
    dn = lambda d: max(10, int(math.ceil(d/5))*5)
    DN_f = dn(d_feed); DN_o = dn(d_OF); DN_u = dn(d_UF)
    vr_f = Q_tot/(math.pi/4*(DN_f/1000)**2)
    vr_o = Q_tot*(1-Rf)/(math.pi/4*(DN_o/1000)**2)
    vr_u = Q_tot*Rf/(math.pi/4*(DN_u/1000)**2)
    return {
        "Re":Re,"Eu":Eu,"Stk":Stk,"Rf":Rf,"c_gg":c_gg,"v":v,
        "dP_kPa":dP_calc_kPa,"Q_cicl_Lh":Q_cicl_Lh,"Q_cicl_Lmin":Q_cicl_Lh/60,
        "x50_um":x50_m*1e6,"eff_d50":G_d50*100,
        "D":D_mm,"Do":Do_mm,"Du":Du_mm,"Lcy":Lcy_mm,"Lco":Lco_mm,
        "La":La_mm,"L":L_mm,"Lv":Lv_mm,"Sa":Sa_mm,"Sb":Sb_mm,"alpha":alpha_deg,
        "Do_D":Do_D,"Du_D":Du_D,"n_cicl_calc":n_cicl_calc,
        "pot_banco":pot_banco,"Q_total_lh":Q_total_lh,
        "DN_feed":DN_f,"DN_OF":DN_o,"DN_UF":DN_u,
        "d_feed_mm":d_feed,"d_OF_mm":d_OF,"d_UF_mm":d_UF,
        "vr_feed":vr_f,"vr_OF":vr_o,"vr_UF":vr_u,
        "T_proc":T_proc,"c_gL_input":c_gL,"rho_f_input":rho_f,"mu_input":mu_mPas,
        "n_total_inst":n_total_inst,
    }

def curva_eficiencia(x50_m, Rf, n=200):
    x_um = np.linspace(1, 120, n)
    x_m  = x_um * 1e-6
    Gp   = 1.0 / (1.0 + (x50_m / x_m)**2.5)
    G    = Rf + (1.0 - Rf) * Gp
    return x_um, G*100, Gp*100

# ─────────────────────────────────────────────
# CÁLCULO
# ─────────────────────────────────────────────
if "r" not in st.session_state:
    st.session_state["r"] = None

if calcular:
    with st.spinner("⚙️ Calculando diseño…"):
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
    st.markdown("""
    ### Sistema de referencia
    **Hy38/1100** · D=38.1mm · 3 bancos (4+3+2 ciclones) · Pentax 3+3+2 HP · SAE 304

    ### Modelo de cálculo
    Bradford (Castilho & Medronho, 2000) — Ec. 4, 5, 6 con iteración numérica `scipy.brentq`
    """)
    st.stop()

# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────
st.markdown("### 📊 Resultados del modelo Bradford")
cols = st.columns(10)
kpis = [
    ("D principal",      f"{r['D']:.1f} mm",        None),
    ("ΔP hidrociclón",   f"{r['dP_kPa']:.1f} kPa",  f"{'🟢 OK' if r['dP_kPa']<=400 else '🟡 Alto' if r['dP_kPa']<=600 else '🔴 Excede'}"),
    ("x'₅₀ corte",       f"{r['x50_um']:.1f} µm",   None),
    ("Rf underflow",     f"{r['Rf']*100:.1f} %",     None),
    ("Vel. entrada",     f"{r['v']:.2f} m/s",        f"{'🟢 OK' if r['v']<=6 else '🟡' if r['v']<=8 else '🔴'}"),
    ("Q/ciclón",         f"{r['Q_cicl_Lh']:.1f} L/h",None),
    ("N° cicl. calc.",   f"{r['n_cicl_calc']:.1f}",  f"Inst: {r['n_total_inst']}"),
    ("Re",               f"{r['Re']:.0f}",           None),
    ("Eu",               f"{r['Eu']:.1f}",           None),
    ("Efic. D50=20µm",   f"{r['eff_d50']:.1f} %",   None),
]
for col, (lbl, val, dlt) in zip(cols, kpis):
    with col: st.metric(lbl, val, dlt)

st.markdown("<hr style='margin:8px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FUNCIONES DE DIBUJO
# ─────────────────────────────────────────────
C_WALL='#1B3A6B'; C_FLUID='#D6EAF8'; C_VF='#AED6F1'
C_IN='#2471A3'; C_OV='#1E8449'; C_UF='#A04000'; C_COTA='#444444'
FS=7.0; FI='italic'

def _cota_v(ax, xc, y1, y2, sym, color=C_COTA):
    ax.plot([xc-2,xc+2],[y1,y1],color=color,lw=0.5,ls=':')
    ax.plot([xc-2,xc+2],[y2,y2],color=color,lw=0.5,ls=':')
    ax.annotate('',xy=(xc,y2),xytext=(xc,y1),
        arrowprops=dict(arrowstyle='<->',color=color,lw=0.7,mutation_scale=5))
    ax.text(xc+2.5,(y1+y2)/2,sym,ha='left',va='center',
            fontsize=FS,color=color,style=FI,fontweight='bold')

def _cota_h(ax, yc, x1, x2, sym, color=C_COTA, above=True):
    ax.plot([x1,x1],[yc-1.5,yc+1.5],color=color,lw=0.5,ls=':')
    ax.plot([x2,x2],[yc-1.5,yc+1.5],color=color,lw=0.5,ls=':')
    ax.annotate('',xy=(x2,yc),xytext=(x1,yc),
        arrowprops=dict(arrowstyle='<->',color=color,lw=0.7,mutation_scale=5))
    off=3.5 if above else -3.5
    ax.text((x1+x2)/2,yc+off,sym,ha='center',
            va='bottom' if above else 'top',
            fontsize=FS,color=color,style=FI,fontweight='bold')

def _bloque_titulo(ax, x, y, vista, plano, escala="1:1"):
    ax.add_patch(plt.Rectangle((x,y-34),78,36,facecolor='white',
        edgecolor='#333',lw=0.7, zorder=10))
    for dy in [18,10]: ax.plot([x,x+78],[y-dy,y-dy],color='#333',lw=0.4)
    ax.text(x+39,y-2,'UNIÓN DE NEGOCIOS CORPORATIVOS',ha='center',
            fontsize=5.5,fontweight='bold',color='#1B3A6B',zorder=11)
    ax.text(x+39,y-12,f'Hidrociclón Kion — {vista}',ha='center',
            fontsize=5,color='#333',zorder=11)
    ax.text(x+39,y-21,f'{plano} | Esc. {escala} (mm)',ha='center',
            fontsize=4.5,color='#555',zorder=11)
    ax.text(x+39,y-29,'Ing. F. Becerra | Jun 2026 | Rev.0',ha='center',
            fontsize=4.5,color='#555',zorder=11)

# ─── VISTA 1: LONGITUDINAL ───────────────────
def fig_longitudinal(r):
    D=r['D']; Do=r['Do']; Du=r['Du']; Lcy=r['Lcy']; Lco=r['Lco']
    La=r['La']; L=r['L']; Lv=r['Lv']; Sa=r['Sa']; Sb=r['Sb']; alpha=r['alpha']
    fig, ax = plt.subplots(figsize=(9,11), facecolor='white')
    ax.set_facecolor('white')
    y0=0.0; cx=0.0

    # Relleno del cuerpo
    ax.add_patch(plt.Rectangle((cx-D/2,y0),D,Lcy,
        facecolor=C_FLUID,edgecolor=C_WALL,lw=1.2,zorder=2))
    ax.add_patch(plt.Polygon([
        [cx-D/2,y0+Lcy],[cx+D/2,y0+Lcy],
        [cx+Du/2,y0+Lcy+Lco],[cx-Du/2,y0+Lcy+Lco]],
        facecolor=C_FLUID,edgecolor=C_WALL,lw=1.2,zorder=2))
    ax.add_patch(plt.Rectangle((cx-Du/2,y0+Lcy+Lco),Du,La,
        facecolor=C_FLUID,edgecolor=C_WALL,lw=1.2,zorder=2))
    # Tapa
    ax.plot([cx-D/2,cx-Do/2],[y0,y0],color=C_WALL,lw=1.2,zorder=3)
    ax.plot([cx+Do/2,cx+D/2],[y0,y0],color=C_WALL,lw=1.2,zorder=3)
    # Vortex finder
    ax.add_patch(plt.Rectangle((cx-Do/2,y0-Lv),Do,Lv+2,
        facecolor=C_VF,edgecolor=C_IN,lw=0.9,linestyle='--',zorder=3,alpha=0.85))
    # Eje central
    ax.axvline(cx,color='#BBBBBB',lw=0.5,ls='-.',zorder=1)
    # Entrada tangencial
    ent_y = y0+Lcy*0.30
    ax.add_patch(plt.Rectangle((cx-D/2-Sa*2.3,ent_y-Sb/2),Sa*2.3,Sb,
        facecolor='#D6EAF8',edgecolor=C_IN,lw=0.9,zorder=2))
    ax.annotate('',xy=(cx-D/2-1,ent_y),xytext=(cx-D/2-Sa*2.3+3,ent_y),
        arrowprops=dict(arrowstyle='->',color=C_IN,lw=1.4),zorder=4)
    ax.text(cx-D/2-Sa*2.3-2,ent_y,'Entrada\ntangencial',
            ha='right',va='center',fontsize=6,color=C_IN)
    # Flechas flujo
    ax.annotate('',xy=(cx,y0-Lv-14),xytext=(cx,y0-Lv-1),
        arrowprops=dict(arrowstyle='->',color=C_OV,lw=2),zorder=4)
    ax.text(cx+2,y0-Lv-16,'Overflow',ha='left',va='top',fontsize=6,color=C_OV)
    ax.annotate('',xy=(cx,y0+Lcy+Lco+La+14),xytext=(cx,y0+Lcy+Lco+La+1),
        arrowprops=dict(arrowstyle='->',color=C_UF,lw=2),zorder=4)
    ax.text(cx+2,y0+Lcy+Lco+La+16,'Underflow',ha='left',va='bottom',fontsize=6,color=C_UF)

    # COTAS verticales escalonadas (lado derecho)
    xd = [D/2+12, D/2+24, D/2+36, D/2+48]
    _cota_v(ax,xd[0], y0-Lv,        y0,               'Lv')
    _cota_v(ax,xd[1], y0,            y0+Lcy,           'Lcy')
    _cota_v(ax,xd[1], y0+Lcy,        y0+Lcy+Lco,       'Lco')
    _cota_v(ax,xd[0], y0+Lcy+Lco,    y0+Lcy+Lco+La,    'La')
    _cota_v(ax,xd[3], y0,            y0+Lcy+Lco+La,    'L', '#1B3A6B')

    # COTAS horizontales (superiores e inferiores)
    _cota_h(ax, y0-Lv-10, cx-D/2,  cx+D/2,  'D',  '#1B3A6B', above=False)
    _cota_h(ax, y0-Lv-19, cx-Do/2, cx+Do/2, 'Do', C_IN,      above=False)
    _cota_h(ax, y0+Lcy+Lco+La+5, cx-Du/2, cx+Du/2, 'Du', C_UF, above=True)
    # Sa en la entrada
    _cota_h(ax, ent_y+Sb/2+4, cx-D/2-Sa*2.3, cx-D/2, 'Sa', C_IN, above=True)
    # Sb (vertical izquierdo)
    _cota_v(ax, cx-D/2-Sa*2.3-10, ent_y-Sb/2, ent_y+Sb/2, 'Sb', C_IN)

    # Ángulo alfa
    ax.text(cx-D/4-2,y0+Lcy+Lco*0.4,'α',ha='right',va='center',
            fontsize=FS+1,color='#8B0000',style=FI,fontweight='bold')

    # Escala gráfica
    sbx = cx-D/2; sby = y0+Lcy+Lco+La+35
    ax.plot([sbx,sbx+20],[sby,sby],color='#333',lw=1.5)
    ax.plot([sbx,sbx],[sby-1,sby+1],color='#333',lw=1.5)
    ax.plot([sbx+20,sbx+20],[sby-1,sby+1],color='#333',lw=1.5)
    ax.text(sbx+10,sby+2,'20 mm',ha='center',va='bottom',fontsize=6,color='#333')

    # Marcas de corte A-A
    ax.text(cx-D/2-Sa*2.3-18,y0+Lcy*0.5,'A',fontsize=8,color='#CC0000',fontweight='bold')
    ax.text(cx+D/2+xd[3]+12, y0+Lcy*0.5,'A',fontsize=8,color='#CC0000',fontweight='bold')
    ax.plot([cx-D/2-Sa*2.3-16,cx+D/2+xd[3]+10],[y0+Lcy*0.5,y0+Lcy*0.5],
            color='#CC0000',lw=0.6,ls=(0,(8,2,2,2)))

    # Bloque título
    _bloque_titulo(ax, cx+D/2+xd[3]+16, y0+Lcy+Lco, 'Corte A-A (Vista Longitudinal)', 'HK-001-R0')

    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(cx-D/2-Sa*2.3-25, cx+D/2+xd[3]+100)
    ax.set_ylim(y0-Lv-30, y0+Lcy+Lco+La+55)
    fig.tight_layout(pad=0.5)
    return fig

# ─── VISTA 2: SUPERIOR ───────────────────────
def fig_superior(r):
    D=r['D']; Do=r['Do']; Sa=r['Sa']; Sb=r['Sb']
    fig, ax = plt.subplots(figsize=(8,7), facecolor='white')
    ax.set_facecolor('white'); cx=cy=0.0
    ax.add_patch(plt.Circle((cx,cy),D/2,facecolor=C_FLUID,edgecolor=C_WALL,lw=1.2,zorder=2))
    ax.add_patch(plt.Circle((cx,cy),Do/2,facecolor=C_VF,edgecolor=C_IN,lw=0.9,ls='--',zorder=3))
    # Líneas de centro
    ax.plot([cx-D/2-5,cx+D/2+5],[cy,cy],color='#BBBBBB',lw=0.5,ls='-.',zorder=1)
    ax.plot([cx,cx],[cy-D/2-5,cy+D/2+5],color='#BBBBBB',lw=0.5,ls='-.',zorder=1)
    # Entrada tangencial
    ent_x = cx-D/2-Sa*2.2
    ax.add_patch(plt.Rectangle((ent_x,cy-Sb/2),Sa*2.2,Sb,
        facecolor='#D6EAF8',edgecolor=C_IN,lw=0.9,zorder=2))
    ax.annotate('',xy=(cx-D/2-1,cy),xytext=(ent_x+3,cy),
        arrowprops=dict(arrowstyle='->',color=C_IN,lw=1.4),zorder=4)
    ax.text(ent_x-2,cy,'Entrada\ntangencial',ha='right',va='center',fontsize=6,color=C_IN)
    # Línea de corte A-A
    ax.plot([-D/2-6,D/2+6],[D/2+7,D/2+7],color='#CC0000',lw=0.8,ls=(0,(8,2,2,2)))
    ax.text(D/2+8,D/2+7,'A',ha='left',va='center',fontsize=7,color='#CC0000',fontweight='bold')
    ax.text(-D/2-10,D/2+7,'A',ha='right',va='center',fontsize=7,color='#CC0000',fontweight='bold')
    # Cotas
    _cota_h(ax,-D/2-9,-D/2,D/2,'D','#1B3A6B',above=False)
    _cota_h(ax,-Do/2-5,-Do/2,Do/2,'Do',C_IN,above=False)
    _cota_h(ax,cy+Sb/2+4,ent_x,cx-D/2,'Sa',C_IN,above=True)
    _cota_v(ax,ent_x-8,cy-Sb/2,cy+Sb/2,'Sb',C_IN)
    # Bloque título
    _bloque_titulo(ax,D/2+14,D/2+12,'Corte B-B (Vista Superior — Planta)','HK-002-R0')
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-D/2-Sa*2.2-20,D/2+100); ax.set_ylim(-D/2-30,D/2+28)
    fig.tight_layout(pad=0.5)
    return fig

# ─── VISTA 3: ENTRADA TANGENCIAL ─────────────
def fig_entrada_tangencial(r):
    D=r['D']; Sa=r['Sa']; Sb=r['Sb']; v=r['v']
    sc=3.0; Dsc=D*sc/2; Sasc=Sa*sc; Sbsc=Sb*sc; ep=2.0*sc
    fig, ax = plt.subplots(figsize=(8,7), facecolor='white')
    ax.set_facecolor('white'); cx=cy=0.0
    theta = np.linspace(100,260,80)
    xarc  = cx+Dsc*np.cos(np.radians(theta))
    yarc  = cy+Dsc*np.sin(np.radians(theta))
    xarc2 = cx+(Dsc+ep)*np.cos(np.radians(theta))
    yarc2 = cy+(Dsc+ep)*np.sin(np.radians(theta))
    ax.fill(np.concatenate([xarc,xarc2[::-1]]),
            np.concatenate([yarc,yarc2[::-1]]),
            facecolor='#B0C4DE',edgecolor=C_WALL,lw=0.8,zorder=2)
    ax.plot(xarc,yarc,color=C_WALL,lw=1.3,zorder=3)
    ax.fill_between(xarc,cy-Dsc,yarc,facecolor=C_FLUID,alpha=0.35,zorder=1)
    ent_xr=cx-Dsc-ep; ent_xl=ent_xr-Sasc*2.3
    ent_yt=cy+Sbsc/2; ent_yb=cy-Sbsc/2
    ax.fill([ent_xl,ent_xr,ent_xr,ent_xl],[ent_yt,ent_yt,ent_yt+ep,ent_yt+ep],
        facecolor='#B0C4DE',edgecolor=C_WALL,lw=0.8,zorder=2)
    ax.fill([ent_xl,ent_xr,ent_xr,ent_xl],[ent_yb-ep,ent_yb-ep,ent_yb,ent_yb],
        facecolor='#B0C4DE',edgecolor=C_WALL,lw=0.8,zorder=2)
    ax.fill([ent_xl,ent_xr,ent_xr,ent_xl],[ent_yb,ent_yb,ent_yt,ent_yt],
        facecolor=C_FLUID,alpha=0.7,zorder=1)
    ax.plot([ent_xl,ent_xl],[ent_yb-ep,ent_yt+ep],color=C_WALL,lw=1.2)
    for f in [0.25,0.5,0.75]:
        fy=ent_yb+(ent_yt-ent_yb)*f
        ax.annotate('',xy=(ent_xr-3,fy),xytext=(ent_xl+Sasc*0.35,fy),
            arrowprops=dict(arrowstyle='->',color=C_IN,lw=1.2),zorder=5)
    r_u=ep*1.5
    ax.add_patch(Arc((ent_xr,ent_yt+r_u),r_u*2,r_u*2,angle=0,theta1=270,theta2=360,color='#E74C3C',lw=0.8,linestyle='--'))
    ax.add_patch(Arc((ent_xr,ent_yb-r_u),r_u*2,r_u*2,angle=0,theta1=0,  theta2=90, color='#E74C3C',lw=0.8,linestyle='--'))
    _cota_h(ax,ent_yt+ep+5,ent_xl,ent_xr,'Sa',C_IN,above=True)
    _cota_v(ax,ent_xl-8,ent_yb,ent_yt,'Sb',C_IN)
    _cota_v(ax,ent_xl-16,ent_yb-ep,ent_yb,'e','#8B0000')
    _cota_h(ax,ent_yb-ep-8,cx-Dsc,cx+Dsc,'D/2 (ref.)','#1B3A6B',above=False)
    ax.text(cx+Dsc+5,cy+Dsc+2,'Notas técnicas:',fontsize=7,fontweight='bold',color='#333')
    notas=[f'• Ra ≤ 0.4 µm (interior canal)',
           f'• Soldadura TIG ER308L, back purge Ar',
           f'• v entrada = {v:.2f} m/s',
           f'• Sa × Sb = {Sa:.1f} × {Sb:.1f} mm',
           f'• Borde entrada: R ≤ 0.2 mm',
           f'• e pared estimado = 2.0 mm (SS304)']
    for i,n in enumerate(notas):
        ax.text(cx+Dsc+5,cy+Dsc-6-i*7,n,fontsize=6.5,color='#444')
    _bloque_titulo(ax,cx+Dsc+5,cy-Dsc+8,'Detalle Entrada Tangencial (Esc. ~3:1)','HK-003-R0','~3:1')
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(ent_xl-25,cx+Dsc+95); ax.set_ylim(cy-Dsc-25,cy+Dsc+22)
    fig.tight_layout(pad=0.5)
    return fig

# ─── VISTA 4: ISOMÉTRICA ─────────────────────
def fig_isometrica(r):
    D=r['D']; Do=r['Do']; Du=r['Du']
    Lcy=r['Lcy']; Lco=r['Lco']; La=r['La']; Lv=r['Lv']; Sa=r['Sa']
    fig, ax = plt.subplots(figsize=(9,10), facecolor='white')
    ax.set_facecolor('white')
    ang=math.radians(30)
    def iso(x,y,z):
        return (x-y)*math.cos(ang), (x+y)*math.sin(ang)+z
    def elipse(ax,cx,cy,cz,rx,ry,fill,edge,lw=1.0,ls='-',alpha=1.0,zo=2):
        t=np.linspace(0,2*math.pi,80)
        pts=[iso(cx+rx*np.cos(a),cy+ry*np.sin(a),cz) for a in t]
        ax.fill([p[0] for p in pts],[p[1] for p in pts],
                facecolor=fill,edgecolor=edge,lw=lw,ls=ls,alpha=alpha,zorder=zo)
    def linea(ax,p1,p2,color,lw=1.0,ls='-',zo=2):
        x1,y1=iso(*p1); x2,y2=iso(*p2)
        ax.plot([x1,x2],[y1,y2],color=color,lw=lw,ls=ls,zorder=zo)
    def cara_lateral(ax,R_top,R_bot,z_top,z_bot,fill,edge,lw=1.0,zo=3):
        t=np.linspace(-math.pi/2,math.pi/2,40)
        pts_t=[iso(R_top*np.cos(a),R_top*np.sin(a),z_top) for a in t]
        pts_b=[iso(R_bot*np.cos(a),R_bot*np.sin(a),z_bot) for a in t]
        xi=[p[0] for p in pts_t]+[p[0] for p in pts_b[::-1]]
        yi=[p[1] for p in pts_t]+[p[1] for p in pts_b[::-1]]
        ax.fill(xi,yi,facecolor=fill,edgecolor=edge,lw=lw,zorder=zo)

    R=D/2; Ro=Do/2; Ru=Du/2; z0=0
    # Tapa superior
    elipse(ax,0,0,z0,R,R*0.35,'#C8D8EA',C_WALL,1.2,zo=5)
    elipse(ax,0,0,z0,Ro,Ro*0.35,'white',C_WALL,0.8,zo=6)
    # Cilindro
    cara_lateral(ax,R,R,z0,z0+Lcy,C_FLUID,C_WALL,1.0)
    elipse(ax,0,0,z0+Lcy,R,R*0.35,'#B8CCE0',C_WALL,0.7,alpha=0.8,zo=4)
    # Vortex finder
    t2=np.linspace(-math.pi/2,math.pi/2,20)
    pts_vf_t=[iso(Ro*np.cos(a),Ro*np.sin(a),z0-Lv) for a in t2]
    pts_vf_b=[iso(Ro*np.cos(a),Ro*np.sin(a),z0)    for a in t2]
    xi_vf=[p[0] for p in pts_vf_t]+[p[0] for p in pts_vf_b[::-1]]
    yi_vf=[p[1] for p in pts_vf_t]+[p[1] for p in pts_vf_b[::-1]]
    ax.fill(xi_vf,yi_vf,facecolor=C_VF,edgecolor=C_IN,lw=0.8,ls='--',alpha=0.9,zorder=7)
    elipse(ax,0,0,z0-Lv,Ro,Ro*0.35,C_VF,C_IN,0.8,zo=8)
    # Cono
    cara_lateral(ax,R,Ru,z0+Lcy,z0+Lcy+Lco,'#C0D5E8',C_WALL,1.0)
    elipse(ax,0,0,z0+Lcy+Lco,Ru,Ru*0.35,'#B0C4D8',C_WALL,0.7,alpha=0.8,zo=4)
    # Spigot
    zs=z0+Lcy+Lco
    cara_lateral(ax,Ru,Ru,zs,zs+La,'#B8CCE0',C_WALL,1.0)
    elipse(ax,0,0,zs+La,Ru,Ru*0.35,'#A8BCE8',C_WALL,0.8,zo=4)
    # Entrada tangencial
    ez=z0+Lcy*0.30
    for dz in [0,Sa]:
        linea(ax,(-R-Sa*2,-Sa/2,ez+dz),(-R,-Sa/2,ez+dz),C_IN,0.8)
        linea(ax,(-R-Sa*2, Sa/2,ez+dz),(-R, Sa/2,ez+dz),C_IN,0.8)
    linea(ax,(-R-Sa*2,-Sa/2,ez),(-R-Sa*2,-Sa/2,ez+Sa),C_IN,0.8)
    linea(ax,(-R,     -Sa/2,ez),(-R,     -Sa/2,ez+Sa),C_IN,0.8)
    linea(ax,(-R-Sa*2, Sa/2,ez),(-R-Sa*2, Sa/2,ez+Sa),C_IN,0.8)
    linea(ax,(-R,      Sa/2,ez),(-R,      Sa/2,ez+Sa),C_IN,0.8)
    # Flechas
    xov,yov=iso(0,0,z0-Lv-10)
    ax.annotate('',xy=(xov,yov+10),xytext=(xov,yov),
        arrowprops=dict(arrowstyle='->',color=C_OV,lw=1.5),zorder=9)
    ax.text(xov+2,yov+12,'Overflow',fontsize=6.5,color=C_OV)
    xuf,yuf=iso(0,0,zs+La+5)
    ax.annotate('',xy=(xuf,yuf-9),xytext=(xuf,yuf),
        arrowprops=dict(arrowstyle='->',color=C_UF,lw=1.5),zorder=9)
    ax.text(xuf+2,yuf-12,'Underflow',fontsize=6.5,color=C_UF)
    xin,yin=iso(-R-Sa*4.5,0,ez+Sa/2)
    ax.annotate('',xy=iso(-R-Sa*2+2,0,ez+Sa/2),xytext=(xin,yin),
        arrowprops=dict(arrowstyle='->',color=C_IN,lw=1.5),zorder=9)
    ax.text(xin-1,yin,'Entrada',fontsize=6.5,color=C_IN,ha='right')
    # Etiquetas con líneas de referencia
    def etiq(ax,px,py,pz,txt,color,dx=8,dy=8):
        x0,y0=iso(px,py,pz)
        ax.annotate(txt,xy=(x0,y0),xytext=(x0+dx,y0+dy),
            fontsize=7,color=color,style='italic',fontweight='bold',
            arrowprops=dict(arrowstyle='-',color=color,lw=0.6))
    etiq(ax, R+2,0,z0+Lcy*0.5,'D', '#1B3A6B', 10, 0)
    etiq(ax, Ro+2,0,z0-Lv/2, 'Do',C_IN, 10, 0)
    etiq(ax, Ru+2,0,zs+La/2, 'Du',C_UF, 10, 0)
    etiq(ax, R+14,0,(z0+zs+La)/2,'L','#333333',12,0)
    etiq(ax, R+2,0,z0+Lcy+Lco/2,'Lco','#555',10,6)
    # Bloque título
    xbt,ybt=iso(R+20,-R-10,z0+Lcy)
    ax.text(xbt,ybt+14,'UNIÓN DE NEGOCIOS CORPORATIVOS',
            fontsize=5.5,fontweight='bold',color='#1B3A6B')
    ax.text(xbt,ybt+8,'Vista Isométrica — Hidrociclón Kion',fontsize=5,color='#333')
    ax.text(xbt,ybt+2,'HK-004-R0 | Jun 2026 | Rev.0',fontsize=4.5,color='#555')
    ax.text(xbt,ybt-3,'Ing. F. Becerra | Sin escala (referencia)',fontsize=4.5,color='#555')

    ax.set_aspect('equal'); ax.axis('off')
    all_pts = [iso(x,y,z) for x,y,z in [
        (-R-Sa*5,-Sa,ez),(R+35,0,z0-Lv-15),(R+35,0,zs+La+15)]]
    xs=[p[0] for p in all_pts]; ys=[p[1] for p in all_pts]
    ax.set_xlim(min(xs)-20, max(xs)+70)
    ax.set_ylim(min(ys)-20, max(ys)+30)
    fig.tight_layout(pad=0.5)
    return fig

def fig_to_bytes(fig, dpi=180):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    return buf

# ─────────────────────────────────────────────
# SECCIÓN PRINCIPAL: 4 PESTAÑAS DE VISTAS
# ─────────────────────────────────────────────
st.markdown("### 📐 Vistas técnicas del hidrociclón")
tab1, tab2, tab3, tab4 = st.tabs([
    "📏 Vista longitudinal (Corte A-A)",
    "🔭 Vista superior (Planta B-B)",
    "🔍 Detalle entrada tangencial",
    "🧊 Vista isométrica",
])

figs_cache = {}
with tab1:
    fig1 = fig_longitudinal(r)
    figs_cache['longitudinal'] = fig1
    buf1 = fig_to_bytes(fig1)
    st.image(buf1, use_container_width=True)
    st.download_button("⬇ Descargar PNG — Vista longitudinal",
                       buf1.getvalue(),"longitudinal_A-A.png","image/png",
                       use_container_width=True)
    plt.close(fig1)

with tab2:
    fig2 = fig_superior(r)
    figs_cache['superior'] = fig2
    buf2 = fig_to_bytes(fig2)
    st.image(buf2, use_container_width=True)
    st.download_button("⬇ Descargar PNG — Vista superior",
                       buf2.getvalue(),"superior_B-B.png","image/png",
                       use_container_width=True)
    plt.close(fig2)

with tab3:
    fig3 = fig_entrada_tangencial(r)
    figs_cache['entrada'] = fig3
    buf3 = fig_to_bytes(fig3)
    st.image(buf3, use_container_width=True)
    st.download_button("⬇ Descargar PNG — Detalle entrada",
                       buf3.getvalue(),"detalle_entrada.png","image/png",
                       use_container_width=True)
    plt.close(fig3)

with tab4:
    fig4 = fig_isometrica(r)
    figs_cache['isometrica'] = fig4
    buf4 = fig_to_bytes(fig4)
    st.image(buf4, use_container_width=True)
    st.download_button("⬇ Descargar PNG — Vista isométrica",
                       buf4.getvalue(),"isometrica.png","image/png",
                       use_container_width=True)
    plt.close(fig4)

# ─────────────────────────────────────────────
# TABLA DE COTAS UNIFICADA
# ─────────────────────────────────────────────
st.markdown("### 📋 Tabla de cotas — Planos HK-001 a HK-004")

RANGOS = {
    'D':   (25,80),  'Do':  (0,999), 'Du': (0,999),
    'Lcy': (0,999),  'Lco': (0,999), 'La': (8,15),
    'L':   (0,999),  'Lv':  (0,999), 'Sa': (0,999),
    'Sb':  (0,999),  'alpha':(10,15),
}

def estado(sym, val):
    lo,hi = RANGOS.get(sym,(0,9999))
    v = val if sym!='alpha' else val
    return "🟢 OK" if lo<=v<=hi else ("🟡 Revisar" if abs(v-lo)<lo*0.25 or lo==0 else "🔴 Fuera rango")

tabla_cotas = [
    {"Símbolo plano":"D",  "Nomenclatura técnica":"Diámetro principal",        "Valor (mm)":f"{r['D']:.1f}",   "Relación geométrica":"Nominal / Bradford",    "Tolerancia":"±0.10 mm","Estado":estado('D',r['D'])},
    {"Símbolo plano":"Do", "Nomenclatura técnica":"Diámetro overflow (vórtex)","Valor (mm)":f"{r['Do']:.1f}",  "Relación geométrica":f"{r['Do_D']:.2f} × D",  "Tolerancia":"±0.05 mm","Estado":estado('Do',r['Do'])},
    {"Símbolo plano":"Du", "Nomenclatura técnica":"Diámetro underflow (spigot)","Valor (mm)":f"{r['Du']:.1f}", "Relación geométrica":f"{r['Du_D']:.2f} × D",  "Tolerancia":"±0.05 mm","Estado":estado('Du',r['Du'])},
    {"Símbolo plano":"Lcy","Nomenclatura técnica":"Longitud cilíndrica",        "Valor (mm)":f"{r['Lcy']:.1f}","Relación geométrica":"2.00 × D",              "Tolerancia":"±0.50 mm","Estado":estado('Lcy',r['Lcy'])},
    {"Símbolo plano":"Lco","Nomenclatura técnica":"Longitud cónica",            "Valor (mm)":f"{r['Lco']:.1f}","Relación geométrica":"(D−Du) / (2·tan α)",   "Tolerancia":"±0.50 mm","Estado":estado('Lco',r['Lco'])},
    {"Símbolo plano":"La", "Nomenclatura técnica":"Longitud spigot (apex)",     "Valor (mm)":f"{r['La']:.1f}", "Relación geométrica":"Fija = 10.0 mm",        "Tolerancia":"±0.20 mm","Estado":estado('La',r['La'])},
    {"Símbolo plano":"L",  "Nomenclatura técnica":"Longitud total",             "Valor (mm)":f"{r['L']:.1f}",  "Relación geométrica":"Lcy + Lco + La",        "Tolerancia":"±0.50 mm","Estado":estado('L',r['L'])},
    {"Símbolo plano":"Lv", "Nomenclatura técnica":"Longitud vórtex finder",     "Valor (mm)":f"{r['Lv']:.1f}", "Relación geométrica":"0.10 × L",              "Tolerancia":"±0.30 mm","Estado":estado('Lv',r['Lv'])},
    {"Símbolo plano":"Sa", "Nomenclatura técnica":"Entrada tangencial — ancho", "Valor (mm)":f"{r['Sa']:.1f}", "Relación geométrica":"√(0.05 × D²)",          "Tolerancia":"±0.10 mm","Estado":estado('Sa',r['Sa'])},
    {"Símbolo plano":"Sb", "Nomenclatura técnica":"Entrada tangencial — alto",  "Valor (mm)":f"{r['Sb']:.1f}", "Relación geométrica":"= Sa",                  "Tolerancia":"±0.10 mm","Estado":estado('Sb',r['Sb'])},
    {"Símbolo plano":"α",  "Nomenclatura técnica":"Ángulo semi-cónico",         "Valor (mm)":f"{r['alpha']}°", "Relación geométrica":"Definido por usuario",  "Tolerancia":"±0.5°",  "Estado":estado('alpha',r['alpha'])},
]
df_cotas = pd.DataFrame(tabla_cotas)
st.dataframe(df_cotas, use_container_width=True, hide_index=True, height=440,
             column_config={
                 "Símbolo plano":       st.column_config.TextColumn(width="small"),
                 "Nomenclatura técnica":st.column_config.TextColumn(width="large"),
                 "Valor (mm)":          st.column_config.TextColumn(width="small"),
                 "Relación geométrica": st.column_config.TextColumn(width="medium"),
                 "Tolerancia":          st.column_config.TextColumn(width="small"),
                 "Estado":              st.column_config.TextColumn(width="small"),
             })
csv_cotas = df_cotas.to_csv(index=False, encoding='utf-8-sig')
st.download_button("⬇ Descargar tabla CSV",csv_cotas,
                   "cotas_hidrociclon_kion.csv","text/csv",use_container_width=True)

st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CURVA EFICIENCIA + BANCOS
# ─────────────────────────────────────────────
col_eff, col_bk = st.columns(2)

with col_eff:
    st.markdown("#### 📈 Curva de eficiencia G(x)")
    x_um,G_pct,Gp_pct = curva_eficiencia(r['x50_um']*1e-6, r['Rf'])
    fig_eff = go.Figure()
    fig_eff.add_trace(go.Scatter(x=x_um,y=G_pct,fill='tozeroy',
        fillcolor='rgba(43,108,176,0.10)',line=dict(color='#2B6CB0',width=2.5),
        name='G(x) total',hovertemplate='x=%{x:.1f}µm<br>G=%{y:.1f}%<extra></extra>'))
    fig_eff.add_trace(go.Scatter(x=x_um,y=Gp_pct,
        line=dict(color='#38A169',width=1.8,dash='dash'),
        name="G'(x) reducida",hovertemplate='x=%{x:.1f}µm<br>G\'=%{y:.1f}%<extra></extra>'))
    fig_eff.add_vline(x=r['x50_um'],line=dict(color='#C53030',width=1.5,dash='dot'),
        annotation_text=f"x'₅₀={r['x50_um']:.1f}µm",
        annotation=dict(font=dict(color='#C53030',size=10)))
    fig_eff.add_vline(x=20,line=dict(color='#D97706',width=1.2,dash='longdash'),
        annotation_text='D₅₀ kion=20µm',
        annotation=dict(font=dict(color='#D97706',size=10)))
    fig_eff.update_layout(
        xaxis=dict(title='x (µm)',type='log',range=[0,np.log10(120)],
                   gridcolor='#EDF2F7'),
        yaxis=dict(title='G(x) (%)',range=[0,102],gridcolor='#EDF2F7'),
        plot_bgcolor='white',paper_bgcolor='white',
        legend=dict(orientation='h',y=1.02,font=dict(size=9)),
        margin=dict(l=50,r=20,t=30,b=50),height=320)
    st.plotly_chart(fig_eff, use_container_width=True)

with col_bk:
    st.markdown("#### 🏭 Sistema de 3 bancos")
    Q_vals=[r['pot_banco'][b]['Q_Lh'] for b in BANCOS]
    P_req =[r['pot_banco'][b]['P_kW'] for b in BANCOS]
    P_nom =[HP_BOMBAS[b]*HP_TO_KW for b in BANCOS]
    labs  =[f"Banco {b} ({BANCOS[b]}×Hy38)" for b in BANCOS]
    fig_bk2=go.Figure()
    fig_bk2.add_trace(go.Bar(name='Q banco (L/h)',x=labs,y=Q_vals,
        marker_color=['#2B6CB0','#276749','#C05621'],
        text=[f"{q:.0f}" for q in Q_vals],textposition='outside',yaxis='y1'))
    fig_bk2.add_trace(go.Bar(name='P requerida (kW)',x=labs,y=P_req,
        marker_color=[('#276749' if r['pot_banco'][b]['P_HP']<=HP_BOMBAS[b] else '#C53030') for b in BANCOS],
        text=[f"{p:.2f}" for p in P_req],textposition='outside',yaxis='y2'))
    fig_bk2.add_trace(go.Scatter(name='P nominal bomba (kW)',x=labs,y=P_nom,
        mode='markers+lines',marker=dict(symbol='diamond',size=9,color='#D97706'),
        line=dict(color='#D97706',width=1.5,dash='dot'),yaxis='y2'))
    fig_bk2.update_layout(barmode='group',plot_bgcolor='white',paper_bgcolor='white',
        yaxis=dict(title='Q (L/h)',gridcolor='#EDF2F7',
                   title_font=dict(color='#2B6CB0'),tickfont=dict(color='#2B6CB0')),
        yaxis2=dict(title='P (kW)',overlaying='y',side='right',
                    title_font=dict(color='#C05621'),tickfont=dict(color='#C05621')),
        legend=dict(orientation='h',y=1.02,font=dict(size=9)),
        margin=dict(l=50,r=50,t=30,b=40),height=320)
    st.plotly_chart(fig_bk2, use_container_width=True)

st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# VERIFICACIONES Y ESPECIFICACIONES
# ─────────────────────────────────────────────
col_v, col_s = st.columns(2)
with col_v:
    st.markdown("#### ✅ Verificaciones operativas")
    chks=[
        ("Vel. entrada ≤ 8 m/s", f"{r['v']:.2f} m/s",
         "🟢 OK" if r['v']<=6 else ("🟡 Acepta." if r['v']<=8 else "🔴 Excede")),
        ("ΔP ≤ 700 kPa (Pentax)", f"{r['dP_kPa']:.1f} kPa",
         "🟢 OK" if r['dP_kPa']<=400 else ("🟡 Acepta." if r['dP_kPa']<=700 else "🔴 Excede")),
        ("Vel. tubería ≤ 3 m/s (SS304)", f"{r['vr_feed']:.2f} m/s",
         "🟢 OK" if r['vr_feed']<=2.5 else ("🟡 Acepta." if r['vr_feed']<=3 else "🔴 Alta")),
        ("T proceso ≪ 80°C (gel.)", f"{r['T_proc']}°C",
         "🟢 OK" if r['T_proc']<50 else ("🟡 Monit." if r['T_proc']<65 else "🔴 Riesgo")),
        ("Concentración 150–250 g/L", f"{r['c_gL_input']} g/L",
         "🟢 OK" if 150<=r['c_gL_input']<=250 else "🟡 Revisar"),
        ("Rf < 40% (spigot libre)", f"{r['Rf']*100:.1f}%",
         "🟢 OK" if r['Rf']<0.25 else ("🟡 Acepta." if r['Rf']<0.40 else "🔴 Alto")),
    ]
    df_chk=pd.DataFrame(chks,columns=["Verificación","Valor","Estado"])
    st.dataframe(df_chk,use_container_width=True,hide_index=True,height=260)

with col_s:
    st.markdown("#### 🔢 Números adimensionales")
    df_adim=pd.DataFrame([
        {"Símbolo":"Re",     "Expresión":"ρf·v·D/μ",            "Valor":f"{r['Re']:.1f}"},
        {"Símbolo":"Eu",     "Expresión":"2·ΔP/(ρf·v²)",        "Valor":f"{r['Eu']:.2f}"},
        {"Símbolo":"Stk'₅₀","Expresión":"(ρs−ρf)·x²·v/18μD",   "Valor":f"{r['Stk']:.5f}"},
        {"Símbolo":"Rf",     "Expresión":"Qu/Q",                 "Valor":f"{r['Rf']:.4f}"},
        {"Símbolo":"c_gg",   "Expresión":"c [g/g]",              "Valor":f"{r['c_gg']:.4f}"},
    ])
    st.dataframe(df_adim,use_container_width=True,hide_index=True,height=220)
    b1c,b2c,b3c=st.columns(3)
    for bc,b in zip([b1c,b2c,b3c],[1,2,3]):
        pb=r['pot_banco'][b]; ok=pb['P_HP']<=pb['nom_HP']
        bc.markdown(f"""<div style="border:1.5px solid {'#C6F6D5' if ok else '#FEB2B2'};
            border-radius:8px;padding:8px;text-align:center;
            background:{'#F0FFF4' if ok else '#FFF5F5'}">
            <b>Banco {b}</b><br>
            <span style="font-size:.8rem;color:#4A5568">
            {BANCOS[b]} cicl. | {pb['Q_Lh']:.0f} L/h<br>
            {pb['P_kW']:.2f} kW / {pb['nom_HP']} HP<br>
            {'✅' if ok else '⚠️'}</span></div>""",
            unsafe_allow_html=True)

st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GENERADORES DE PDF
# ─────────────────────────────────────────────
def fig_para_rl(fig, dpi=180, w_mm=None, h_mm=None):
    """Convierte figura matplotlib a Image de ReportLab."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img = RLImage(buf)
    if w_mm: img.drawWidth  = w_mm*mm
    if h_mm: img.drawHeight = h_mm*mm
    return img

def plotly_para_rl(fig_go, w_mm=160, h_mm=100):
    """Convierte figura plotly a Image de ReportLab via kaleido si está disponible."""
    try:
        import kaleido
        buf = io.BytesIO(fig_go.to_image(format='png', width=1200, height=750, scale=2))
        img = RLImage(buf, width=w_mm*mm, height=h_mm*mm)
        return img
    except Exception:
        return None

def estilos_pdf():
    styles = getSampleStyleSheet()
    azul   = rlcolors.HexColor('#1B3A6B')
    gris   = rlcolors.HexColor('#4A5568')
    titulo = ParagraphStyle('titulo', parent=styles['Title'],
                fontSize=18, textColor=azul, spaceAfter=6, alignment=TA_CENTER)
    subtit = ParagraphStyle('subtit', parent=styles['Heading2'],
                fontSize=13, textColor=azul, spaceAfter=4)
    normal = ParagraphStyle('normal', parent=styles['Normal'],
                fontSize=9, textColor=gris, spaceAfter=4, leading=13)
    peq    = ParagraphStyle('peq', parent=styles['Normal'],
                fontSize=7.5, textColor=gris, leading=11)
    return titulo, subtit, normal, peq, azul, gris, styles

def tabla_rl(datos, encabezados, col_w=None):
    """Crea tabla ReportLab con estilo corporativo."""
    azul  = rlcolors.HexColor('#1B3A6B')
    gris1 = rlcolors.HexColor('#F0F4F8')
    gris2 = rlcolors.HexColor('#E2E8F0')
    filas = [encabezados] + datos
    t = Table(filas, colWidths=col_w)
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0),(-1,0),  azul),
        ('TEXTCOLOR',   (0,0),(-1,0),  rlcolors.white),
        ('FONTNAME',    (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0,0),(-1,0),  8),
        ('ALIGN',       (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',      (0,0),(-1,-1), 'MIDDLE'),
        ('FONTNAME',    (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,1),(-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[gris1, rlcolors.white]),
        ('GRID',        (0,0),(-1,-1), 0.4, gris2),
        ('TOPPADDING',  (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING', (0,0),(-1,-1), 5),
        ('RIGHTPADDING',(0,0),(-1,-1), 5),
    ]))
    return t

def caratula_rl(story, titulo_s, subtit_s, normal_s, peq_s, azul, tipo='taller'):
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("UNIÓN DE NEGOCIOS CORPORATIVOS", titulo_s))
    story.append(Paragraph("Planta de procesamiento de jengibre (Kion) — Perú", subtit_s))
    story.append(HRFlowable(width='100%', thickness=2, color=azul, spaceAfter=10))
    tit_doc = "PLANOS TÉCNICOS DE FABRICACIÓN" if tipo=='taller' else "INFORME TÉCNICO COMPLETO DE DISEÑO"
    story.append(Paragraph(tit_doc, subtit_s))
    story.append(Paragraph("Sistema Hidrociclónico Hy38/1100 — Separación de Almidón de Zingiber officinale", normal_s))
    story.append(Spacer(1, 10*mm))
    meta = [
        ["Responsable técnico:", "Ing. Froilán Becerra — Jefe de Mantenimiento"],
        ["Material:", "Acero Inoxidable SAE 304 — Conexiones Tri-Clamp Sanitario"],
        ["Modelo hidrociclón:", "Hy38/1100 (Diametro nominal 38.1 mm = 1.5 pulgadas)"],
        ["Configuración:", "3 bancos: Banco 1 (4 cicl.), Banco 2 (3 cicl.), Banco 3 (2 cicl.)"],
        ["Bombas:", "Pentax España — 3 HP / 3 HP / 2 HP"],
        ["Capacidad nominal:", f"{r['Q_total_lh']} L/h de jugo de jengibre"],
        ["Modelo de cálculo:", "Bradford — Castilho & Medronho, 2000 (Ec. 4, 5 y 6)"],
        ["Fecha:", "Junio 2026"],
        ["Revisión:", "Rev. 0 — Versión inicial"],
        ["Planos incluidos:",
         "HK-001-R0 (Longitudinal), HK-002-R0 (Superior), HK-003-R0 (Entrada tang.), HK-004-R0 (Isométrica)"],
    ]
    t_meta = tabla_rl(meta, ["Campo","Descripción"], [55*mm, 120*mm])
    story.append(t_meta)

def pdf_taller(r, buf1, buf2, buf3, buf4):
    """PDF A3 horizontal orientado a fabricación."""
    buf_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buf_pdf, pagesize=landscape(A3),
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    titulo_s, subtit_s, normal_s, peq_s, azul, gris, styles = estilos_pdf()
    story = []

    # Carátula
    caratula_rl(story, titulo_s, subtit_s, normal_s, peq_s, azul, 'taller')
    story.append(PageBreak())

    # Plano 1 — Longitudinal
    story.append(Paragraph("Plano HK-001-R0 — Corte A-A (Vista Longitudinal)", subtit_s))
    story.append(HRFlowable(width='100%', thickness=1, color=azul, spaceAfter=6))
    f1 = fig_longitudinal(r)
    story.append(fig_para_rl(f1, dpi=200, w_mm=340, h_mm=220))
    plt.close(f1)
    story.append(PageBreak())

    # Planos 2 y 3 en misma hoja
    story.append(Paragraph("Plano HK-002-R0 — Vista Superior (Planta)  /  HK-003-R0 — Detalle Entrada Tangencial", subtit_s))
    story.append(HRFlowable(width='100%', thickness=1, color=azul, spaceAfter=6))
    f2 = fig_superior(r); f3 = fig_entrada_tangencial(r)
    row_imgs = [[fig_para_rl(f2,200,w_mm=170,h_mm=160),
                 fig_para_rl(f3,200,w_mm=170,h_mm=160)]]
    plt.close(f2); plt.close(f3)
    t_imgs = Table(row_imgs, colWidths=[180*mm, 180*mm])
    t_imgs.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                                 ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(t_imgs)
    story.append(PageBreak())

    # Tabla de cotas
    story.append(Paragraph("Tabla de cotas — Dimensiones de fabricación", subtit_s))
    story.append(HRFlowable(width='100%', thickness=1, color=azul, spaceAfter=6))
    enc_c = ["Símbolo","Parámetro","Valor (mm)","Relación geométrica","Tolerancia","Estado"]
    dat_c = [[d["Símbolo plano"],d["Nomenclatura técnica"],d["Valor (mm)"],
              d["Relación geométrica"],d["Tolerancia"],d["Estado"]] for d in tabla_cotas]
    story.append(tabla_rl(dat_c, enc_c, [18*mm,70*mm,28*mm,70*mm,30*mm,28*mm]))
    story.append(Spacer(1, 8*mm))

    # Notas de fabricación resumidas
    story.append(Paragraph("Notas de fabricación", subtit_s))
    notas_fab = [
        "• Material: Acero inoxidable SAE 304 (EN 10204 tipo 3.1) — contacto alimentario",
        f"• Acabado interior zona cilíndrica: Ra ≤ 0.8 µm | Zona cónica y entrada: Ra ≤ 0.4 µm",
        "• Soldadura: GTAW (TIG) proceso ER308L, bajo carbono (<0.03% C), back purge argón 99.99%",
        "• Pasivado post-mecanizado: HNO₃ 20%, 30 min, enjuague con agua desionizada",
        "• Conexiones: Tri-Clamp DIN 32676 clase A — Juntas PTFE o EPDM FDA-grado",
        "• Prueba hidrostática: 1.5 × P_trabajo antes de puesta en marcha",
        "• Concentricidad vórtex finder: TIR ≤ 0.05 mm | Ángulo cónico: verificar con plantilla ±0.5°",
    ]
    for n in notas_fab:
        story.append(Paragraph(n, peq_s))

    doc.build(story)
    buf_pdf.seek(0)
    return buf_pdf

def pdf_informe(r, buf1, buf2, buf3, buf4):
    """PDF A4 vertical — informe técnico completo."""
    buf_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buf_pdf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    titulo_s, subtit_s, normal_s, peq_s, azul, gris, styles = estilos_pdf()
    story = []

    # Carátula
    caratula_rl(story, titulo_s, subtit_s, normal_s, peq_s, azul, 'informe')
    story.append(PageBreak())

    # 1. Parámetros de entrada
    story.append(Paragraph("1. Parámetros de entrada del cálculo", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    params_i = [
        ["Densidad jugo (ρ_f)",       f"{r['rho_f_input']} kg/m³",    "Jugo de rizoma fresco"],
        ["Viscosidad dinámica (μ)",   f"{r['mu_input']} mPa·s",        "Suspensión diluida a 20°C"],
        ["Concentración sólidos",     f"{r['c_gL_input']} g/L",        f"c_gg = {r['c_gg']:.4f} g/g"],
        ["Temperatura proceso",       f"{r['T_proc']} °C",             f"T_gel almidón = {T_GEL}°C"],
        ["Densidad almidón (ρ_s)",    f"{RHO_S} kg/m³",                "Reyes, 1982 — Zingiber officinale"],
        ["Diámetro principal (D)",    f"{r['D']:.1f} mm",              "Modelo Hy38/1100"],
        ["Relación Du/D",             f"{r['Du_D']:.2f}",              f"Du = {r['Du']:.1f} mm"],
        ["Relación Do/D",             f"{r['Do_D']:.2f}",              f"Do = {r['Do']:.1f} mm"],
        ["Ángulo cónico (α)",         f"{r['alpha']}°",                "Óptimo para partículas < 20 µm"],
        ["Caudal total sistema",      f"{r['Q_total_lh']} L/h",        f"{BANCOS} ciclones instalados"],
    ]
    story.append(tabla_rl(params_i,["Parámetro","Valor","Observación"],[68*mm,42*mm,60*mm]))
    story.append(Spacer(1,5*mm))

    # 2. Desarrollo del cálculo
    story.append(Paragraph("2. Desarrollo del cálculo — Modelo Bradford (Castilho & Medronho, 2000)", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    calc_steps = [
        ("Velocidad característica", "v = Q / (π/4·D²)", f"v = {r['v']:.4f} m/s"),
        ("Número de Reynolds (Ec.)", "Re = ρf·v·D / μ",  f"Re = {r['Re']:.2f}"),
        ("Número de Euler (Ec. 5)",  "Eu = 371.5·Re^0.116·exp(−2.12·c_gg)", f"Eu = {r['Eu']:.4f}"),
        ("Relación flujo UF (Ec. 6)","Rf = 1218·(Du/D)^4.75·Eu^−0.3",      f"Rf = {r['Rf']:.6f} = {r['Rf']*100:.2f}%"),
        ("Stokes reducido (Ec. 4)",  "Stk'·Eu = 0.0474·[ln(1/Rf)]^0.742·exp(8.96·c_gg)", f"Stk' = {r['Stk']:.6f}"),
        ("Tamaño de corte",          "x'₅₀ = √(Stk'·18·μ·D / ((ρs−ρf)·v))", f"x'₅₀ = {r['x50_um']:.3f} µm"),
        ("Caída de presión",         "ΔP = Eu·ρf·v²/2",                      f"ΔP = {r['dP_kPa']:.2f} kPa"),
        ("Caudal por ciclón",        "Q_cicl = v·π/4·D²",                    f"Q_cicl = {r['Q_cicl_Lh']:.2f} L/h"),
        ("Ciclones necesarios",      "n = Q_total / Q_cicl",                  f"n = {r['n_cicl_calc']:.2f} (instalados: {r['n_total_inst']})"),
        ("Eficiencia D50=20µm",      "G(20µm) = Rf+(1−Rf)·G'(20µm)",        f"G(20µm) = {r['eff_d50']:.2f}%"),
    ]
    story.append(tabla_rl(calc_steps,["Paso","Ecuación","Resultado"],[45*mm,90*mm,35*mm]))
    story.append(Spacer(1,5*mm))

    # 3. Dimensiones geométricas
    story.append(Paragraph("3. Dimensiones geométricas del hidrociclón individual", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    story.append(tabla_rl(
        [[d["Símbolo plano"],d["Nomenclatura técnica"],d["Valor (mm)"],
          d["Relación geométrica"],d["Tolerancia"],d["Estado"]] for d in tabla_cotas],
        ["Símbolo","Parámetro","Valor (mm)","Relación","Tolerancia","Estado"],
        [16*mm,62*mm,22*mm,52*mm,25*mm,22*mm]))
    story.append(PageBreak())

    # 4. Planos técnicos (una por página)
    for tit, gen in [
        ("4. Plano HK-001-R0 — Vista Longitudinal (Corte A-A)", fig_longitudinal),
        ("5. Plano HK-002-R0 — Vista Superior (Planta)", fig_superior),
        ("6. Plano HK-003-R0 — Detalle Entrada Tangencial", fig_entrada_tangencial),
        ("7. Plano HK-004-R0 — Vista Isométrica", fig_isometrica),
    ]:
        story.append(Paragraph(tit, subtit_s))
        story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
        f = gen(r)
        story.append(fig_para_rl(f, dpi=180, w_mm=168, h_mm=145))
        plt.close(f)
        story.append(PageBreak())

    # 8. KPIs y verificaciones
    story.append(Paragraph("8. Resultados — KPIs y verificaciones operativas", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    kpi_data = [
        ["D principal",        f"{r['D']:.1f} mm",          "Diámetro nominal del ciclón"],
        ["ΔP hidrociclón",     f"{r['dP_kPa']:.1f} kPa",    "Límite operativo: 700 kPa"],
        ["x'₅₀ de corte",      f"{r['x50_um']:.2f} µm",     "Tamaño reducido de separación"],
        ["Rf underflow",       f"{r['Rf']*100:.2f} %",       "Fracción mínima al underflow"],
        ["Velocidad entrada",  f"{r['v']:.3f} m/s",          "Límite recomendado: ≤ 6 m/s"],
        ["Q por ciclón",       f"{r['Q_cicl_Lh']:.2f} L/h",  "Caudal volumétrico individual"],
        ["N° cicl. calculados",f"{r['n_cicl_calc']:.2f}",    f"Instalados: {r['n_total_inst']}"],
        ["Reynolds (Re)",      f"{r['Re']:.1f}",             "Flujo turbulento desarrollado"],
        ["Euler (Eu)",         f"{r['Eu']:.2f}",             "Resistencia del flujo"],
        ["Efic. D50=20µm",     f"{r['eff_d50']:.2f} %",      "Almidón jengibre típico"],
    ]
    story.append(tabla_rl(kpi_data,["KPI","Valor","Observación"],[55*mm,40*mm,75*mm]))
    story.append(Spacer(1,5*mm))
    ver_data=[[c["Verificación"],c["Valor"],c["Estado"]] for c in chks]
    story.append(tabla_rl(ver_data,["Verificación","Valor","Estado"],[100*mm,30*mm,40*mm]))
    story.append(PageBreak())

    # 9. Sistema de 3 bancos
    story.append(Paragraph("9. Sistema de 3 bancos — Distribución de flujo y potencia", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    ban_data=[[f"Banco {b}",f"{BANCOS[b]} ciclones",
               f"{r['pot_banco'][b]['Q_Lh']:.0f} L/h",
               f"{r['pot_banco'][b]['P_kW']:.3f} kW",
               f"{r['pot_banco'][b]['P_HP']:.3f} HP",
               f"{r['pot_banco'][b]['nom_HP']} HP",
               "✅ OK" if r['pot_banco'][b]['P_HP']<=r['pot_banco'][b]['nom_HP'] else "⚠️ Revisar"]
              for b in BANCOS]
    story.append(tabla_rl(ban_data,
        ["Banco","N° cicl.","Q banco","P hidráulica","P req. (HP)","P bomba","Estado"],
        [20*mm,22*mm,30*mm,32*mm,28*mm,26*mm,28*mm]))
    story.append(Spacer(1,5*mm))

    # 10. Tuberías
    story.append(Paragraph("10. Dimensionamiento de tuberías colectoras (SAE 304)", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    pipe_data=[
        ["Alimentación (feed)", f"DN {r['DN_feed']} mm", f"{r['d_feed_mm']:.1f} mm",
         f"{r['vr_feed']:.2f} m/s","✅ OK" if r['vr_feed']<=3 else "⚠️"],
        ["Colector overflow",   f"DN {r['DN_OF']} mm",   f"{r['d_OF_mm']:.1f} mm",
         f"{r['vr_OF']:.2f} m/s","✅ OK" if r['vr_OF']<=3 else "⚠️"],
        ["Colector underflow",  f"DN {r['DN_UF']} mm",   f"{r['d_UF_mm']:.1f} mm",
         f"{r['vr_UF']:.2f} m/s","✅ OK" if r['vr_UF']<=3 else "⚠️"],
    ]
    story.append(tabla_rl(pipe_data,["Línea","DN estándar","D calculado","Vel. real","Estado"],
        [50*mm,30*mm,32*mm,30*mm,28*mm]))
    story.append(PageBreak())

    # 11. Notas de fabricación
    story.append(Paragraph("11. Notas de fabricación — SAE 304 alimentario", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    secciones_fab = [
        ("Tolerancias críticas", [
            f"Diámetro D: ±0.10 mm",f"Diámetro Do (overflow): ±0.05 mm",
            f"Diámetro Du (underflow/spigot): ±0.05 mm",
            "Ángulo cónico α: ±0.5°","Longitud vórtex finder Lv: ±0.30 mm",
            "Concentricidad vórtex finder: TIR ≤ 0.05 mm",
        ]),
        ("Acabado superficial", [
            "Interior zona cilíndrica: Ra ≤ 0.8 µm (electropolido)",
            "Interior zona cónica y entrada tangencial: Ra ≤ 0.4 µm",
            "Exterior sanitario: Ra ≤ 1.6 µm",
            "Sin soldaduras expuestas al fluido alimentario",
            "Certificación EN 10204 tipo 3.1",
        ]),
        ("Soldadura TIG — SS304", [
            "Proceso GTAW (TIG) con back purge de Ar 99.99% al interior",
            "Material de aporte: ER308L (C < 0.03%)",
            "Gas protección: Argón 99.99%, 8–12 L/min",
            "Temperatura entre pasadas: ≤ 100°C",
            "END: Líquidos penetrantes PT tras soldadura",
        ]),
        ("CIP/SIP", [
            "1. Pre-enjuague: agua potable fría, 3 min",
            "2. Soda cáustica NaOH 1.5%, 70°C, 15 min",
            "3. Enjuague: agua desmineralizada, 5 min",
            "4. Ácido peracético 0.2%, 10 min",
            "5. Enjuague final: agua purificada (conductividad ≤ 10 µS/cm)",
        ]),
    ]
    for titulo_sec, items in secciones_fab:
        story.append(Paragraph(f"<b>{titulo_sec}</b>", normal_s))
        for item in items:
            story.append(Paragraph(f"• {item}", peq_s))
        story.append(Spacer(1,3*mm))

    # 12. Referencias
    story.append(PageBreak())
    story.append(Paragraph("12. Referencias bibliográficas", subtit_s))
    story.append(HRFlowable(width='100%',thickness=1,color=azul,spaceAfter=4))
    refs=[
        "Castilho, L.R. & Medronho, R.A. (2000). A simple procedure for design and performance prediction of Bradley and Rietema hydrocyclones. Minerals Engineering, 13(2), 183–191.",
        "Sáiz Rubio, V. (2009). Design of an Energy-saving Hydrocyclone for Wheat Starch Separation. Växjö University, TD 052/2009.",
        "Reyes, O.A. (1982). Characterization of Starch from Ginger Root (Zingiber officinale). Starch/Stärke, 34(2), 40–44.",
        "Chu, L.Y. et al. (2000). Energy-efficient hydrocyclone design parameters. Chemical Engineering Research and Design.",
        "Grommers, H.E. et al. (2004). Potato Starch: Production, Modifications and Uses. Wiley.",
        "Svarovsky, L. (2000). Solid-Liquid Separation, 4th ed. Butterworth-Heinemann.",
        "Buriticá Henao, P.A. (2011). Sistema Hidrociclónico para la Separación del Almidón de Sagú. Universidad de los Andes, Bogotá.",
    ]
    for i,ref in enumerate(refs,1):
        story.append(Paragraph(f"{i}. {ref}", peq_s))
        story.append(Spacer(1,2*mm))

    doc.build(story)
    buf_pdf.seek(0)
    return buf_pdf

# ─────────────────────────────────────────────
# BOTONES DE EXPORTACIÓN PDF
# ─────────────────────────────────────────────
st.markdown("### 📄 Exportar documentos")
col_pdf1, col_pdf2 = st.columns(2)

with col_pdf1:
    st.markdown("""**📐 PDF Taller** — Planos A3 horizontal para fabricación  
    Incluye: carátula · 4 planos técnicos · tabla de cotas · notas SS304""")
    if st.button("⬇ Generar PDF Taller (A3)", key="pdf_taller"):
        with st.spinner("⚙️ Generando PDF de fabricación…"):
            try:
                b1=fig_to_bytes(fig_longitudinal(r))
                b2=fig_to_bytes(fig_superior(r))
                b3=fig_to_bytes(fig_entrada_tangencial(r))
                b4=fig_to_bytes(fig_isometrica(r))
                pdf_buf = pdf_taller(r, b1, b2, b3, b4)
                st.download_button("📥 Descargar PDF Taller",pdf_buf.getvalue(),
                    "HK-Taller-Hidrociclon-Kion.pdf","application/pdf",
                    use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar PDF: {e}")

with col_pdf2:
    st.markdown("""**📋 PDF Informe Técnico** — Documento A4 vertical completo  
    Incluye: carátula · cálculos · planos · KPIs · bancos · tuberías · fabricación · referencias""")
    if st.button("⬇ Generar PDF Informe Completo (A4)", key="pdf_informe"):
        with st.spinner("⚙️ Generando informe técnico completo…"):
            try:
                b1=fig_to_bytes(fig_longitudinal(r))
                b2=fig_to_bytes(fig_superior(r))
                b3=fig_to_bytes(fig_entrada_tangencial(r))
                b4=fig_to_bytes(fig_isometrica(r))
                pdf_buf2 = pdf_informe(r, b1, b2, b3, b4)
                st.download_button("📥 Descargar Informe Técnico Completo",pdf_buf2.getvalue(),
                    "HK-Informe-Tecnico-Hidrociclon-Kion.pdf","application/pdf",
                    use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar PDF: {e}")

# ─────────────────────────────────────────────
# NOTAS DE FABRICACIÓN (expander)
# ─────────────────────────────────────────────
with st.expander("📋 Notas de fabricación detalladas — SAE 304"):
    nc1,nc2,nc3 = st.columns(3)
    with nc1:
        st.markdown("""**🔧 Tolerancias**
| Zona | Tolerancia |
|------|-----------|
| D | ±0.10 mm |
| Do | ±0.05 mm |
| Du (spigot) | ±0.05 mm |
| Ángulo α | ±0.5° |
| Lv | ±0.30 mm |
| Concentricidad | TIR ≤ 0.05 mm |""")
    with nc2:
        st.markdown("""**⚗️ Acabado y soldadura**
- Interior cilíndrico: Ra ≤ 0.8 µm
- Interior cónico: Ra ≤ 0.4 µm
- TIG ER308L + back purge Ar
- Pasivado HNO₃ 20%, 30 min
- Certificación EN 10204 tipo 3.1
- Prueba hidrostática: 1.5×P_trabajo""")
    with nc3:
        st.markdown("""**🛠️ CIP/SIP y mantenimiento**
1. Pre-enjuague agua fría, 3 min
2. NaOH 1.5%, 70°C, 15 min
3. Enjuague DI, 5 min
4. Ácido peracético 0.2%, 10 min
5. Enjuague final ≤10 µS/cm
- Spigot: revisar desgaste mensual
- O-rings: cambio preventivo 6 meses""")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<hr style='margin:16px 0 8px 0'>", unsafe_allow_html=True)
st.markdown("""<div style="text-align:center;font-size:.78rem;color:#718096;padding:4px 0 10px">
    <b>UNIÓN DE NEGOCIOS CORPORATIVOS — Perú</b> &nbsp;·&nbsp;
    Sistema Hidrociclónico · Almidón de Kion &nbsp;·&nbsp;
    Modelo Bradford (Castilho & Medronho, 2000) &nbsp;·&nbsp;
    Ing. Froilán Becerra &nbsp;·&nbsp; <b>v2.0 — Junio 2026</b>
</div>""", unsafe_allow_html=True)

# =============================================================================
# requirements.txt
# streamlit>=1.32.0
# numpy>=1.24.0
# matplotlib>=3.7.0
# plotly>=5.18.0
# pandas>=2.0.0
# scipy>=1.10.0
# reportlab>=4.0.0
# =============================================================================
