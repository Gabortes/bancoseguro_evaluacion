from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from conexion_bd import obtener_conexion, cerrar_conexion
import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from generador_pdf import generar_pdf_informe
import os
import re
from datetime import datetime, date
import json

app = Flask(__name__)
app.secret_key = 'BancoSeguro_2026_Evaluacion_Secreta'

# Configuración de gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ==================== DECORADORES ====================

def login_requerido(f):
    """Decorador para verificar si el usuario está logueado"""
    def decorado(*args, **kwargs):
        if 'id_usuario' not in session:
            flash('Debes iniciar sesión primero', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorado.__name__ = f.__name__
    return decorado

def rol_requerido(*roles_permitidos):
    """Decorador para verificar si el usuario tiene el rol requerido"""
    def decorador(f):
        def decorado(*args, **kwargs):
            if 'rol' not in session or session['rol'] not in roles_permitidos:
                flash('Acceso denegado. No tienes permisos para esta acción', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        decorado.__name__ = f.__name__
        return decorado
    return decorador

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').lower()
        contrasena = request.form.get('contrasena', '')
        
        if not correo or not contrasena:
            flash('Correo y contraseña son requeridos', 'error')
            return redirect(url_for('login'))
        
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
            usuario = cursor.fetchone()
            
            if usuario and check_password_hash(usuario['contrasena_hash'], contrasena):
                session['id_usuario'] = usuario['id_usuario']
                session['nombre_usuario'] = usuario['nombre_usuario']
                session['correo'] = usuario['correo']
                session['rol'] = usuario['rol']
                
                flash(f'Bienvenido, {usuario["nombre_usuario"]}', 'success')
                return redirect(url_for('index'))
            else:
                flash('Correo o contraseña incorrectos', 'error')
        
        except Error as e:
            flash(f'Error en la base de datos: {str(e)}', 'error')
        finally:
            if cursor:
                cursor.close()
            if conexion:
                cerrar_conexion(conexion)
    
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre_usuario', '').strip()
        correo = request.form.get('correo', '').lower().strip()
        contrasena = request.form.get('contrasena', '')
        rol = request.form.get('rol', '')
        
        # Validaciones
        if not nombre or len(nombre) < 3:
            flash('El nombre debe tener al menos 3 caracteres', 'error')
            return redirect(url_for('registro'))
        
        if not correo.endswith('@bancoseguro.com'):
            flash('El correo debe ser del dominio @bancoseguro.com', 'error')
            return redirect(url_for('registro'))
        
        # Validar contraseña: 8 caracteres, mayúscula, número, carácter especial
        patron = r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:\'"|,.<>?\/\\]).{8,}$'
        if not re.match(patron, contrasena):
            flash('Contraseña debe tener: 8+ caracteres, mayúscula, número, carácter especial', 'error')
            return redirect(url_for('registro'))
        
        if rol not in ['Cajero Registrador', 'Auditor de Calidad', 'Analista de Riesgo']:
            flash('Rol inválido seleccionado', 'error')
            return redirect(url_for('registro'))
        
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            
            contrasena_hash = generate_password_hash(contrasena)
            
            cursor.execute(
                "INSERT INTO usuarios (nombre_usuario, correo, contrasena_hash, rol) VALUES (%s, %s, %s, %s)",
                (nombre, correo, contrasena_hash, rol)
            )
            conexion.commit()
            
            flash('Registro exitoso. Por favor inicia sesión', 'success')
            return redirect(url_for('login'))
        
        except Error as e:
            if 'Duplicate' in str(e):
                flash('El correo ya está registrado', 'error')
            else:
                flash(f'Error en el registro: {str(e)}', 'error')
        finally:
            if cursor:
                cursor.close()
            if conexion:
                cerrar_conexion(conexion)
    
    return render_template('registro.html')

@app.route('/logout')
@login_requerido
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
@login_requerido
def index():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener catálogos
        cursor.execute("SELECT * FROM tipos_transaccion ORDER BY id_tipo")
        tipos = cursor.fetchall()
        
        cursor.execute("SELECT * FROM ciudades_cajero ORDER BY id_ciudad")
        ciudades = cursor.fetchall()
        
        # Obtener transacciones
        if session['rol'] == 'Cajero Registrador':
            cursor.execute("""
                SELECT t.*, tp.nombre_tipo, c.nombre_ciudad, u.nombre_usuario, u.rol
                FROM transacciones_atm t
                LEFT JOIN tipos_transaccion tp ON t.id_tipo = tp.id_tipo
                LEFT JOIN ciudades_cajero c ON t.id_ciudad = c.id_ciudad
                LEFT JOIN usuarios u ON t.id_usuario = u.id_usuario
                WHERE t.id_usuario = %s
                ORDER BY t.id_transaccion DESC
            """, (session['id_usuario'],))
        else:
            cursor.execute("""
                SELECT t.*, tp.nombre_tipo, c.nombre_ciudad, u.nombre_usuario, u.rol
                FROM transacciones_atm t
                LEFT JOIN tipos_transaccion tp ON t.id_tipo = tp.id_tipo
                LEFT JOIN ciudades_cajero c ON t.id_ciudad = c.id_ciudad
                LEFT JOIN usuarios u ON t.id_usuario = u.id_usuario
                ORDER BY t.id_transaccion DESC
            """)
        
        transacciones = cursor.fetchall()
        
        # Crear DataFrames
        if transacciones:
            df_crudo = pd.DataFrame([
                {
                    'id_transaccion': t['id_transaccion'],
                    'monto_transaccion_miles': t['monto_transaccion_miles'],
                    'tiempo_transaccion_seg': t['tiempo_transaccion_seg'],
                    'saldo_disponible_miles': t['saldo_disponible_miles'],
                    'tipo_transaccion': t['nombre_tipo'],
                    'ciudad_cajero': t['nombre_ciudad'],
                    'fecha_transaccion': t['fecha_transaccion'],
                    'hora_transaccion': t['hora_transaccion'],
                    'nombre_usuario': t['nombre_usuario'],
                    'rol': t['rol']
                }
                for t in transacciones
            ])
            
            # Limpiar datos
            df_limpio = df_crudo.copy()
            
            # Eliminar duplicados (excluyendo id_transaccion)
            df_limpio = df_limpio.drop_duplicates(subset=[
                'tipo_transaccion', 'ciudad_cajero', 'monto_transaccion_miles',
                'tiempo_transaccion_seg', 'saldo_disponible_miles',
                'fecha_transaccion', 'hora_transaccion'
            ], keep='first')
            
            # Eliminar registros irrecuperables (faltan tipo Y monto simultáneamente)
            df_limpio = df_limpio[~(df_limpio['tipo_transaccion'].isna() & df_limpio['monto_transaccion_miles'].isna())]
            
            total_crudo = len(df_crudo)
            total_limpio = len(df_limpio)
        else:
            df_crudo = pd.DataFrame()
            df_limpio = pd.DataFrame()
            total_crudo = 0
            total_limpio = 0
        
        # Calcular estadísticas
        stats_crudo = {}
        stats_limpio = {}
        
        if not df_crudo.empty:
            for var in ['monto_transaccion_miles', 'tiempo_transaccion_seg']:
                data_cruda = df_crudo[var].dropna()
                if len(data_cruda) > 0:
                    stats_crudo[var] = {
                        'media': data_cruda.mean(),
                        'mediana': data_cruda.median(),
                        'desviacion_estandar': data_cruda.std(),
                        'varianza': data_cruda.var(),
                        'coeficiente_variacion': (data_cruda.std() / data_cruda.mean() * 100) if data_cruda.mean() != 0 else 0,
                        'asimetria': stats.skew(data_cruda),
                        'curtosis': stats.kurtosis(data_cruda),
                        'min': data_cruda.min(),
                        'max': data_cruda.max(),
                        'rango': data_cruda.max() - data_cruda.min(),
                        'iqr': data_cruda.quantile(0.75) - data_cruda.quantile(0.25)
                    }
        
        if not df_limpio.empty:
            for var in ['monto_transaccion_miles', 'tiempo_transaccion_seg']:
                data_limpia = df_limpio[var].dropna()
                if len(data_limpia) > 0:
                    stats_limpio[var] = {
                        'media': data_limpia.mean(),
                        'mediana': data_limpia.median(),
                        'desviacion_estandar': data_limpia.std(),
                        'varianza': data_limpia.var(),
                        'coeficiente_variacion': (data_limpia.std() / data_limpia.mean() * 100) if data_limpia.mean() != 0 else 0,
                        'asimetria': stats.skew(data_limpia),
                        'curtosis': stats.kurtosis(data_limpia),
                        'min': data_limpia.min(),
                        'max': data_limpia.max(),
                        'rango': data_limpia.max() - data_limpia.min(),
                        'iqr': data_limpia.quantile(0.75) - data_limpia.quantile(0.25)
                    }
        
        # Crear visualizaciones
        crear_visualizaciones(df_crudo, df_limpio)
        
        # Convertir DataFrames a JSON para JavaScript
        df_crudo_json = df_crudo.to_json(orient='records', default_handler=str) if not df_crudo.empty else '[]'
        df_limpio_json = df_limpio.to_json(orient='records', default_handler=str) if not df_limpio.empty else '[]'
        
        return render_template('index.html',
            usuario=session['nombre_usuario'],
            rol=session['rol'],
            tipos=tipos,
            ciudades=ciudades,
            df_crudo=df_crudo,
            df_limpio=df_limpio,
            df_crudo_json=df_crudo_json,
            df_limpio_json=df_limpio_json,
            total_crudo=total_crudo,
            total_limpio=total_limpio,
            stats_crudo=stats_crudo,
            stats_limpio=stats_limpio,
            now=datetime.now()
        )
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('logout'))
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)

