"""
mapa.py — Módulo de mapa interactivo geoespacial
Renderiza el mapamundi con marcadores por visita y línea de trayectoria
Usa st.plotly_chart con on_select para captura de clics (compatible con Streamlit >= 1.38)
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Paleta fija de colores para cada tipo de actividad (máx. 6)
COLORES_ACTIVIDAD = {
    "Firma de Convenio":        "#00C9A7",
    "Conferencia Internacional": "#845EC2",
    "Visita Técnica":           "#FFC75F",
    "Reunión Bilateral":        "#F9F871",
    "Foro / Cumbre":            "#FF6F91",
    "Visita Oficial":           "#4FC3F7",
}


def construir_mapa(df: pd.DataFrame) -> go.Figure:
    """
    Construye la figura de Plotly con marcadores y línea de trayectoria.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas a graficar.

    Retorna:
        go.Figure: Figura completa lista para renderizar.
    """
    df = df.copy()

    # --- Capa de marcadores usando go.Figure directamente ---
    # (evita problemas de agrupación de px.scatter_geo con on_select)
    fig = go.Figure()

    # Agregar un trace por cada visita para identificar el índice exacto al hacer clic
    for _, fila in df.iterrows():
        color = COLORES_ACTIVIDAD.get(fila["tipo_actividad"], "#AAAAAA")
        fig.add_trace(
            go.Scattergeo(
                lat=[fila["latitud"]],
                lon=[fila["longitud"]],
                mode="markers",
                marker=dict(
                    size=max(10, fila["duracion_dias"] * 3),
                    color=color,
                    line=dict(width=1, color="white"),
                    opacity=0.9,
                ),
                name=fila["tipo_actividad"],
                text=fila["pais"],
                customdata=[[fila["id"]]],
                hovertemplate=(
                    f"<b>{fila['pais']}</b><br>"
                    f"Ciudad: {fila['ciudad']}<br>"
                    f"Fecha: {fila['fecha']}<br>"
                    f"Tipo: {fila['tipo_actividad']}<br>"
                    f"Contraparte: {fila['contraparte']}<br>"
                    f"Duración: {fila['duracion_dias']} días"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # --- Leyenda manual con un trace por tipo (sin duplicar marcadores) ---
    tipos_vistos = set()
    for _, fila in df.iterrows():
        tipo = fila["tipo_actividad"]
        if tipo not in tipos_vistos:
            tipos_vistos.add(tipo)
            color = COLORES_ACTIVIDAD.get(tipo, "#AAAAAA")
            fig.add_trace(
                go.Scattergeo(
                    lat=[None],
                    lon=[None],
                    mode="markers",
                    marker=dict(size=10, color=color),
                    name=tipo,
                    showlegend=True,
                )
            )

    # --- Línea de trayectoria cronológica ---
    df_ordenado = df.sort_values("fecha")
    fig.add_trace(
        go.Scattergeo(
            lat=df_ordenado["latitud"].tolist(),
            lon=df_ordenado["longitud"].tolist(),
            mode="lines",
            line=dict(width=1.5, color="white", dash="dot"),
            opacity=0.3,
            showlegend=False,
            hoverinfo="skip",
            name="Trayectoria",
        )
    )

    # --- Layout ---
    fig.update_layout(
        title=dict(
            text="Mapa de Visitas Oficiales — Versión Prueba",
            font=dict(color="white", size=16),
        ),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(
            title=dict(text="Tipo de Actividad", font=dict(color="white")),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1,
            font=dict(color="white"),
        ),
        geo=dict(
            projection_type="natural earth",
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
        template="plotly_dark",
    )

    return fig


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el mapa y captura clics usando st.plotly_chart con on_select.
    Compatible con Streamlit >= 1.38 sin dependencias externas.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        pd.Series | None: Fila del DataFrame del punto clickeado, o None.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    fig = construir_mapa(df)

    # Renderizar con soporte de selección nativo de Streamlit
    evento = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        key="mapa_visitas",
    )

    # Procesar el punto seleccionado
    if evento and evento.selection and evento.selection.points:
        punto = evento.selection.points[0]
        curva_idx = punto.get("curve_number", None)

        # Los primeros len(df) traces son los marcadores individuales (uno por visita)
        if curva_idx is not None and curva_idx < len(df):
            df_reset = df.reset_index(drop=True)
            fila = df_reset.iloc[curva_idx]
            return fila

    return None
