"""
app.py — Punto de entrada principal de la app "Visitas Oficiales — Prueba"
Orquesta el mapa interactivo, filtros y panel de detalle con foto
"""

import os
import pandas as pd
import streamlit as st

from modules.filtros import renderizar_filtros
from modules.mapa import renderizar_mapa
from modules.detalle_visita import mostrar_detalle, mostrar_foto, _badge_tipo

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Visitas Oficiales — Prueba",
    page_icon="🌍",
)


def cargar_datos() -> pd.DataFrame:
    """Carga el CSV de visitas desde la ruta relativa al proyecto."""
    ruta_csv = os.path.join(os.path.dirname(__file__), "data", "visitas.csv")
    df = pd.read_csv(ruta_csv, encoding="utf-8")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def calcular_metricas(df: pd.DataFrame) -> dict:
    """Calcula las 4 métricas principales según el DataFrame filtrado."""
    if df.empty:
        return {
            "total_visitas": 0,
            "paises_visitados": 0,
            "total_dias": 0,
            "tipo_frecuente": "—",
        }
    return {
        "total_visitas": len(df),
        "paises_visitados": df["pais"].nunique(),
        "total_dias": int(df["duracion_dias"].sum()),
        "tipo_frecuente": df["tipo_actividad"].value_counts().idxmax(),
    }


def main():
    """Función principal que orquesta todos los componentes de la app."""

    # ── Inicializar session_state ─────────────────────────────────────────────
    if "visita_seleccionada" not in st.session_state:
        st.session_state["visita_seleccionada"] = None

    # ── Cargar datos ──────────────────────────────────────────────────────────
    df_completo = cargar_datos()

    # ── Cabecera principal ────────────────────────────────────────────────────
    st.title("🌍 Visitas Oficiales — Máxima Autoridad")
    st.caption(
        "Visualización geoespacial de visitas oficiales al exterior · "
        "Versión de prueba · 3 países · 9 visitas"
    )

    # ── Filtros en sidebar ────────────────────────────────────────────────────
    df_filtrado = renderizar_filtros(df_completo)

    # ── Fila de métricas ──────────────────────────────────────────────────────
    metricas = calcular_metricas(df_filtrado)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Visitas", metricas["total_visitas"])
    with col2:
        st.metric("Países Visitados", metricas["paises_visitados"])
    with col3:
        st.metric("Total Días en Exterior", f"{metricas['total_dias']} días")
    with col4:
        st.metric("Actividad más Frecuente", metricas["tipo_frecuente"])

    st.divider()

    # ── Layout principal: mapa + foto al seleccionar ──────────────────────────
    visita_activa = st.session_state.get("visita_seleccionada")

    if visita_activa is not None:
        # Con visita seleccionada: mapa a la izquierda, foto a la derecha
        col_mapa, col_foto = st.columns([2, 1])

        with col_mapa:
            fila_clickeada = renderizar_mapa(df_filtrado)

        with col_foto:
            st.markdown(f"### {visita_activa['pais']} — {visita_activa['ciudad']}")
            tipo = str(visita_activa.get("tipo_actividad", ""))
            st.markdown(_badge_tipo(tipo), unsafe_allow_html=True)
            st.markdown("")
            mostrar_foto(visita_activa, use_container_width=True)

    else:
        # Sin visita seleccionada: mapa ocupa todo el ancho
        fila_clickeada = renderizar_mapa(df_filtrado)

    # Actualizar visita seleccionada si se hizo clic en el mapa
    if fila_clickeada is not None:
        st.session_state["visita_seleccionada"] = fila_clickeada
        st.rerun()

    # ── Panel de detalle completo en el sidebar ───────────────────────────────
    if visita_activa is not None:
        with st.sidebar:
            st.markdown("---")
            mostrar_detalle(visita_activa)
    else:
        with st.sidebar:
            st.markdown("---")
            st.info(
                "Haz clic en un marcador del mapa para ver "
                "el detalle de la visita y la foto de la autoridad."
            )


if __name__ == "__main__":
    main()