@app.route('/usuarios')
@login_requerido
@rol_requerido('Administrador del Sistema')
def usuarios():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("SELECT id_usuario, nombre_usuario, correo, rol, fecha_creacion FROM usuarios ORDER BY fecha_creacion DESC")
        usuarios_list = cursor.fetchall()
        
        return render_template('usuarios.html',
            usuario=session['nombre_usuario'],
            rol=session['rol'],
            usuarios=usuarios_list
        )
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)

@app.route('/registrar-manual', methods=['POST'])
@login_requerido
@rol_requerido('Cajero Registrador', 'Auditor de Calidad', 'Analista de Riesgo')
def registrar_manual():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        id_tipo = request.form.get('id_tipo')
        id_ciudad = request.form.get('id_ciudad')
        monto = request.form.get('monto_transaccion_miles')
        tiempo = request.form.get('tiempo_transaccion_seg')
        saldo = request.form.get('saldo_disponible_miles')
        fecha = request.form.get('fecha_transaccion')
        hora = request.form.get('hora_transaccion')
        
        # Convertir valores
        monto = float(monto) if monto else None
        tiempo = float(tiempo) if tiempo else None
        saldo = float(saldo) if saldo else None
        
        cursor.execute("""
            INSERT INTO transacciones_atm 
            (id_tipo, id_ciudad, id_usuario, monto_transaccion_miles, tiempo_transaccion_seg, 
             saldo_disponible_miles, fecha_transaccion, hora_transaccion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (id_tipo, id_ciudad, session['id_usuario'], monto, tiempo, saldo, fecha, hora))
        
        conexion.commit()
        flash('Transacción registrada exitosamente', 'success')
    
    except Error as e:
        flash(f'Error al registrar: {str(e)}', 'error')
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)
    
    return redirect(url_for('index'))

@app.route('/cargar-csv', methods=['POST'])
@login_requerido
@rol_requerido('Administrador del Sistema')
def cargar_csv():
    try:
        if 'archivo_csv' not in request.files:
            flash('No se seleccionó archivo', 'error')
            return redirect(url_for('index'))
        
        archivo = request.files['archivo_csv']
        
        if not archivo.filename.endswith('.csv'):
            flash('Solo se aceptan archivos CSV', 'error')
            return redirect(url_for('index'))
        
        # Leer CSV
        df = pd.read_csv(archivo)
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Obtener mapeos de catálogos
        cursor.execute("SELECT id_tipo, nombre_tipo FROM tipos_transaccion")
        tipos_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT id_ciudad, nombre_ciudad FROM ciudades_cajero")
        ciudades_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        for _, row in df.iterrows():
            tipo_nombre = str(row['tipo_transaccion']).strip().lower()
            ciudad_nombre = str(row['ciudad_cajero']).strip().lower()
            
            id_tipo = tipos_map.get(tipo_nombre)
            id_ciudad = ciudades_map.get(ciudad_nombre)
            
            if id_tipo and id_ciudad:
                monto = float(row['monto_transaccion_miles']) if pd.notna(row['monto_transaccion_miles']) else None
                tiempo = float(row['tiempo_transaccion_seg']) if pd.notna(row['tiempo_transaccion_seg']) else None
                saldo = float(row['saldo_disponible_miles']) if pd.notna(row['saldo_disponible_miles']) else None
                
                cursor.execute("""
                    INSERT INTO transacciones_atm 
                    (id_tipo, id_ciudad, id_usuario, monto_transaccion_miles, tiempo_transaccion_seg,
                     saldo_disponible_miles, fecha_transaccion, hora_transaccion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (id_tipo, id_ciudad, session['id_usuario'], monto, tiempo, saldo, 
                      row['fecha_transaccion'], row['hora_transaccion']))
        
        conexion.commit()
        flash(f'CSV cargado exitosamente. {len(df)} registros importados', 'success')
    
    except Exception as e:
        flash(f'Error al cargar CSV: {str(e)}', 'error')
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)
    
    return redirect(url_for('index'))

