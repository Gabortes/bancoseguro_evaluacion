# 🏦 RED BANCOSEGURO

**Plataforma Web con Roles de Usuario para el Registro y Análisis Estadístico de Transacciones en Cajeros Automáticos (ATM)**

## Descripción

Red BancoSeguro es una aplicación web completa desarrollada con Flask, MySQL y análisis estadístico avanzado. Permite registrar, limpiar y analizar transacciones de cajeros automáticos con 4 roles de usuario diferenciados y generación de informes PDF en formato APA 7.

## Características Principales

✅ **4 Roles de Usuario** con permisos diferenciados  
✅ **40 Transacciones** (25 CSV + 15 manuales) que se limpian automáticamente a 35  
✅ **Estadística Descriptiva Completa** comparando datos crudos vs limpios  
✅ **Análisis de Probabilidades** incluyendo Teorema de Bayes  
✅ **Correlaciones Múltiples** (Pearson, Spearman, Kendall, Phi)  
✅ **14 Visualizaciones** (7 crudas + 7 limpias, estáticas e interactivas)  
✅ **Informe PDF en APA 7** con 13 preguntas reflexivas  
✅ **Seguridad en Servidor** con validación de roles  
✅ **Base de Datos Automática** al ejecutar `python app.py`

## Requisitos Previos

- Python 3.8+
- XAMPP (Apache + MySQL)
- Git

## Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Gabortes/bancoseguro_evaluacion.git
cd bancoseguro_evaluacion
```

### 2. Crear Entorno Virtual (Recomendado)
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

## Ejecución

### 1. Iniciar XAMPP
- Abrir XAMPP Control Panel
- Iniciar Apache y MySQL

### 2. Ejecutar la Aplicación
```bash
python app.py
```

### 3. Acceder a la Plataforma
Abrir navegador en:
```
http://localhost:5000/login
```

## Credenciales Iniciales

**Administrador del Sistema:**
- Correo: `admin@bancoseguro.com`
- Contraseña: `Admin123!Seguro`

## Estructura del Proyecto

```
bancoseguro_evaluacion/
├── app.py                          # Aplicación principal Flask
├── conexion_bd.py                  # Conexión y creación de BD
├── generador_pdf.py                # Generación de informes PDF
├── requirements.txt                # Dependencias Python
├── static/
│   ├── styles.css                  # Estilos CSS
│   ├── grafica_*.png               # Gráficos estáticos (14 archivos)
│   └── *_interactivo*.html         # Gráficos Plotly interactivos
├── templates/
│   ├── login.html                  # Página de login
│   ├── registro.html               # Página de registro
│   ├── usuarios.html               # Gestión de usuarios (admin)
│   └── index.html                  # Página principal de análisis
├── informes_generados/             # Informes PDF generados
└── README.md
```

## Matriz de Permisos

| Acción | Cajero | Auditor | Analista | Admin |
|--------|--------|---------|----------|-------|
| Login | ✅ | ✅ | ✅ | ✅ |
| Registro | ✅ | ✅ | ✅ | ❌ |
| Registrar Manual | ✅ | ✅ | ✅ | ❌ |
| Cargar CSV | ❌ | ❌ | ❌ | ✅ |
| Ver Datos Crudos | Solo suyos | Todos | Todos | Todos |
| Editar | ❌ | ✅ | ❌ | ✅ |
| Eliminar | ❌ | ✅ | ❌ | ✅ |
| Ver Estadísticas | ❌ | ✅ | ✅ | ✅ |
| Ver Gráficas | ❌ | ✅ | ✅ | ✅ |
| Generar PDF | ❌ | ❌ | ✅ | ✅ |
| Gestionar Usuarios | ❌ | ❌ | ❌ | ✅ |

## Tecnologías Utilizadas

- **Backend:** Flask 2.3.3
- **Base de Datos:** MySQL 8.0
- **Análisis de Datos:** Pandas, NumPy, SciPy, Statsmodels
- **Visualizaciones:** Matplotlib, Seaborn, Plotly
- **Reportes:** fpdf2
- **Seguridad:** Werkzeug (password hashing)
- **Frontend:** HTML5, CSS3, JavaScript

## Análisis Estadístico Incluido

### Estadística Descriptiva
- Media, Mediana, Moda
- Desviación Estándar, Varianza
- Rango, Cuartiles, Deciles, Percentiles
- Asimetría y Curtosis
- Coeficiente de Variación

### Probabilidades
- Probabilidades Marginales
- Probabilidades Conjuntas
- Probabilidades Condicionales
- Teorema de Bayes

### Correlaciones
- Pearson (lineal)
- Spearman (rangos)
- Kendall (concordancia)
- Phi (asociación 2×2)

### Visualizaciones
1. Histogramas
2. Polígonos de Frecuencia
3. Diagramas de Caja Simple
4. Diagramas de Caja Comparativos
5. Gráficos de Dispersión Interactivos
6. Gráficos de Barras Interactivos
7. Gráficos Circulares Interactivos

## Limpieza de Datos

El sistema automáticamente:
- Elimina 3 duplicados por contenido (excluyendo id_transaccion)
- Elimina 2 registros irrecuperables (falta tipo Y monto)
- Normaliza fechas y horas
- Recupera valores faltantes con mediana
- Maneja outliers con regla 1.5 × IQR

**Resultado:** 40 registros iniciales → 35 registros válidos

## Informe PDF (APA 7)

El informe generado incluye:
- ✅ Portada con trazabilidad (nombre, rol, fecha/hora del generador)
- ✅ Introducción y Metodología
- ✅ Estadística Descriptiva Comparativa
- ✅ Análisis de Probabilidades
- ✅ Teorema de Bayes
- ✅ Correlaciones (Pearson, Spearman, Kendall, Phi)
- ✅ 14 Visualizaciones
- ✅ 13 Preguntas Reflexivas con Respuestas Reales
- ✅ Conclusiones y Recomendaciones
- ✅ Referencias APA 7
- ✅ Márgenes 2.54 cm, numeración de páginas

## Validaciones

✅ Correo institucional (@bancoseguro.com)  
✅ Contraseña segura (8 caracteres, mayúscula, número, especial)  
✅ Roles validados en servidor (no solo HTML)  
✅ Consultas parametrizadas (prevención SQL injection)  
✅ Manejo de excepciones completo  

## Licencia

Este proyecto es de código abierto con propósitos educativos.

## Autor

Desarrollado como evaluación final de análisis estadístico en plataformas web.

---

**¿Preguntas o problemas?** Abre un issue en el repositorio.
