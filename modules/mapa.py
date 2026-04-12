"""
mapa.py — Globo 3D interactivo con Plotly (proyección ortográfica)
Estilo vista satélite: océanos azul profundo + tierra en tonos naturales
Captura clics via st.plotly_chart on_select para identificar la visita seleccionada
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Paleta de colores por tipo de actividad
COLORES_ACTIVIDAD = {
    "Firma de Convenio":         "#00E5CC",
    "Conferencia Internacional":  "#C77DFF",
    "Visita Técnica":            "#FFD166",
    "Reunión Bilateral":         "#FFEF5E",
    "Foro / Cumbre":             "#FF6B9D",
    "Visita Oficial":            "#4FC3F7",
}


def construir_globo(df: pd.DataFrame) -> go.Figure:
    """
    Construye el globo 3D con proyección ortográfica estilo vista satélite.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        go.Figure: Figura Plotly lista para renderizar.
    """
    fig = go.Figure()

    # ── Marcadores de visitas ─────────────────────────────────────────────────
    colores  = [COLORES_ACTIVIDAD.get(t, "#FFFFFF") for t in df["tipo_actividad"]]
    tamanos  = [max(16, int(d) * 4) for d in df["duracion_dias"]]
    tooltips = [
        (
            f"<b>{row['pais']} — {row['ciudad']}</b><br>"
            f"<span style='color:{COLORES_ACTIVIDAD.get(row['tipo_actividad'], '#fff')}'>"
            f"■ {row['tipo_actividad']}</span><br>"
            f"📅 {str(row['fecha'])[:10]}<br>"
            f"🤝 {row['contraparte']}<br>"
            f"⏱️ {row['duracion_dias']} días"
        )
        for _, row in df.iterrows()
    ]

    fig.add_trace(go.Scattergeo(
        lat=df["latitud"].tolist(),
        lon=df["longitud"].tolist(),
        mode="markers",
        marker=dict(
            size=tamanos,
            color=colores,
            line=dict(color="white", width=2),
            opacity=0.95,
        ),
        text=tooltips,
        customdata=list(range(len(df))),
        hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    ))

    # ── Layout del globo — estilo vista satélite ──────────────────────────────
    fig.update_layout(
        geo=dict(
            projection_type="orthographic",
            projection_rotation=dict(lon=15, lat=20, roll=0),
            # Tierra: tonos naturales verdes/marrones como vista satelital
            showland=True,
            landcolor="#4a7a52",        # verde natural / vegetación
            # Océano: azul profundo oceánico
            showocean=True,
            oceancolor="#1a3f6f",       # azul océano profundo
            # Bordes de país sutiles
            showcountries=True,
            countrycolor="rgba(255,255,255,0.30)",
            countrywidth=0.6,
            # Costlines con blanco para resaltar
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.80)",
            coastlinewidth=1.4,
            # Lagos en el mismo tono del océano
            showlakes=True,
            lakecolor="#1a3f6f",
            showrivers=False,
            showframe=False,
            bgcolor="rgba(0,0,0,0)",
            lataxis=dict(showgrid=False),
            lonaxis=dict(showgrid=False),
        ),
        # Fondo oscuro tipo espacio exterior alrededor del globo
        paper_bgcolor="#0a0a14",
        plot_bgcolor="#0a0a14",
        margin=dict(l=0, r=0, t=0, b=0),
        height=560,
        dragmode="zoom",
    )

    return fig


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el globo 3D y captura el clic del usuario.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        pd.Series | None: Fila del DataFrame clickeada, o None.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    fig = construir_globo(df)

    evento = st.plotly_chart(
        fig,
        use_container_width=True,
        key="mapa_globo",
        on_select="rerun",
        selection_mode="points",
    )

    puntos = (
        evento.selection.points
        if evento and hasattr(evento, "selection") and evento.selection
        else []
    )

    if puntos:
        point_idx = puntos[0].get("point_index", -1)
        ultimo    = st.session_state.get("_ultimo_clic_mapa")

        if point_idx != ultimo:
            st.session_state["_ultimo_clic_mapa"] = point_idx
            if 0 <= point_idx < len(df):
                return df.iloc[point_idx]

    return None