@app.route('/editar/<int:id_transaccion>', methods=['GET', 'POST'])
@login_requerido
@rol_requerido('Auditor de Calidad', 'Administrador del Sistema')
def editar(id_transaccion):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        if request.method == 'POST':
            id_tipo = request.form.get('id_tipo')
            id_ciudad = request.form.get('id_ciudad')
            monto = float(request.form.get('monto_transaccion_miles', 0))
            tiempo = float(request.form.get('tiempo_transaccion_seg', 0)) if request.form.get('tiempo_transaccion_seg') else None
            saldo = float(request.form.get('saldo_disponible_miles', 0))
            fecha = request.form.get('fecha_transaccion')
            hora = request.form.get('hora_transaccion')
            
            cursor.execute("""
                UPDATE transacciones_atm
                SET id_tipo=%s, id_ciudad=%s, monto_transaccion_miles=%s,
                    tiempo_transaccion_seg=%s, saldo_disponible_miles=%s,
                    fecha_transaccion=%s, hora_transaccion=%s
                WHERE id_transaccion=%s
            """, (id_tipo, id_ciudad, monto, tiempo, saldo, fecha, hora, id_transaccion))
            
            conexion.commit()
            flash('Transacción actualizada exitosamente', 'success')
            return redirect(url_for('index'))
        
        cursor.execute("SELECT * FROM transacciones_atm WHERE id_transaccion=%s", (id_transaccion,))
        transaccion = cursor.fetchone()
        
        if not transaccion:
            flash('Transacción no encontrada', 'error')
            return redirect(url_for('index'))
        
        cursor.execute("SELECT * FROM tipos_transaccion")
        tipos = cursor.fetchall()
        cursor.execute("SELECT * FROM ciudades_cajero")
        ciudades = cursor.fetchall()
        
        return render_template('editar.html',
            usuario=session['nombre_usuario'],
            rol=session['rol'],
            transaccion=transaccion,
            tipos=tipos,
            ciudades=ciudades
        )
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)

