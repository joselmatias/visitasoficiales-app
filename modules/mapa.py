"""
mapa.py — Módulo de mapa interactivo geoespacial
Renderiza el mapamundi con marcadores por visita y línea de trayectoria
Usa plotly.express y streamlit-plotly-events para captura de clics
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events

# Paleta fija de colores para cada tipo de actividad (máx. 6)
COLORES_ACTIVIDAD = {
    "Firma de Convenio":       "#00C9A7",
    "Conferencia Internacional": "#845EC2",
    "Visita Técnica":          "#FFC75F",
    "Reunión Bilateral":       "#F9F871",
    "Foro / Cumbre":           "#FF6F91",
    "Visita Oficial":          "#4FC3F7",
}


def construir_mapa(df: pd.DataFrame) -> go.Figure:
    """
    Construye la figura de Plotly con marcadores y línea de trayectoria.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas a graficar.

    Retorna:
        go.Figure: Figura completa lista para renderizar.
    """

    # Asignar color según tipo de actividad
    df = df.copy()
    df["color"] = df["tipo_actividad"].map(COLORES_ACTIVIDAD).fillna("#AAAAAA")

    # --- Capa de marcadores (scatter_geo) ---
    fig = px.scatter_geo(
        df,
        lat="latitud",
        lon="longitud",
        color="tipo_actividad",
        color_discrete_map=COLORES_ACTIVIDAD,
        size="duracion_dias",
        size_max=20,
        projection="natural earth",
        template="plotly_dark",
        hover_name="pais",
        hover_data={
            "ciudad": True,
            "fecha": True,
            "tipo_actividad": True,
            "contraparte": True,
            "latitud": False,
            "longitud": False,
            "duracion_dias": False,
        },
        custom_data=["id"],   # Guardamos el id para identificar la fila al hacer clic
        title="Mapa de Visitas Oficiales — Versión Prueba",
    )

    # --- Capa de línea de trayectoria cronológica ---
    df_ordenado = df.sort_values("fecha")
    fig.add_trace(
        go.Scattergeo(
            lat=df_ordenado["latitud"].tolist(),
            lon=df_ordenado["longitud"].tolist(),
            mode="lines",
            line=dict(
                width=1.5,
                color="white",
                dash="dot",
            ),
            opacity=0.3,
            showlegend=False,
            hoverinfo="skip",
            name="Trayectoria",
        )
    )

    # --- Ajustes de layout ---
    fig.update_layout(
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(
            title="Tipo de Actividad",
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1,
            font=dict(color="white"),
        ),
        geo=dict(
            showland=True,
            landcolor="rgb(40, 40, 60)",
            showocean=True,
            oceancolor="rgb(20, 30, 50)",
            showcountries=True,
            countrycolor="rgba(255,255,255,0.15)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.2)",
            bgcolor="rgb(17, 17, 34)",
        ),
        paper_bgcolor="rgb(17, 17, 34)",
        plot_bgcolor="rgb(17, 17, 34)",
        title_font=dict(color="white", size=16),
    )

    return fig


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el mapa en la interfaz de Streamlit y captura el evento de clic.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        pd.Series | None: La fila del DataFrame correspondiente al punto
                          clickeado, o None si no hubo clic.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    fig = construir_mapa(df)

    # Capturar evento de clic usando streamlit-plotly-events
    puntos_seleccionados = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=550,
        key="mapa_visitas",
    )

    # Procesar el clic si existe
    if puntos_seleccionados:
        punto = puntos_seleccionados[0]
        punto_idx = punto.get("pointIndex", None)
        curva_idx = punto.get("curveNumber", 0)

        # Solo procesar clics en la capa de marcadores (curveNumber 0..n-1 de scatter)
        # La línea de trayectoria es la última traza, la ignoramos
        if punto_idx is not None and curva_idx < len(df["tipo_actividad"].unique()):
            try:
                # Reconstruir el subset de puntos en el mismo orden que plotly los grafica
                # plotly agrupa por color (tipo_actividad), necesitamos mapear correctamente
                tipo_unico = df["tipo_actividad"].unique()
                if curva_idx < len(tipo_unico):
                    tipo_seleccionado = tipo_unico[curva_idx]
                    subset = df[df["tipo_actividad"] == tipo_seleccionado].reset_index(drop=True)
                    if punto_idx < len(subset):
                        fila = subset.iloc[punto_idx]
                        return fila
            except (IndexError, KeyError):
                pass

    return None
