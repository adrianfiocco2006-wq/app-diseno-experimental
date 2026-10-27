# Instrucciones permanentes del repositorio

- **Proyecto:** App de Diseño Experimental en Python y Streamlit para el curso de Diseño Experimental de Ingeniería Agrícola, Universidad de Sucre.
- **Estructura:** `app.py` es la portada; `pages/` contiene un archivo por diseño; `utils/` contiene funciones reutilizables e incluye `__init__.py`; `data/` contiene CSV de ejemplo; `verificacion/` contiene scripts de R.
- Todo el código, comentarios, docstrings y mensajes de la interfaz deben estar en español.
- Cada paso estadístico debe incluir un comentario que explique qué calcula y por qué, pensado para estudiantes de Ingeniería Agrícola.
- Las funciones deben incluir anotaciones de tipos y docstrings con estilo Google.
- **Librerías permitidas:** `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `plotly` y `openpyxl`. No agregues otras sin pedir permiso.
- Ajusta los ANOVA con `statsmodels.formula.api.ols` y `statsmodels.stats.anova.anova_lm(typ=2)`. Realiza las comparaciones de Tukey con `statsmodels.stats.multicomp.pairwise_tukeyhsd`.
- No inventes resultados: los números siempre deben provenir del cálculo.
- Antes de terminar una tarea, ejecuta el código y corrige los errores que aparezcan.