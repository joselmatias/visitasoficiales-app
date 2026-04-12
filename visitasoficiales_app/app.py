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
from modules.detalle_visita import mostrar_foto, _badge_tipo, _formatear_fecha


CONTINENTES = {
    "Japón":       "Asia",
    "Alemania":    "Europa",
    "Colombia":    "América del Sur",
    "Brasil":      "América del Sur",
    "Argentina":   "América del Sur",
    "Chile":       "América del Sur",
    "Perú":        "América del Sur",
    "México":      "América del Norte",
    "EEUU":        "América del Norte",
    "Estados Unidos": "América del Norte",
    "Canadá":      "América del Norte",
    "Francia":     "Europa",
    "España":      "Europa",
    "Italia":      "Europa",
    "Reino Unido": "Europa",
    "China":       "Asia",
    "India":       "Asia",
    "Corea del Sur": "Asia",
    "Australia":   "Oceanía",
    "Sudáfrica":   "África",
    "Egipto":      "África",
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


def panel_detalle_principal(fila: pd.Series) -> None:
    st.divider()
    col_foto, col_info = st.columns([1, 2])

    with col_foto:
        mostrar_foto(fila, use_container_width=True)

    with col_info:
        st.markdown(f"## {fila['pais']} — {fila['ciudad']}")
        tipo = str(fila.get("tipo_actividad", ""))
        st.markdown(_badge_tipo(tipo), unsafe_allow_html=True)
        st.markdown("")

        m1, m2 = st.columns(2)
        with m1:
            st.metric("Duración", f"{int(fila['duracion_dias'])} días")
        with m2:
            st.metric("Fecha", _formatear_fecha(str(fila.get("fecha", ""))))

        st.write(fila.get("descripcion", "Sin descripción disponible."))
        st.info(f"**Contraparte:** {fila.get('contraparte', 'No especificada')}")

        if st.button("✕ Cerrar detalle", key="btn_cerrar", use_container_width=True):
            st.session_state["visita_seleccionada"] = None
            st.session_state["_ultimo_clic_mapa"] = None
            st.rerun()


def main():
    # ── Inicializar session_state ─────────────────────────────────────────────
    if "visita_seleccionada" not in st.session_state:
        st.session_state["visita_seleccionada"] = None
    if "_ultimo_clic_mapa" not in st.session_state:
        st.session_state["_ultimo_clic_mapa"] = None

    # ── Cargar datos ──────────────────────────────────────────────────────────
    df_completo = cargar_datos()

    # ── Sidebar: logo + filtros ───────────────────────────────────────────────
    logo = _cargar_logo()
    if logo:
        st.sidebar.image(logo, use_container_width=True)
        st.sidebar.markdown("---")

    df_filtrado = renderizar_filtros(df_completo)

    # ── Si la visita seleccionada ya no está en el filtro activo, limpiarla ───
    visita_activa = st.session_state.get("visita_seleccionada")
    if visita_activa is not None:
        ids_visibles = df_filtrado["id"].tolist()
        if int(visita_activa["id"]) not in ids_visibles:
            st.session_state["visita_seleccionada"] = None
            st.session_state["_ultimo_clic_mapa"] = None
            visita_activa = None

    # ── Cabecera: logo + título ───────────────────────────────────────────────
    if logo:
        col_logo, col_titulo = st.columns([1, 5])
        with col_logo:
            st.image(logo, use_container_width=True)
        with col_titulo:
            st.title("🌍 Visitas Oficiales — Máxima Autoridad")
            st.caption(
                "Visualización geoespacial · Vista satélite · "
                "Versión de prueba · 3 países · 3 visitas"
            )
    else:
        st.title("🌍 Visitas Oficiales — Máxima Autoridad")
        st.caption(
            "Visualización geoespacial · Vista satélite · "
            "Versión de prueba · 3 países · 3 visitas"
        )
    st.caption(
        "Desarrollado por: Dirección Regional de Abogacía de la Competencia "
        "— Intendencia Regional · DRAC-IR"
    )

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
    fila_clickeada = renderizar_mapa(df_filtrado)

    # Actualizar la visita seleccionada si hubo un clic nuevo.
    # No se usa st.rerun() porque st_folium ya genera un rerun automático
    # al recibir la interacción del usuario. El doble rerun causaba que
    # el mapa se recreara mostrando la capa callejero por defecto.
    if fila_clickeada is not None:
        st.session_state["visita_seleccionada"] = fila_clickeada

    # ── Panel de detalle debajo del mapa ──────────────────────────────────────
    visita_activa = st.session_state.get("visita_seleccionada")
    if visita_activa is not None:
        panel_detalle_principal(visita_activa)
    else:
        st.caption("👆 Haz clic sobre un marcador del mapa para ver el detalle de la visita.")


if __name__ == "__main__":
    main()
