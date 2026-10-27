import warnings
from typing import IO

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import f as distribucion_f

from utils.anova_utils import (
	ajustar_dca,
	cargar_datos,
	coeficiente_variacion,
	interpretar_dca,
	resumen_tratamientos,
	tabla_anova,
	tukey,
	validar_dca,
)


@st.cache_data(show_spinner=False)
def cargar_archivo(archivo: IO[bytes] | None = None) -> pd.DataFrame:
	"""Carga el archivo seleccionado o los datos de ejemplo del DCA.

	Args:
		archivo: Archivo CSV o XLSX cargado desde la interfaz, si existe.

	Returns:
		Datos experimentales en un DataFrame.
	"""
	if archivo is None:
		return cargar_datos("data/dca_secadores.csv")
	return cargar_datos(archivo)


st.title("DCA | Diseño completamente al azar")
st.write(
	"El diseño completamente al azar compara tratamientos asignados al azar a "
	"unidades experimentales homogéneas. En este ejemplo se comparan cuatro "
	"secadores solares midiendo la humedad final de porciones de yuca."
)

archivo = st.file_uploader(
	"Carga los datos del ensayo",
	type=["csv", "xlsx"],
)

try:
	datos = cargar_archivo(archivo)
except Exception as error:
	st.error(f"No se pudo leer el archivo: {error}")
	st.stop()

if archivo is None:
	st.caption("No se cargó un archivo; se usan los datos de ejemplo de los cuatro secadores solares.")

columnas = list(datos.columns)
if not columnas:
	st.error("El archivo no contiene columnas para analizar.")
	st.stop()

columnas_categoricas = [
	columna
	for columna in columnas
	if not pd.api.types.is_numeric_dtype(datos[columna])
]
columnas_numericas = [
	columna
	for columna in columnas
	if pd.api.types.is_numeric_dtype(datos[columna])
]
tratamiento_inicial = columnas_categoricas[0] if columnas_categoricas else columnas[0]
respuesta_inicial = columnas_numericas[0] if columnas_numericas else columnas[-1]

columna_tratamiento = st.selectbox(
	"Columna de tratamiento",
	columnas,
	index=columnas.index(tratamiento_inicial),
)
columna_respuesta = st.selectbox(
	"Columna de respuesta",
	columnas,
	index=columnas.index(respuesta_inicial),
)
alfa = st.slider(
	"Nivel de significancia (alfa)",
	min_value=0.01,
	max_value=0.10,
	value=0.05,
	step=0.01,
	format="%.2f",
)

if columna_tratamiento == columna_respuesta:
	st.error("Selecciona columnas diferentes para tratamiento y respuesta.")
	st.stop()

errores = validar_dca(datos, columna_tratamiento, columna_respuesta)
if errores:
	for mensaje in errores:
		st.error(mensaje)
	st.stop()

# Se normaliza la respuesta numérica antes de que los modelos estadísticos la utilicen.
datos[columna_respuesta] = pd.to_numeric(datos[columna_respuesta], errors="raise")

modelo = ajustar_dca(datos, columna_tratamiento, columna_respuesta)
tabla = tabla_anova(modelo)
resumen = resumen_tratamientos(datos, columna_tratamiento, columna_respuesta)
cv = coeficiente_variacion(modelo, datos, columna_respuesta)
p_valor = float(tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"].iloc[0])
gl_tratamientos = int(tabla.loc[tabla["Fuente"] == "Tratamientos", "gl"].iloc[0])
gl_error = int(tabla.loc[tabla["Fuente"] == "Error", "gl"].iloc[0])

# La F crítica separa la región de rechazo usando los grados de libertad del ANOVA.
f_critica = float(distribucion_f.ppf(1 - alfa, gl_tratamientos, gl_error))

pestanas = st.tabs(["Datos", "ANOVA", "Comparaciones", "Gráficos"])

with pestanas[0]:
	st.subheader("Datos del ensayo")
	st.dataframe(datos, hide_index=True, width="stretch")
	st.subheader("Resumen por tratamiento")
	st.dataframe(resumen, hide_index=True, width="stretch")

with pestanas[1]:
	st.subheader("Análisis de varianza")
	formato_anova = {
		columna: "{:.4f}"
		for columna in ("SC", "CM", "F", "p-valor")
	}
	st.dataframe(
		tabla.style.format(formato_anova, na_rep="—"),
		hide_index=True,
		width="stretch",
	)
	columna_f, columna_cv = st.columns(2)
	columna_f.metric("F crítica", f"{f_critica:.4f}")
	columna_cv.metric("Coeficiente de variación", f"{cv:.4f}%")

	interpretacion = interpretar_dca(tabla, alfa)
	if p_valor < alfa:
		st.success(interpretacion)
	else:
		st.info(interpretacion)

with pestanas[2]:
	st.subheader("Comparaciones múltiples de Tukey")
	if p_valor < alfa:
		with warnings.catch_warnings(record=True) as advertencias:
			warnings.simplefilter("always", UserWarning)
			comparaciones, dms = tukey(
				datos,
				columna_tratamiento,
				columna_respuesta,
				alfa,
			)
		for advertencia in advertencias:
			st.warning(str(advertencia.message))

		formato_tukey = {
			columna: "{:.4f}"
			for columna in (
				"Diferencia de medias",
				"p-valor ajustado",
				"Límite inferior",
				"Límite superior",
			)
			if columna in comparaciones.columns
		}
		st.dataframe(
			comparaciones.style.format(formato_tukey),
			hide_index=True,
			width="stretch",
		)
		st.metric("Diferencia mínima significativa (DMS)", f"{dms:.4f}")
	else:
		st.info(
			"No se realiza Tukey porque el ANOVA no detectó diferencias "
			"estadísticamente significativas entre tratamientos para el alfa elegido."
		)

with pestanas[3]:
	st.subheader("Respuesta por tratamiento")
	grafico_cajas = px.box(
		datos,
		x=columna_tratamiento,
		y=columna_respuesta,
		color=columna_tratamiento,
		points="all",
		labels={
			columna_tratamiento: "Tratamiento",
			columna_respuesta: columna_respuesta,
		},
		title="Distribución de la respuesta por tratamiento",
	)
	grafico_cajas.update_layout(showlegend=False)
	st.plotly_chart(grafico_cajas, width="stretch")

	st.subheader("Media por tratamiento")
	grafico_medias = px.bar(
		resumen,
		x="Tratamiento",
		y="Media",
		error_y="Desviación estándar",
		labels={
			"Tratamiento": "Tratamiento",
			"Media": f"Media de {columna_respuesta}",
			"Desviación estándar": "Desviación estándar",
		},
		title="Media y desviación estándar por tratamiento",
	)
	st.plotly_chart(grafico_medias, width="stretch")