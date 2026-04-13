"""
mapa.py — Globo 3D satelital con globe.gl (Three.js via CDN, gratuito)
Textura NASA Blue Marble + rotación horizontal automática
Etiquetas HTML nativas (htmlElementsData + decodeURIComponent) para tildes correctas
Clic en ciudad/marcador → navega con ?vid=X para abrir panel de detalle completo
"""

import json
from urllib.parse import quote
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
  <meta charset="UTF-8">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0a0a14; overflow: hidden; font-family: sans-serif; }}
    #g   {{ width: 100vw; height: 520px; }}
    .etiqueta {{
      font-size: 13px;
      font-weight: 700;
      text-shadow: 0 0 6px #000, 0 0 12px #000;
      pointer-events: auto;
      cursor: pointer;
      white-space: nowrap;
      padding: 2px 4px;
    }}
  </style>
</head>
<body>
  <div id="g"></div>
  <script src="https://unpkg.com/globe.gl/dist/globe.gl.min.js"></script>
  <script>
    const pts = {puntos_json};

    function abrirDetalle(p) {{
      const url = new URL(window.parent.location.href);
      url.searchParams.set('vid', p.id);
      window.parent.location.href = url.toString();
    }}

    const world = Globe({{ animateIn: false }})
      .globeImageUrl(
        'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
      .bumpImageUrl(
        'https://unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundColor('#0a0a14')

      // Marcadores de punto
      .pointsData(pts)
      .pointLat('lat')
      .pointLng('lon')
      .pointColor('color')
      .pointRadius(0.45)
      .pointAltitude(0.05)
      .onPointClick(p => abrirDetalle(p))

      // Etiquetas como elementos HTML reales — soporte nativo de tildes/Unicode
      .htmlElementsData(pts)
      .htmlLat('lat')
      .htmlLng('lon')
      .htmlAltitude(0.08)
      .htmlElement(d => {{
        const el = document.createElement('div');
        el.className = 'etiqueta';
        el.textContent = decodeURIComponent(d.ciudad);
        el.style.color = d.color;
        el.addEventListener('click', () => abrirDetalle(d));
        return el;
      }})

      (document.getElementById('g'));

    // Rotación horizontal automática
    world.controls().autoRotate      = true;
    world.controls().autoRotateSpeed = 0.7;
    world.controls().enableZoom      = true;

    // Pausa al arrastrar, reanuda al soltar
    const ctrl = world.controls();
    document.getElementById('g').addEventListener('mousedown',
      () => ctrl.autoRotate = false);
    document.addEventListener('mouseup',
      () => ctrl.autoRotate = true);
  </script>
</body>
</html>"""


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el globo 3D satelital.
    Los clics en el globo navegan con ?vid=X (manejado en app.py).
    Los botones debajo también permiten seleccionar visita.

    Retorna:
        pd.Series | None: Fila seleccionada via botón, o None.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    puntos = [
        {
            "id":    int(row["id"]),
            "lat":   float(row["latitud"]),
            "lon":   float(row["longitud"]),
            "color": COLORES_ACTIVIDAD.get(str(row["tipo_actividad"]), "#FFFFFF"),
            "pais":  str(row["pais"]),
            "ciudad": quote(str(row["ciudad"])),
            "tipo":  str(row["tipo_actividad"]),
            "fecha": str(row["fecha"])[:10],
            "dias":  int(row["duracion_dias"]),
        }
        for _, row in df.iterrows()
    ]

    components.html(
        _html_globo(json.dumps(puntos, ensure_ascii=False)),
        height=528,
        scrolling=False,
    )

    # Botones alternativos (no requieren recarga de página)
    st.caption("👆 Haz clic en una ciudad del globo · "
               "o usa los botones para ver el detalle:")
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
