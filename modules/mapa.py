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

# CartoDB Dark Matter — mapamundi oscuro con bordes de países visibles
TILE_DARK = (
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
)
TILE_DARK_ATTR = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
    'contributors &copy; <a href="https://carto.com/">CARTO</a>'
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


def _posiciones_marcadores(df: pd.DataFrame) -> dict:
    """
    Devuelve un dict {idx_fila: (lat_marcador, lon_marcador)} con las
    coordenadas reales de cada marcador en el mapa (incluye offsets circulares).
    Usa los mismos parámetros que construir_mapa para que coincidan exactamente.
    """
    posiciones = {}
    for (lat_base, lon_base), grupo in df.groupby(["latitud", "longitud"]):
        n = len(grupo)
        offsets = _offsets_circulares(n, radio=0.5)
        for (idx, _), (dlat, dlon) in zip(grupo.iterrows(), offsets):
            posiciones[idx] = (lat_base + dlat, lon_base + dlon)
    return posiciones


def construir_mapa(df: pd.DataFrame) -> folium.Map:
    """
    Construye el mapa Folium con fondo satélite, marcadores, trayectoria
    y controles interactivos (pantalla completa, minimap, coordenadas).

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        folium.Map: Objeto mapa listo para renderizar.
    """

    # ── Base del mapa — CartoDB Dark Matter (mapamundi oscuro) ───────────────
    mapa = folium.Map(
        location=[20, 10],
        zoom_start=2,
        tiles=TILE_DARK,
        attr=TILE_DARK_ATTR,
        control_scale=True,
    )

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

            # Tooltip flotante — incluye número de visita, país, ciudad y detalle
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
                <b style="font-size:15px;">#{idx_local + 1} &nbsp; 🌍 {fila['pais']} — {fila['ciudad']}</b><br>
                <span style="color:{color};">■</span>
                <b>{fila['tipo_actividad']}</b><br>
                📅 {str(fila['fecha'])[:10]}<br>
                🤝 {fila['contraparte']}<br>
                ⏱️ {fila['duracion_dias']} días
            </div>
            """

            # Marcador circular — ocupa toda el área clicable sin superposición
            folium.CircleMarker(
                location=[lat_m, lon_m],
                radius=radio_px,
                color="white",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.88,
                tooltip=folium.Tooltip(tooltip_html, sticky=True),
            ).add_to(mapa)

            # Número encima del círculo usando DivIcon overlay (no interactivo)
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
                        pointer-events: none;
                        user-select: none;
                    ">{idx_local + 1}</div>
                    """,
                    icon_size=(radio_px * 2, radio_px * 2),
                    icon_anchor=(radio_px, radio_px),
                ),
                interactive=False,
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
    minimap_tile = folium.TileLayer(
        tiles=TILE_DARK,
        attr=TILE_DARK_ATTR,
    )
    MiniMap(
        tile_layer=minimap_tile,
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

    # Detectar solo clics NUEVOS comparando con el último clic guardado
    clic = resultado.get("last_object_clicked") if resultado else None

    if clic and clic.get("lat") is not None:
        lat_c = round(clic["lat"], 5)
        lon_c = round(clic["lng"], 5)
        clic_key = (lat_c, lon_c)

        # Recuperar el último clic registrado
        ultimo = st.session_state.get("_ultimo_clic_mapa")
        ultimo_key = (
            round(ultimo["lat"], 5),
            round(ultimo["lng"], 5),
        ) if ultimo else None

        # Solo procesar si las coordenadas son distintas al clic anterior
        if clic_key != ultimo_key:
            st.session_state["_ultimo_clic_mapa"] = clic

            # Usar posiciones reales de los marcadores (con offsets circulares)
            # para identificar cuál fue clickeado. Sin esto, todos los marcadores
            # de una misma ciudad comparten la misma lat/lon base y solo responde uno.
            posiciones = _posiciones_marcadores(df)
            df_tmp = df.copy()
            df_tmp["_lat_m"] = df_tmp.index.map(lambda i: posiciones[i][0])
            df_tmp["_lon_m"] = df_tmp.index.map(lambda i: posiciones[i][1])
            df_tmp["_dist"] = (
                (df_tmp["_lat_m"] - lat_c) ** 2 +
                (df_tmp["_lon_m"] - lon_c) ** 2
            ) ** 0.5

            cercano = df_tmp[df_tmp["_dist"] < 1.0]
            if not cercano.empty:
                return cercano.loc[cercano["_dist"].idxmin()].drop(
                    columns=["_lat_m", "_lon_m", "_dist"]
                )

    return None
