"""
app.py — Punto de entrada principal de la app "Visitas Oficiales — Prueba"
Mapa satélite tipo Google Earth + panel de foto/detalle en área principal
El sidebar contiene solo los filtros
"""

import os
import pandas as pd
import streamlit as st

from modules.filtros import renderizar_filtros
from modules.mapa import renderizar_mapa
from modules.detalle_visita import mostrar_foto, _badge_tipo, _formatear_fecha

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
        return {"total_visitas": 0, "paises_visitados": 0,
                "total_dias": 0, "tipo_frecuente": "—"}
    return {
        "total_visitas": len(df),
        "paises_visitados": df["pais"].nunique(),
        "total_dias": int(df["duracion_dias"].sum()),
        "tipo_frecuente": df["tipo_actividad"].value_counts().idxmax(),
    }


def panel_detalle_principal(fila: pd.Series) -> None:
    """
    Muestra el panel de detalle de la visita seleccionada en el área principal,
    debajo del mapa. Incluye foto, badge, métricas y descripción.
    """
    st.divider()

    col_foto, col_info = st.columns([1, 2])

    with col_foto:
        mostrar_foto(fila, use_container_width=True)

    with col_info:
        # Encabezado
        st.markdown(f"## {fila['pais']} — {fila['ciudad']}")
        tipo = str(fila.get("tipo_actividad", ""))
        st.markdown(_badge_tipo(tipo), unsafe_allow_html=True)
        st.markdown("")

        # Métricas rápidas
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Duración", f"{int(fila['duracion_dias'])} días")
        with m2:
            st.metric("Fecha", _formatear_fecha(str(fila.get("fecha", ""))))

        # Descripción y contraparte
        st.write(fila.get("descripcion", "Sin descripción disponible."))
        st.info(f"**Contraparte:** {fila.get('contraparte', 'No especificada')}")

        # Botón cerrar
        if st.button("✕ Cerrar detalle", key="btn_cerrar", use_container_width=True):
            st.session_state["visita_seleccionada"] = None
            st.rerun()


def main():
    """Función principal que orquesta todos los componentes de la app."""

    # ── Inicializar session_state ─────────────────────────────────────────────
    if "visita_seleccionada" not in st.session_state:
        st.session_state["visita_seleccionada"] = None

    # ── Cargar datos ──────────────────────────────────────────────────────────
    df_completo = cargar_datos()

    # ── Sidebar: solo filtros ─────────────────────────────────────────────────
    df_filtrado = renderizar_filtros(df_completo)

    # ── Cabecera ──────────────────────────────────────────────────────────────
    st.title("🌍 Visitas Oficiales — Máxima Autoridad")
    st.caption(
        "Visualización geoespacial · Vista satélite · "
        "Versión de prueba · 3 países · 9 visitas"
    )

    # ── Métricas ──────────────────────────────────────────────────────────────
    metricas = calcular_metricas(df_filtrado)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Visitas", metricas["total_visitas"])
    c2.metric("Países Visitados", metricas["paises_visitados"])
    c3.metric("Total Días en Exterior", f"{metricas['total_dias']} días")
    c4.metric("Actividad más Frecuente", metricas["tipo_frecuente"])

    st.divider()

    # ── Mapa satélite ─────────────────────────────────────────────────────────
    fila_clickeada = renderizar_mapa(df_filtrado)

    if fila_clickeada is not None:
        st.session_state["visita_seleccionada"] = fila_clickeada
        st.rerun()

    # ── Panel de detalle debajo del mapa (sin sidebar) ────────────────────────
    visita_activa = st.session_state.get("visita_seleccionada")
    if visita_activa is not None:
        panel_detalle_principal(visita_activa)
    else:
        st.caption("👆 Haz clic sobre un marcador del mapa para ver el detalle de la visita.")


if __name__ == "__main__":
    main()
