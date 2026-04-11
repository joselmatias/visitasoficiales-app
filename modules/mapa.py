"""
mapa.py — Mapa interactivo con vista satélite tipo Google Earth
Usa Scattermapbox con tiles ESRI World Imagery (gratuito, sin API key)
Captura clics con st.plotly_chart on_select nativo de Streamlit >= 1.38
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Paleta fija de colores por tipo de actividad
COLORES_ACTIVIDAD = {
    "Firma de Convenio":        "#00E5CC",
    "Conferencia Internacional": "#C77DFF",
    "Visita Técnica":           "#FFD166",
    "Reunión Bilateral":        "#FFEF5E",
    "Foro / Cumbre":            "#FF6B9D",
    "Visita Oficial":           "#4FC3F7",
}

# Tiles ESRI World Imagery — satélite gratuito sin token
TILE_SATELITE = (
    "https://server.arcgisonline.com/ArcGIS/rest/"
    "services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

# Tiles ESRI etiquetas de países encima del satélite
TILE_LABELS = (
    "https://services.arcgisonline.com/ArcGIS/rest/"
    "services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
)


def construir_mapa(df: pd.DataFrame) -> go.Figure:
    """
    Construye la figura Scattermapbox sobre fondo satélite ESRI.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        go.Figure: Figura completa lista para renderizar.
    """
    fig = go.Figure()

    # --- Un trace por visita para identificar el clic exacto ---
    for _, fila in df.iterrows():
        color = COLORES_ACTIVIDAD.get(fila["tipo_actividad"], "#FFFFFF")
        fig.add_trace(
            go.Scattermapbox(
                lat=[fila["latitud"]],
                lon=[fila["longitud"]],
                mode="markers",
                marker=dict(
                    size=max(14, int(fila["duracion_dias"]) * 4),
                    color=color,
                    opacity=0.92,
                ),
                text=fila["pais"],
                customdata=[[fila["id"]]],
                hovertemplate=(
                    f"<b>🌍 {fila['pais']} — {fila['ciudad']}</b><br>"
                    f"📅 {fila['fecha']}<br>"
                    f"🏷️ {fila['tipo_actividad']}<br>"
                    f"🤝 {fila['contraparte']}<br>"
                    f"⏱️ {fila['duracion_dias']} días"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # --- Leyenda visual por tipo (traces vacíos) ---
    tipos_vistos = set()
    for _, fila in df.iterrows():
        tipo = fila["tipo_actividad"]
        if tipo not in tipos_vistos:
            tipos_vistos.add(tipo)
            fig.add_trace(
                go.Scattermapbox(
                    lat=[None], lon=[None],
                    mode="markers",
                    marker=dict(size=10, color=COLORES_ACTIVIDAD.get(tipo, "#FFF")),
                    name=tipo,
                    showlegend=True,
                )
            )

    # --- Línea de trayectoria cronológica ---
    df_ord = df.sort_values("fecha")
    fig.add_trace(
        go.Scattermapbox(
            lat=df_ord["latitud"].tolist(),
            lon=df_ord["longitud"].tolist(),
            mode="lines",
            line=dict(width=2, color="white"),
            opacity=0.35,
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # --- Layout con fondo satélite ESRI + capa de etiquetas ---
    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox=dict(
            style="white-bg",
            zoom=1.4,
            center=dict(lat=25, lon=10),
            layers=[
                # Capa 1: Imágenes satélite
                dict(
                    below="traces",
                    sourcetype="raster",
                    sourceattribution="ESRI World Imagery",
                    source=[TILE_SATELITE],
                ),
                # Capa 2: Nombres de países y fronteras encima del satélite
                dict(
                    below="",
                    sourcetype="raster",
                    sourceattribution="ESRI Reference",
                    source=[TILE_LABELS],
                    opacity=0.7,
                ),
            ],
        ),
        legend=dict(
            title=dict(text="Tipo de Actividad", font=dict(color="white", size=12)),
            bgcolor="rgba(0,0,0,0.6)",
            bordercolor="rgba(255,255,255,0.25)",
            borderwidth=1,
            font=dict(color="white", size=11),
            x=0.01,
            y=0.99,
        ),
        paper_bgcolor="black",
    )

    return fig


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el mapa satélite y captura el clic sobre un marcador.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        pd.Series | None: Fila del DataFrame clickeada, o None.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    fig = construir_mapa(df)

    evento = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        key="mapa_visitas",
    )

    # Procesar clic — los primeros len(df) traces son los marcadores individuales
    if evento and evento.selection and evento.selection.points:
        punto = evento.selection.points[0]
        curva_idx = punto.get("curve_number", None)
        if curva_idx is not None and curva_idx < len(df):
            df_reset = df.reset_index(drop=True)
            return df_reset.iloc[curva_idx]

    return None
