"""
app.py — Punto de entrada principal de la app "Visitas Oficiales — Prueba"
Orquesta el mapa interactivo, filtros y panel de detalle con foto
"""

import os
import pandas as pd
import streamlit as st

# Importar módulos del proyecto
from modules.filtros import renderizar_filtros
from modules.mapa import renderizar_mapa
from modules.detalle_visita import mostrar_detalle

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Visitas Oficiales — Prueba",
    page_icon="🌍",
)


def cargar_datos() -> pd.DataFrame:
    """
    Carga el archivo CSV de visitas desde la ruta relativa al proyecto.

    Retorna:
        pd.DataFrame: DataFrame con todas las visitas cargadas.
    """
    # Ruta relativa al CSV desde el directorio donde se ejecuta la app
    ruta_csv = os.path.join(os.path.dirname(__file__), "data", "visitas.csv")
    df = pd.read_csv(ruta_csv, encoding="utf-8")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def calcular_metricas(df: pd.DataFrame) -> dict:
    """
    Calcula las 4 métricas principales a mostrar en la cabecera.

    Parámetros:
        df (pd.DataFrame): DataFrame con las visitas (puede ser el filtrado).

    Retorna:
        dict: Diccionario con los valores de cada métrica.
    """
    total_visitas = len(df)
    paises_visitados = df["pais"].nunique()
    total_dias = int(df["duracion_dias"].sum())

    if not df.empty:
        tipo_frecuente = df["tipo_actividad"].value_counts().idxmax()
    else:
        tipo_frecuente = "—"

    return {
        "total_visitas": total_visitas,
        "paises_visitados": paises_visitados,
        "total_dias": total_dias,
        "tipo_frecuente": tipo_frecuente,
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

    # ── Filtros en sidebar (retorna DataFrame filtrado) ───────────────────────
    df_filtrado = renderizar_filtros(df_completo)

    # ── Fila de métricas (basadas en el DataFrame FILTRADO) ───────────────────
    metricas = calcular_metricas(df_filtrado)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total de Visitas",
            value=metricas["total_visitas"],
            delta=None,
        )
    with col2:
        st.metric(
            label="Países Visitados",
            value=metricas["paises_visitados"],
        )
    with col3:
        st.metric(
            label="Total Días en Exterior",
            value=f"{metricas['total_dias']} días",
        )
    with col4:
        st.metric(
            label="Actividad más Frecuente",
            value=metricas["tipo_frecuente"],
        )

    st.divider()

    # ── Mapa interactivo ──────────────────────────────────────────────────────
    fila_clickeada = renderizar_mapa(df_filtrado)

    # Actualizar visita seleccionada si se hizo clic en el mapa
    if fila_clickeada is not None:
        st.session_state["visita_seleccionada"] = fila_clickeada

    # ── Panel de detalle en el sidebar ────────────────────────────────────────
    visita_activa = st.session_state.get("visita_seleccionada")
    if visita_activa is not None:
        with st.sidebar:
            st.markdown("---")
            mostrar_detalle(visita_activa)

    # ── Nota informativa en el sidebar si no hay visita seleccionada ──────────
    elif st.session_state.get("visita_seleccionada") is None:
        with st.sidebar:
            st.markdown("---")
            st.info(
                "Haz clic en un marcador del mapa para ver "
                "el detalle de la visita y la foto de la autoridad."
            )


if __name__ == "__main__":
    main()
