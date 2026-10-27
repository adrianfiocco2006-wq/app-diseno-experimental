AUTOR = "Escribe aquí tu nombre"

import streamlit as st

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("App de Diseño Experimental")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite planear ensayos de campo de forma ordenada, "
    "comparar tratamientos y distinguir sus efectos de la variabilidad natural. "
    "Así, las decisiones sobre cultivos y prácticas agrícolas se apoyan en datos "
    "y en conclusiones que pueden evaluarse."
)

st.header("Módulos")
st.dataframe(
    [
        {
            "Módulo": "DCA | Diseño completamente al azar",
            "Cuándo se usa": "Cuando las unidades experimentales son homogéneas y los tratamientos se asignan al azar.",
            "Ejemplo agrícola": "Comparar cuatro secadores usando porciones de yuca de humedad inicial similar.",
            "Estado": "Disponible",
        },
        {
            "Módulo": "DBCA | Diseño de bloques completos al azar",
            "Cuándo se usa": "Cuando se puede agrupar las unidades en bloques homogéneos para controlar una fuente de variación.",
            "Ejemplo agrícola": "Comparar fertilizantes agrupando parcelas por gradiente de fertilidad del suelo.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DCL | Diseño de cuadrado latino",
            "Cuándo se usa": "Cuando se deben controlar dos fuentes de variación además del tratamiento.",
            "Ejemplo agrícola": "Evaluar variedades controlando gradientes de humedad y fertilidad en un lote.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DPD | Diseño de parcelas divididas",
            "Cuándo se usa": "Cuando se estudian factores con distinta facilidad o escala de aplicación.",
            "Ejemplo agrícola": "Evaluar riego en parcelas principales y variedades en subparcelas.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "Diseños factoriales",
            "Cuándo se usa": "Cuando interesa evaluar varios factores y sus interacciones en un mismo ensayo.",
            "Ejemplo agrícola": "Estudiar dosis de fertilizante y láminas de riego sobre el rendimiento del maíz.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "RSM | Metodología de superficie de respuesta",
            "Cuándo se usa": "Cuando se busca modelar y optimizar una respuesta en función de factores cuantitativos.",
            "Ejemplo agrícola": "Optimizar temperatura y tiempo de secado para reducir la humedad final de la yuca.",
            "Estado": "En construcción",
        },
    ],
    hide_index=True,
    use_container_width=True,
)

st.header("Cómo usar la app")
st.markdown(
    """
1. Elige un módulo en el menú lateral.
2. Carga los datos del ensayo en el formato solicitado.
3. Revisa los resultados y su interpretación.
4. Verifica los supuestos y compara con tu cálculo manual.
"""
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

with st.sidebar:
    st.header("Información académica")
    st.write(f"**Autor:** {AUTOR}")
    st.write("**Curso:** Diseño Experimental")
    st.write("**Semestre:** 2026-2")