"""
mapa.py — Mapa interactivo tipo Google Earth con Folium
Satélite ESRI + zoom suave + pantalla completa + minimap + trayectoria
Captura clics via st_folium para identificar la visita seleccionada
"""

import math
import pandas as pd
import folium
from folium.plugins import Fullscreen, MiniMap, MousePosition
import streamlit as st
from streamlit_folium import st_folium

# Paleta de colores por tipo de actividad
COLORES_ACTIVIDAD = {
    "Firma de Convenio":        "#00E5CC",
    "Conferencia Internacional": "#C77DFF",
    "Visita Técnica":           "#FFD166",
    "Reunión Bilateral":        "#FFEF5E",
    "Foro / Cumbre":            "#FF6B9D",
    "Visita Oficial":           "#4FC3F7",
}

# URL tiles satélite ESRI (gratuito, sin API key)
TILE_SATELITE = (
    "https://server.arcgisonline.com/ArcGIS/rest/"
    "services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
# URL tiles etiquetas/fronteras sobre el satélite
TILE_LABELS = (
    "https://services.arcgisonline.com/ArcGIS/rest/"
    "services/Reference/World_Boundaries_and_Places/"
    "MapServer/tile/{z}/{y}/{x}"
)


def _offsets_circulares(n: int, radio: float = 0.8) -> list[tuple]:
    """
    Genera n posiciones en círculo para separar marcadores en la misma ciudad.
    Radio en grados (~80 km) — suficiente para verlos distintos al hacer zoom.
    """
    if n == 1:
        return [(0.0, 0.0)]
    angulos = [2 * math.pi * i / n for i in range(n)]
    return [(radio * math.sin(a), radio * math.cos(a)) for a in angulos]


def construir_mapa(df: pd.DataFrame) -> folium.Map:
    """
    Construye el mapa Folium con fondo satélite, marcadores, trayectoria
    y controles interactivos (pantalla completa, minimap, coordenadas).

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        folium.Map: Objeto mapa listo para renderizar.
    """

    # ── Base del mapa ─────────────────────────────────────────────────────────
    mapa = folium.Map(
        location=[20, 10],
        zoom_start=2,
        tiles=None,                  # Sin tiles por defecto
        control_scale=True,          # Escala de distancia
    )

    # ── Capa 1: Satélite ESRI ─────────────────────────────────────────────────
    folium.TileLayer(
        tiles=TILE_SATELITE,
        attr="Esri World Imagery",
        name="🛰️ Satélite",
        overlay=False,
        control=True,
    ).add_to(mapa)

    # ── Capa 2: Etiquetas de países (overlay transparente) ────────────────────
    folium.TileLayer(
        tiles=TILE_LABELS,
        attr="Esri Reference",
        name="🏷️ Etiquetas",
        overlay=True,
        control=True,
        opacity=0.85,
    ).add_to(mapa)

    # ── Capa 3: OpenStreetMap como alternativa ─────────────────────────────────
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺️ Mapa Callejero",
        overlay=False,
        control=True,
    ).add_to(mapa)

    # ── Línea de trayectoria cronológica ──────────────────────────────────────
    df_ord = df.sort_values("fecha")
    coords_linea = df_ord[["latitud", "longitud"]].values.tolist()

    if len(coords_linea) > 1:
        folium.PolyLine(
            locations=coords_linea,
            color="white",
            weight=2,
            opacity=0.4,
            dash_array="8 6",
            tooltip="Trayectoria cronológica",
        ).add_to(mapa)

        # Flechas de dirección en la línea
        for i in range(len(coords_linea) - 1):
            mid_lat = (coords_linea[i][0] + coords_linea[i+1][0]) / 2
            mid_lon = (coords_linea[i][1] + coords_linea[i+1][1]) / 2
            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.DivIcon(
                    html='<div style="font-size:14px;color:white;opacity:0.6;">➤</div>',
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                ),
            ).add_to(mapa)

    # ── Marcadores por visita (separados si comparten ubicación) ──────────────
    # Agrupar por ciudad para calcular offsets
    grupos = df.groupby(["latitud", "longitud"])

    for (lat_base, lon_base), grupo in grupos:
        n = len(grupo)
        offsets = _offsets_circulares(n, radio=0.5)

        for idx_local, ((_, fila), (dlat, dlon)) in enumerate(
            zip(grupo.iterrows(), offsets)
        ):
            color = COLORES_ACTIVIDAD.get(fila["tipo_actividad"], "#FFFFFF")
            lat_m = lat_base + dlat
            lon_m = lon_base + dlon
            radio_px = max(12, int(fila["duracion_dias"]) * 3)

            # Tooltip flotante al pasar el cursor
            tooltip_html = f"""
            <div style="
                font-family: Arial, sans-serif;
                font-size: 13px;
                background: rgba(0,0,0,0.85);
                color: white;
                padding: 8px 12px;
                border-radius: 8px;
                border-left: 4px solid {color};
                min-width: 220px;
            ">
                <b style="font-size:15px;">🌍 {fila['pais']} — {fila['ciudad']}</b><br>
                <span style="color:{color};">■</span>
                <b>{fila['tipo_actividad']}</b><br>
                📅 {str(fila['fecha'])[:10]}<br>
                🤝 {fila['contraparte']}<br>
                ⏱️ {fila['duracion_dias']} días
            </div>
            """

            # Marcador circular estilizado
            folium.CircleMarker(
                location=[lat_m, lon_m],
                radius=radio_px,
                color="white",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.88,
                tooltip=folium.Tooltip(
                    tooltip_html,
                    sticky=True,
                ),
            ).add_to(mapa)

            # Número de visita en el centro del marcador
            folium.Marker(
                location=[lat_m, lon_m],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: 11px;
                        font-weight: bold;
                        color: black;
                        text-align: center;
                        line-height: {radio_px * 2}px;
                        width: {radio_px * 2}px;
                        height: {radio_px * 2}px;
                        margin-top: -{radio_px}px;
                        margin-left: -{radio_px}px;
                    ">{idx_local + 1}</div>
                    """,
                    icon_size=(radio_px * 2, radio_px * 2),
                    icon_anchor=(radio_px, radio_px),
                ),
            ).add_to(mapa)

    # ── Plugins interactivos ──────────────────────────────────────────────────
    # Pantalla completa
    Fullscreen(
        position="topright",
        title="Pantalla completa",
        title_cancel="Salir",
        force_separate_button=True,
    ).add_to(mapa)

    # Minimapa de referencia
    MiniMap(
        tile_layer=TILE_SATELITE,
        position="bottomright",
        width=160,
        height=120,
        collapsed_width=25,
        collapsed_height=25,
        zoom_level_offset=-5,
        toggle_display=True,
    ).add_to(mapa)

    # Coordenadas del cursor
    MousePosition(
        position="bottomleft",
        separator=" | ",
        prefix="Lat/Lon:",
    ).add_to(mapa)

    # Control de capas (satélite / callejero / etiquetas)
    folium.LayerControl(position="topright", collapsed=False).add_to(mapa)

    return mapa


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el mapa Folium y captura el clic del usuario.
    Identifica la visita más cercana al punto clickeado.

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        pd.Series | None: Fila del DataFrame clickeada, o None.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    mapa = construir_mapa(df)

    resultado = st_folium(
        mapa,
        use_container_width=True,
        height=560,
        key="mapa_folium",
        returned_objects=["last_object_clicked"],
    )

    # Detectar clic y buscar la visita más cercana
    clic = resultado.get("last_object_clicked") if resultado else None
    if clic and clic.get("lat") is not None:
        lat_c = clic["lat"]
        lon_c = clic["lng"]

        # Calcular distancia euclidiana a cada visita y retornar la más cercana
        df_tmp = df.copy()
        df_tmp["_dist"] = (
            (df_tmp["latitud"] - lat_c) ** 2 +
            (df_tmp["longitud"] - lon_c) ** 2
        ) ** 0.5

        # Solo considerar clics dentro de un radio razonable (< 2 grados)
        cercano = df_tmp[df_tmp["_dist"] < 2.0]
        if not cercano.empty:
            return cercano.loc[cercano["_dist"].idxmin()].drop("_dist")

    return None
