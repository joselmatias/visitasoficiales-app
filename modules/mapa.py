"""
mapa.py — Globo 3D interactivo con Plotly (proyección ortográfica)
Estilo vista satélite: océanos azul profundo + tierra en tonos naturales
Animación horizontal (rotación lon) con botones ▶ / ⏸
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

# Configuración de la animación
_LON_INICIO  = 15    # longitud inicial del centro del globo
_PASO_GRADOS = 4     # grados por frame
_N_ROTACIONES = 10   # número de vueltas completas antes de detenerse
_MS_POR_FRAME = 55   # velocidad: menor = más rápido


def _construir_frames() -> list[go.Frame]:
    """Genera los frames de rotación horizontal (solo lon varía, lat fija en 20°)."""
    total = _N_ROTACIONES * (360 // _PASO_GRADOS)
    frames = []
    for i in range(total):
        lon = (_LON_INICIO + i * _PASO_GRADOS) % 360
        if lon > 180:
            lon -= 360
        frames.append(
            go.Frame(
                layout=dict(
                    geo=dict(projection_rotation=dict(lon=lon, lat=20, roll=0))
                ),
                name=str(i),
            )
        )
    return frames


def construir_globo(df: pd.DataFrame) -> go.Figure:
    """
    Construye el globo 3D con proyección ortográfica estilo vista satélite
    y animación de rotación horizontal.

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

    # ── Frames de animación horizontal ───────────────────────────────────────
    fig.frames = _construir_frames()

    # ── Layout del globo — estilo vista satélite ──────────────────────────────
    fig.update_layout(
        geo=dict(
            projection_type="orthographic",
            projection_rotation=dict(lon=_LON_INICIO, lat=20, roll=0),
            showland=True,
            landcolor="#4a7a52",
            showocean=True,
            oceancolor="#1a3f6f",
            showcountries=True,
            countrycolor="rgba(255,255,255,0.30)",
            countrywidth=0.6,
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.80)",
            coastlinewidth=1.4,
            showlakes=True,
            lakecolor="#1a3f6f",
            showrivers=False,
            showframe=False,
            bgcolor="rgba(0,0,0,0)",
            lataxis=dict(showgrid=False),
            lonaxis=dict(showgrid=False),
        ),
        paper_bgcolor="#0a0a14",
        plot_bgcolor="#0a0a14",
        margin=dict(l=0, r=0, t=0, b=48),
        height=580,
        dragmode="zoom",
        # ── Botones ▶ / ⏸ ────────────────────────────────────────────────────
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.5,
                y=-0.04,
                xanchor="center",
                yanchor="top",
                bgcolor="rgba(20,30,55,0.85)",
                bordercolor="rgba(255,255,255,0.25)",
                borderwidth=1,
                font=dict(color="white", size=14),
                buttons=[
                    dict(
                        label="▶  Girar",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=_MS_POR_FRAME, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=0),
                                mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="⏸  Pausa",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
            )
        ],
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
