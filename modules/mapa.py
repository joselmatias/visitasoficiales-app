"""
mapa.py — Globo 3D satelital con globe.gl (Three.js via CDN, gratuito)
Textura NASA Blue Marble + rotación horizontal automática
Selección de visita mediante botones nativos Streamlit debajo del globo
"""

import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Paleta de colores por tipo de actividad
COLORES_ACTIVIDAD = {
    "Firma de Convenio":         "#00E5CC",
    "Conferencia Internacional":  "#C77DFF",
    "Visita Técnica":            "#FFD166",
    "Reunión Bilateral":         "#FFEF5E",
    "Foro / Cumbre":             "#FF6B9D",
    "Visita Oficial":            "#4FC3F7",
}


def _html_globo(puntos_json: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ margin:0; background:#0a0a14; overflow:hidden; }}
    #g   {{ width:100%; height:520px; }}
  </style>
</head>
<body>
  <div id="g"></div>
  <script src="https://unpkg.com/globe.gl/dist/globe.gl.min.js"></script>
  <script>
    const pts = {puntos_json};

    const world = Globe({{ animateIn: false }})
      .globeImageUrl(
        'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
      .bumpImageUrl(
        'https://unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundColor('#0a0a14')
      .pointsData(pts)
      .pointLat('lat')
      .pointLng('lon')
      .pointColor('color')
      .pointRadius(0.55)
      .pointAltitude(0.06)
      .pointLabel(p =>
        `<div style="background:rgba(0,0,0,.75);color:#fff;padding:7px 10px;
                     border-radius:6px;font:13px/1.5 sans-serif;">
           <b>${{p.pais}} — ${{p.ciudad}}</b><br>
           <span style="color:${{p.color}}">■</span> ${{p.tipo}}<br>
           📅 ${{p.fecha}} &nbsp;⏱️ ${{p.dias}} días
         </div>`)
      (document.getElementById('g'));

    // Rotación horizontal automática (solo eje Y)
    world.controls().autoRotate      = true;
    world.controls().autoRotateSpeed = 0.7;
    world.controls().enableZoom      = true;
  </script>
</body>
</html>"""


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el globo 3D satelital y retorna la fila seleccionada (o None).

    Parámetros:
        df (pd.DataFrame): DataFrame filtrado con las visitas.

    Retorna:
        pd.Series | None: Fila del DataFrame seleccionada, o None.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    # Preparar datos para globe.gl
    puntos = [
        {
            "lat":   float(row["latitud"]),
            "lon":   float(row["longitud"]),
            "color": COLORES_ACTIVIDAD.get(str(row["tipo_actividad"]), "#FFFFFF"),
            "pais":  str(row["pais"]),
            "ciudad":str(row["ciudad"]),
            "tipo":  str(row["tipo_actividad"]),
            "fecha": str(row["fecha"])[:10],
            "dias":  int(row["duracion_dias"]),
        }
        for _, row in df.iterrows()
    ]

    # Renderizar globo satelital
    components.html(_html_globo(json.dumps(puntos)), height=528, scrolling=False)

    # ── Botones de selección de visita ────────────────────────────────────────
    st.caption("👆 Pasa el cursor sobre un marcador para ver el tooltip · "
               "Haz clic en un botón para ver el detalle completo:")

    cols = st.columns(len(df))
    for col, (_, row) in zip(cols, df.iterrows()):
        color = COLORES_ACTIVIDAD.get(str(row["tipo_actividad"]), "#FFFFFF")
        etiqueta = f"{row['pais']} — {row['ciudad']}"
        with col:
            st.markdown(
                f"<div style='text-align:center;margin-bottom:2px;"
                f"font-size:11px;color:{color};'>■ {row['tipo_actividad']}</div>",
                unsafe_allow_html=True,
            )
            if st.button(etiqueta, key=f"btn_v_{int(row['id'])}", use_container_width=True):
                return row

    return None
