from pathlib import Path
from typing import IO
import warnings

import numpy as np
import pandas as pd
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def cargar_datos(archivo: str | Path | IO[bytes]) -> pd.DataFrame:
    """Lee datos experimentales desde un archivo CSV o Excel.

    Args:
        archivo: Ruta o archivo binario abierto con extensión `.csv` o `.xlsx`.

    Returns:
        Un DataFrame con los datos del archivo.

    Raises:
        ValueError: Si la extensión no corresponde a CSV o XLSX.
    """
    # Se identifica la extensión; los flujos sin nombre se interpretan como CSV.
    nombre = getattr(archivo, "name", None)
    if nombre is None:
        nombre = archivo if isinstance(archivo, (str, Path)) else ""
    extension = Path(str(nombre)).suffix.lower()

    # Excel conserva los tipos de celda; CSV detecta automáticamente coma o punto y coma.
    if extension == ".xlsx":
        return pd.read_excel(archivo)
    if extension in (".csv", ""):
        return pd.read_csv(archivo, sep=None, engine="python", encoding="utf-8-sig")

    raise ValueError("El archivo debe tener extensión .csv o .xlsx.")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Valida los datos requeridos para un diseño completamente al azar.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Mensajes en español para los errores encontrados; lista vacía si son válidos.
    """
    errores: list[str] = []

    # Se comprueba que las dos variables del modelo estén disponibles.
    if col_trat not in df.columns:
        errores.append(f"No se encontró la columna de tratamientos '{col_trat}'.")
    if col_resp not in df.columns:
        errores.append(f"No se encontró la columna de respuesta '{col_resp}'.")

    # Se revisan los faltantes solo en las columnas que requiere el DCA.
    columnas_presentes = [col for col in (col_trat, col_resp) if col in df.columns]
    if columnas_presentes and df[columnas_presentes].isna().any().any():
        errores.append("Hay datos faltantes en las columnas de tratamiento o respuesta.")

    # La respuesta debe poder convertirse a números para calcular medias y varianzas.
    if col_resp in df.columns:
        respuesta = pd.to_numeric(df[col_resp], errors="coerce")
        no_numericos = df[col_resp].notna() & respuesta.isna()
        if no_numericos.any():
            errores.append(f"La columna de respuesta '{col_resp}' debe ser numérica.")

    # Se verifica que haya al menos dos tratamientos y dos observaciones por tratamiento.
    if col_trat in df.columns:
        tratamientos = df[col_trat].dropna()
        if tratamientos.nunique() < 2:
            errores.append("El DCA requiere al menos dos tratamientos.")
        replicas = tratamientos.value_counts()
        pocos_datos = replicas[replicas < 2].index.tolist()
        if pocos_datos:
            nombres = ", ".join(str(tratamiento) for tratamiento in pocos_datos)
            errores.append(
                "Cada tratamiento debe tener al menos dos réplicas. "
                f"No cumplen: {nombres}."
            )

    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta el modelo lineal de un diseño completamente al azar.

    Args:
        df: Datos validados del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        El modelo OLS ajustado.

    Raises:
        ValueError: Si los datos no cumplen las condiciones mínimas del DCA.
    """
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede ajustar el DCA: " + " ".join(errores))

    # El modelo compara las medias: respuesta = media general + efecto del tratamiento + error.
    # Q() protege nombres de columna con espacios, tildes o caracteres especiales.
    formula = f"Q({col_resp!r}) ~ C(Q({col_trat!r}))"
    return ols(formula, data=df).fit()


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye la tabla ANOVA tipo II para el modelo DCA.

    Args:
        modelo: Modelo OLS ajustado con `ajustar_dca`.

    Returns:
        Tabla con las fuentes Tratamientos, Error y Total.
    """
    # ANOVA tipo II separa la variación explicada por tratamientos de la variación residual.
    anova = anova_lm(modelo, typ=2)
    fila_tratamientos = anova.drop(index="Residual").iloc[0]
    fila_error = anova.loc["Residual"]

    # Cada cuadrado medio se obtiene como SC/gl; el total suma tratamientos y error.
    gl_tratamientos = int(fila_tratamientos["df"])
    gl_error = int(fila_error["df"])
    sc_tratamientos = float(fila_tratamientos["sum_sq"])
    sc_error = float(fila_error["sum_sq"])
    gl_total = gl_tratamientos + gl_error
    sc_total = sc_tratamientos + sc_error

    return pd.DataFrame(
        [
            {
                "Fuente": "Tratamientos",
                "gl": gl_tratamientos,
                "SC": sc_tratamientos,
                "CM": sc_tratamientos / gl_tratamientos,
                "F": float(fila_tratamientos["F"]),
                "p-valor": float(fila_tratamientos["PR(>F)"]),
            },
            {
                "Fuente": "Error",
                "gl": gl_error,
                "SC": sc_error,
                "CM": sc_error / gl_error,
                "F": np.nan,
                "p-valor": np.nan,
            },
            {
                "Fuente": "Total",
                "gl": gl_total,
                "SC": sc_total,
                "CM": sc_total / gl_total,
                "F": np.nan,
                "p-valor": np.nan,
            },
        ],
        columns=["Fuente", "gl", "SC", "CM", "F", "p-valor"],
    )


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el número de réplicas y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        DataFrame con n, total, media y desviación estándar por tratamiento.

    Raises:
        ValueError: Si los datos no cumplen las condiciones mínimas del DCA.
    """
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede resumir el DCA: " + " ".join(errores))

    # El resumen usa n = cantidad de observaciones, total = suma y media = total/n.
    # La desviación estándar muestral describe la variación entre réplicas del tratamiento.
    resumen = (
        df.groupby(col_trat, sort=False)[col_resp]
        .agg(
            n="count",
            total="sum",
            media="mean",
            desviacion_estandar="std",
        )
        .reset_index()
    )
    return resumen.rename(
        columns={
            col_trat: "Tratamiento",
            "total": "Total",
            "media": "Media",
            "desviacion_estandar": "Desviación estándar",
        }
    )


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación del experimento.

    Args:
        modelo: Modelo OLS ajustado para el DCA.
        df: Datos del experimento.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        Coeficiente de variación expresado como porcentaje.

    Raises:
        ValueError: Si la respuesta no es numérica o su media general es cero.
    """
    # El cuadrado medio del error (CME) estima la varianza residual del experimento.
    cme = float(modelo.mse_resid)
    try:
        media_general = float(pd.to_numeric(df[col_resp], errors="raise").mean())
    except (KeyError, ValueError) as error:
        raise ValueError(f"La columna de respuesta '{col_resp}' debe ser numérica.") from error

    if media_general == 0:
        raise ValueError("No se puede calcular el CV porque la media general es cero.")

    # Fórmula: CV (%) = sqrt(CME) / media general * 100.
    return float(np.sqrt(cme) / media_general * 100)


def tukey(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[pd.DataFrame, float]:
    """Compara tratamientos con Tukey y calcula una DMS crítica.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Una tabla de comparaciones de Tukey en español y la DMS.

    Raises:
        ValueError: Si alfa o los datos no son válidos para el DCA.
    """
    if not 0 < alfa < 1:
        raise ValueError("alfa debe ser mayor que cero y menor que uno.")
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede aplicar Tukey: " + " ".join(errores))

    # Tukey controla el error familiar al contrastar todas las parejas de medias.
    resultado = pairwise_tukeyhsd(
        endog=pd.to_numeric(df[col_resp], errors="raise"),
        groups=df[col_trat],
        alpha=alfa,
    )
    datos_resumen = resultado.summary().data
    comparaciones = pd.DataFrame(datos_resumen[1:], columns=datos_resumen[0])
    comparaciones = comparaciones.rename(
        columns={
            "group1": "Tratamiento 1",
            "group2": "Tratamiento 2",
            "meandiff": "Diferencia de medias",
            "p-adj": "p-valor ajustado",
            "lower": "Límite inferior",
            "upper": "Límite superior",
            "reject": "Se rechaza H0",
        }
    )

    # El CME y los grados de libertad residuales provienen del mismo modelo DCA.
    modelo = ajustar_dca(df, col_trat, col_resp)
    cme = float(modelo.mse_resid)
    gl_error = float(modelo.df_resid)
    replicas = df.groupby(col_trat, sort=False).size().astype(float)
    balanceado = replicas.nunique() == 1

    if balanceado:
        r = float(replicas.iloc[0])
    else:
        # Con tamaños distintos, la media armónica aproxima un único tamaño de réplica.
        r = float(len(replicas) / (1 / replicas).sum())
        warnings.warn(
            "El diseño no está balanceado; la DMS calculada con el tamaño armónico "
            "de réplica es aproximada.",
            UserWarning,
            stacklevel=2,
        )

    # Fórmula: DMS = q(1-alfa; tratamientos; glE) * sqrt(CME/r).
    q_critico = float(
        studentized_range.ppf(1 - alfa, len(replicas), gl_error)
    )
    dms = q_critico * float(np.sqrt(cme / r))
    return comparaciones, float(dms)


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la prueba F de tratamientos en una tabla ANOVA.

    Args:
        tabla: Tabla creada por `tabla_anova`.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Una conclusión sencilla para apoyar la decisión experimental.

    Raises:
        ValueError: Si alfa o la fila de tratamientos no son válidos.
    """
    if not 0 < alfa < 1:
        raise ValueError("alfa debe ser mayor que cero y menor que uno.")
    if "Fuente" not in tabla.columns or "p-valor" not in tabla.columns:
        raise ValueError("La tabla debe incluir las columnas 'Fuente' y 'p-valor'.")

    # Se usa el p-valor de tratamientos para contrastar H0: todas las medias son iguales.
    fila = tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"]
    if fila.empty or pd.isna(fila.iloc[0]):
        raise ValueError("La tabla no contiene un p-valor válido para Tratamientos.")
    p_valor = float(fila.iloc[0])

    if p_valor < alfa:
        return (
            "Se rechaza H0: hay evidencia de que no todas las medias de los "
            "tratamientos son iguales. Para decidir cuál tratamiento difiere, "
            "revise una comparación de medias como Tukey."
        )
    return (
        "No se rechaza H0: no hay evidencia suficiente para afirmar que las "
        "medias de los tratamientos difieren. Esto no demuestra que sean iguales."
    )