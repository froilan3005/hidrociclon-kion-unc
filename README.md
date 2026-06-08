# Sistema Hidrociclónico — Separación de Almidón de Jengibre (Kion)

**UNIÓN DE NEGOCIOS CORPORATIVOS — Perú**  
Ing. Froilán Becerra — Jefe de Mantenimiento  
Versión 1.0 — Junio 2026

---

## Descripción

Aplicación web para el **diseño y análisis** de sistemas hidrociclónicos industriales 
destinados a la separación continua de almidón de jengibre (*Zingiber officinale*).

Implementa el **modelo adimensional de Bradford** (Castilho & Medronho, 2000) con:
- Iteración numérica por `scipy.optimize.brentq` 
- Geometría completa (Chu et al., 2000; Grommers et al., 2004)
- Curva de eficiencia G(x) interactiva (Plotly)
- Diagrama 2D a escala con cotas (Matplotlib)
- Verificaciones operativas automáticas (semáforo verde/amarillo/rojo)
- Dimensionamiento de tuberías colectoras (SS304)

## Sistema de referencia

| Parámetro | Especificación |
|-----------|---------------|
| Modelo hidrociclón | Hy38/1100 (1½") |
| Capacidad nominal | 1,500 L/h |
| Configuración | 3 bancos: 4+3+2 ciclones |
| Bombas | Pentax (España): 3+3+2 HP |
| Material | Acero inoxidable SAE 304 |
| Conexiones | Tri-Clamp sanitario |

## Propiedades del almidón de jengibre

- **Densidad:** ρ_s = 1,517 kg/m³ (Reyes, 1982) — *fijo en el modelo*
- **T_gelatinización:** 80°C — sin riesgo a temperatura ambiente
- **D₅₀:** ≈ 20 µm (*Zingiber officinale*, distribución amplia 2–50 µm)

## Instalación local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy en Streamlit Community Cloud

1. Subir este repositorio a GitHub (público o privado)
2. Ir a [share.streamlit.io](https://share.streamlit.io)
3. Conectar el repositorio → seleccionar `app.py` → Deploy
4. La app estará disponible en `https://[usuario]-[repo]-[hash].streamlit.app`

## Estructura del repositorio

```
├── app.py              # Aplicación principal Streamlit
├── requirements.txt    # Dependencias Python
└── README.md           # Este archivo
```

## Modos de cálculo

| Modo | Input | Output |
|------|-------|--------|
| **Fijar ΔP** | Presión de trabajo (kPa) + D (mm) | v, Q_cicl, x'₅₀, Rf, n_cicl |
| **Fijar v** | Velocidad entrada (m/s) + D (mm) | ΔP, Q_cicl, x'₅₀, Rf, n_cicl |

## Referencias

- Castilho, L.R. & Medronho, R.A. (2000). *Minerals Engineering*, 13(2), 183–191.
- Sáiz Rubio, V. (2009). *Växjö University, TD 052/2009.*
- Reyes, O.A. (1982). *Starch/Stärke*, 34(2), 40–44.
- Chu, L.Y. et al. (2000). *Chem. Eng. Res. Design.*
- Svarovsky, L. (2000). *Solid-Liquid Separation*, 4th ed.