@app.route('/eliminar/<int:id_transaccion>', methods=['POST'])
@login_requerido
@rol_requerido('Auditor de Calidad', 'Administrador del Sistema')
def eliminar(id_transaccion):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("DELETE FROM transacciones_atm WHERE id_transaccion=%s", (id_transaccion,))
        conexion.commit()
        
        flash('Transacción eliminada exitosamente', 'success')
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)
    
    return redirect(url_for('index'))

@app.route('/generar-informe', methods=['POST'])
@login_requerido
@rol_requerido('Analista de Riesgo', 'Administrador del Sistema')
def generar_informe():
    try:
        # Obtener datos
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT t.*, tp.nombre_tipo, c.nombre_ciudad, u.nombre_usuario, u.rol
            FROM transacciones_atm t
            LEFT JOIN tipos_transaccion tp ON t.id_tipo = tp.id_tipo
            LEFT JOIN ciudades_cajero c ON t.id_ciudad = c.id_ciudad
            LEFT JOIN usuarios u ON t.id_usuario = u.id_usuario
            ORDER BY t.id_transaccion
        """)
        
        transacciones = cursor.fetchall()
        
        if not transacciones:
            flash('No hay datos para generar el informe', 'error')
            return redirect(url_for('index'))
        
        # Crear DataFrames
        df = pd.DataFrame([{
            'id_transaccion': t['id_transaccion'],
            'monto_transaccion_miles': t['monto_transaccion_miles'],
            'tiempo_transaccion_seg': t['tiempo_transaccion_seg'],
            'saldo_disponible_miles': t['saldo_disponible_miles'],
            'tipo_transaccion': t['nombre_tipo'],
            'ciudad_cajero': t['nombre_ciudad'],
            'fecha_transaccion': t['fecha_transaccion'],
            'hora_transaccion': t['hora_transaccion']
        } for t in transacciones])
        
        # Generar PDF
        nombre_generador = session['nombre_usuario']
        rol_generador = session['rol']
        fecha_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        pdf_path = generar_pdf_informe(df, nombre_generador, rol_generador, fecha_hora)
        
        return send_file(pdf_path, as_attachment=True, download_name=f'informe_bancoseguro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
    
    except Exception as e:
        flash(f'Error al generar informe: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)

# ==================== FUNCIONES AUXILIARES ====================

def crear_visualizaciones(df_crudo, df_limpio):
    """Crea todas las visualizaciones necesarias"""
    
    if df_crudo.empty or df_limpio.empty:
        return
    
    # Crear carpeta static si no existe
    os.makedirs('static', exist_ok=True)
    
    # 1. Histogramas
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df_crudo['monto_transaccion_miles'].dropna(), bins=10, color='#667eea', alpha=0.7, edgecolor='black')
    ax.set_xlabel('Monto (miles)', fontsize=12)
    ax.set_ylabel('Frecuencia', fontsize=12)
    ax.set_title('Histograma - Datos Crudos', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('static/grafica_histograma_atipica.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df_limpio['monto_transaccion_miles'].dropna(), bins=10, color='#48bb78', alpha=0.7, edgecolor='black')
    ax.set_xlabel('Monto (miles)', fontsize=12)
    ax.set_ylabel('Frecuencia', fontsize=12)
    ax.set_title('Histograma - Datos Limpios', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('static/grafica_histograma_limpia.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. Polígonos de Frecuencia
    for df, nombre in [(df_crudo, 'atipico'), (df_limpio, 'limpio')]:
        counts, bins = np.histogram(df['monto_transaccion_miles'].dropna(), bins=10)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(bin_centers, counts, marker='o', color='#667eea' if nombre == 'atipico' else '#48bb78', linewidth=2, markersize=8)
        ax.fill_between(bin_centers, counts, alpha=0.3, color='#667eea' if nombre == 'atipico' else '#48bb78')
        ax.set_xlabel('Monto (miles)', fontsize=12)
        ax.set_ylabel('Frecuencia', fontsize=12)
        ax.set_title(f'Polígono de Frecuencia - Datos {"Crudos" if nombre == "atipico" else "Limpios"}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'static/grafica_poligono_de_frecuencia_{nombre}.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    # 3. Cajas Simples
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(df_crudo['monto_transaccion_miles'].dropna(), vert=True)
    ax.set_ylabel('Monto (miles)', fontsize=12)
    ax.set_title('Diagrama de Caja Simple - Datos Crudos', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('static/grafica_caja_simple_atipica.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(df_limpio['monto_transaccion_miles'].dropna(), vert=True)
    ax.set_ylabel('Monto (miles)', fontsize=12)
    ax.set_title('Diagrama de Caja Simple - Datos Limpios', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('static/grafica_caja_simple_limpia.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 4. Cajas Comparativas
    for df, nombre in [(df_crudo, 'atipica'), (df_limpio, 'limpia')]:
        fig, ax = plt.subplots(figsize=(12, 6))
        df_temp = df.dropna(subset=['tipo_transaccion', 'monto_transaccion_miles'])
        if not df_temp.empty:
            df_temp.boxplot(column='monto_transaccion_miles', by='tipo_transaccion', ax=ax)
            ax.set_xlabel('Tipo de Transacción', fontsize=12)
            ax.set_ylabel('Monto (miles)', fontsize=12)
            plt.suptitle(f'Diagrama de Caja Comparativo - Datos {"Crudos" if nombre == "atipica" else "Limpios"}', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f'static/grafica_caja_comparativa_{nombre}.png', dpi=150, bbox_inches='tight')
            plt.close()
    
    # 5. Gráficos Plotly Interactivos
    for df, nombre in [(df_crudo, 'atipico'), (df_limpio, 'limpio')]:
        df_clean = df.dropna(subset=['tiempo_transaccion_seg', 'monto_transaccion_miles'])
        if not df_clean.empty:
            fig = px.scatter(df_clean, x='tiempo_transaccion_seg', y='monto_transaccion_miles',
                            trendline='ols', title=f'Dispersión - Datos {"Crudos" if nombre == "atipico" else "Limpios"}')
            fig.write_html(f'static/dispersion_interactivo_{nombre}.html')
            
            fig = px.bar(df_clean.groupby('ciudad_cajero')['monto_transaccion_miles'].mean(),
                        title=f'Promedio de Monto por Ciudad - Datos {"Crudos" if nombre == "atipico" else "Limpios"}')
            fig.write_html(f'static/barras_interactivo_{nombre}.html')
            
            fig = px.pie(df_clean['ciudad_cajero'].value_counts(),
                        title=f'Participación por Ciudad - Datos {"Crudos" if nombre == "atipico" else "Limpios"}')
            fig.write_html(f'static/circular_interactivo_{nombre}.html')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error='Error interno del servidor'), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    # Inicializar BD
    conexion = obtener_conexion()
    if conexion:
        cerrar_conexion(conexion)
        print("✅ Base de datos inicializada correctamente")
    
    # Crear carpetas necesarias
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('informes_generados', exist_ok=True)
    
    app.run(debug=True, host='localhost', port=5000)
