"""
app.py — Punto de entrada principal de la app "Visitas Oficiales — Prueba"
Mapa satélite tipo Google Earth + panel de foto/detalle en área principal
El sidebar contiene solo los filtros
"""

import os
import pandas as pd
import streamlit as st
from PIL import Image

from modules.filtros import renderizar_filtros
from modules.mapa import renderizar_mapa


CONTINENTES = {
    "Japón":          "Asia",
    "Alemania":       "Europa",
    "Colombia":       "América del Sur",
    "Brasil":         "América del Sur",
    "Argentina":      "América del Sur",
    "Chile":          "América del Sur",
    "Perú":           "América del Sur",
    "México":         "América del Norte",
    "EEUU":           "América del Norte",
    "Estados Unidos": "América del Norte",
    "Canadá":         "América del Norte",
    "Francia":        "Europa",
    "España":         "Europa",
    "Italia":         "Europa",
    "Reino Unido":    "Europa",
    "Escocia":        "Europa",
    "China":          "Asia",
    "India":          "Asia",
    "Corea del Sur":  "Asia",
    "Australia":      "Oceanía",
    "Sudáfrica":      "África",
    "Egipto":         "África",
    "Costa Rica":     "América Central",
}


def _cargar_logo() -> Image.Image | None:
    ruta = os.path.join(os.path.dirname(__file__), "assets", "logo_presidencia.png")
    if os.path.exists(ruta):
        img = Image.open(ruta).convert("RGBA")
        # Componer sobre fondo blanco para que sea visible en modo oscuro
        fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
        fondo.paste(img, mask=img.split()[3])
        return fondo.convert("RGB")
    return None


def _cargar_foto_header() -> Image.Image | None:
    """Carga la foto de la máxima autoridad para el encabezado."""
    base = os.path.dirname(__file__)
    candidatos = [
        os.path.join(base, "assets", "foto_autoridad.jpg"),
        os.path.join(base, "assets", "foto_autoridad.png"),
        os.path.join(base, "assets", "fotos", "foto_japon.jpg"),
        os.path.join(base, "assets", "fotos", "foto_alemania.jfif"),
        os.path.join(base, "assets", "fotos", "foto_colombia.jfif"),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            return Image.open(ruta).convert("RGB")
    return None

st.set_page_config(
    layout="wide",
    page_title="Visitas Oficiales — Prueba",
    page_icon="🌍",
)


def cargar_datos() -> pd.DataFrame:
    ruta_csv = os.path.join(os.path.dirname(__file__), "data", "visitas.csv")
    df = pd.read_csv(ruta_csv, encoding="utf-8")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def calcular_metricas(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_visitas": 0,
            "paises_visitados": 0,
            "total_dias": 0,
            "tipo_frecuente": "—",
            "tipos_actividad": 0,
            "continentes": 0,
        }
    continentes_visitados = df["pais"].map(CONTINENTES).dropna().nunique()
    return {
        "total_visitas": len(df),
        "paises_visitados": df["pais"].nunique(),
        "total_dias": int(df["duracion_dias"].sum()),
        "tipo_frecuente": df["tipo_actividad"].value_counts().idxmax(),
        "tipos_actividad": df["tipo_actividad"].nunique(),
        "continentes": continentes_visitados,
    }


def main():
    # ── Cargar datos ──────────────────────────────────────────────────────────
    df_completo = cargar_datos()

    # ── Sidebar: logo + filtros ───────────────────────────────────────────────
    logo = _cargar_logo()
    if logo:
        st.sidebar.image(logo, use_container_width=True)

    df_filtrado = renderizar_filtros(df_completo)

    # ── Cabecera: foto izquierda + título + logo derecho ─────────────────────
    foto_header = _cargar_foto_header()
    col_foto, col_titulo, col_logo = st.columns([1, 5, 1])
    with col_foto:
        if foto_header:
            st.image(foto_header, use_container_width=True)
    with col_titulo:
        st.title("🌍 Visitas Oficiales")
        st.header("Superintendente de Competencia Económica")
        st.caption(
            "Visualización geoespacial · Vista satélite · "
            "Desarrollado por: DRAC-IR"
        )
    with col_logo:
        if logo:
            st.image(logo, use_container_width=True)

    # ── Métricas ──────────────────────────────────────────────────────────────
    metricas = calcular_metricas(df_filtrado)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Visitas", metricas["total_visitas"])
    c2.metric("Países Visitados", metricas["paises_visitados"])
    c3.metric("Total Días en Exterior", f"{metricas['total_dias']} días")

    c4, c5, c6 = st.columns(3)
    c4.metric("Actividad más Frecuente", metricas["tipo_frecuente"])
    c5.metric("Tipos de Actividad", metricas["tipos_actividad"])
    c6.metric("Continentes Visitados", metricas["continentes"])

    st.divider()

    # ── Mapa satélite ─────────────────────────────────────────────────────────
    renderizar_mapa(df_filtrado)


if __name__ == "__main__":
    main()
