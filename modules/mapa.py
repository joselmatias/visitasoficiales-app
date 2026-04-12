"""
mapa.py — Globo 3D satelital con globe.gl (Three.js via CDN, gratuito)
Textura NASA Blue Marble + rotación horizontal automática
Etiquetas fijas con nombre de ciudad + panel de info al hacer clic
Selección de detalle completo mediante botones Streamlit debajo del globo
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
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0a0a14; overflow: hidden; font-family: sans-serif; }}
  #g   {{ width: 100vw; height: 520px; }}

  /* Panel de info al seleccionar ciudad */
  #info {{
    display: none;
    position: absolute;
    bottom: 18px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(8, 12, 30, 0.88);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 10px;
    padding: 12px 18px;
    color: #fff;
    min-width: 220px;
    max-width: 320px;
    text-align: center;
    backdrop-filter: blur(6px);
    pointer-events: none;
  }}
  #info .ciudad  {{ font-size: 15px; font-weight: 700; margin-bottom: 4px; }}
  #info .tipo    {{ font-size: 12px; margin-bottom: 6px; }}
  #info .meta    {{ font-size: 12px; color: #ccc; line-height: 1.6; }}
  #info .cerrar  {{
    pointer-events: all;
    cursor: pointer;
    font-size: 11px;
    color: #aaa;
    margin-top: 6px;
    display: inline-block;
  }}
</style>
</head>
<body>
<div id="g"></div>
<div id="info">
  <div class="ciudad" id="i-ciudad"></div>
  <div class="tipo"   id="i-tipo"></div>
  <div class="meta"   id="i-meta"></div>
  <span class="cerrar" onclick="document.getElementById('info').style.display='none'">✕ cerrar</span>
</div>

<script src="https://unpkg.com/globe.gl/dist/globe.gl.min.js"></script>
<script>
  const pts = {puntos_json};

  function mostrarInfo(p) {{
    document.getElementById('i-ciudad').innerHTML =
      p.pais + ' &mdash; ' + p.ciudad;
    document.getElementById('i-tipo').innerHTML =
      '<span style="color:' + p.color + '">■</span> ' + p.tipo;
    document.getElementById('i-meta').innerHTML =
      '📅 ' + p.fecha + '<br>⏱️ ' + p.dias + ' días';
    document.getElementById('info').style.display = 'block';
  }}

  const world = Globe({{ animateIn: false }})
    .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
    .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
    .backgroundColor('#0a0a14')

    // Marcadores de puntos
    .pointsData(pts)
    .pointLat('lat')
    .pointLng('lon')
    .pointColor('color')
    .pointRadius(0.45)
    .pointAltitude(0.05)
    .onPointClick(p => mostrarInfo(p))

    // Etiquetas fijas con nombre de ciudad
    .labelsData(pts)
    .labelLat('lat')
    .labelLng('lon')
    .labelText('ciudad')
    .labelSize(1.4)
    .labelDotRadius(0.35)
    .labelDotOrientation(() => 'bottom')
    .labelColor(p => p.color)
    .labelResolution(3)
    .onLabelClick(p => mostrarInfo(p))

    (document.getElementById('g'));

  // Rotación horizontal automática
  world.controls().autoRotate      = true;
  world.controls().autoRotateSpeed = 0.7;
  world.controls().enableZoom      = true;

  // Pausar rotación al interactuar, reanudar al soltar
  const ctrl = world.controls();
  document.getElementById('g').addEventListener('mousedown', () => ctrl.autoRotate = false);
  document.addEventListener('mouseup', () => ctrl.autoRotate = true);
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

    # Globo satelital
    components.html(_html_globo(json.dumps(puntos)), height=528, scrolling=False)

    # Botones para abrir el panel de detalle completo (foto + descripción)
    st.caption("Haz clic en el globo para ver fecha y actividad · "
               "Usa los botones para el detalle completo:")
    cols = st.columns(len(df))
    for col, (_, row) in zip(cols, df.iterrows()):
        color = COLORES_ACTIVIDAD.get(str(row["tipo_actividad"]), "#FFFFFF")
        with col:
            st.markdown(
                f"<div style='text-align:center;margin-bottom:3px;"
                f"font-size:11px;color:{color};'>■ {row['tipo_actividad']}</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"{row['pais']} — {row['ciudad']}",
                key=f"btn_v_{int(row['id'])}",
                use_container_width=True,
            ):
                return row

    return None
