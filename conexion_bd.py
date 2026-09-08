import mysql.connector
from mysql.connector import Error
import os

def obtener_conexion():
    """
    Función reutilizable para obtener conexión a MySQL.
    Crea la base de datos si no existe.
    """
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password=""
        )
        
        if conexion.is_connected():
            cursor = conexion.cursor()
            
            # Crear base de datos
            cursor.execute("CREATE DATABASE IF NOT EXISTS bancoseguro_db")
            cursor.execute("USE bancoseguro_db")
            
            # TABLA 1: tipos_transaccion
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tipos_transaccion (
                    id_tipo INT PRIMARY KEY AUTO_INCREMENT,
                    nombre_tipo VARCHAR(50) NOT NULL UNIQUE
                )
            """)
            
            # Insertar semillas tipos_transaccion
            cursor.execute("INSERT IGNORE INTO tipos_transaccion (id_tipo, nombre_tipo) VALUES (1, 'Retiro')")
            cursor.execute("INSERT IGNORE INTO tipos_transaccion (id_tipo, nombre_tipo) VALUES (2, 'Consignación')")
            cursor.execute("INSERT IGNORE INTO tipos_transaccion (id_tipo, nombre_tipo) VALUES (3, 'Transferencia')")
            cursor.execute("INSERT IGNORE INTO tipos_transaccion (id_tipo, nombre_tipo) VALUES (4, 'Consulta de Saldo')")
            
            # TABLA 2: ciudades_cajero
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ciudades_cajero (
                    id_ciudad INT PRIMARY KEY AUTO_INCREMENT,
                    nombre_ciudad VARCHAR(50) NOT NULL UNIQUE
                )
            """)
            
            # Insertar semillas ciudades_cajero
            cursor.execute("INSERT IGNORE INTO ciudades_cajero (id_ciudad, nombre_ciudad) VALUES (1, 'Bogotá')")
            cursor.execute("INSERT IGNORE INTO ciudades_cajero (id_ciudad, nombre_ciudad) VALUES (2, 'Medellín')")
            cursor.execute("INSERT IGNORE INTO ciudades_cajero (id_ciudad, nombre_ciudad) VALUES (3, 'Cali')")
            cursor.execute("INSERT IGNORE INTO ciudades_cajero (id_ciudad, nombre_ciudad) VALUES (4, 'Barranquilla')")
            cursor.execute("INSERT IGNORE INTO ciudades_cajero (id_ciudad, nombre_ciudad) VALUES (5, 'Bucaramanga')")
            
            # TABLA 3: usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
                    nombre_usuario VARCHAR(80) NOT NULL,
                    correo VARCHAR(120) NOT NULL UNIQUE,
                    contrasena_hash VARCHAR(255) NOT NULL,
                    rol VARCHAR(30) NOT NULL,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Verificar si administrador ya existe
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'Administrador del Sistema'")
            if cursor.fetchone()[0] == 0:
                # Importar aquí para evitar circular import
                from werkzeug.security import generate_password_hash
                admin_hash = generate_password_hash("Admin123!Seguro")
                cursor.execute("""
                    INSERT INTO usuarios (nombre_usuario, correo, contrasena_hash, rol)
                    VALUES (%s, %s, %s, %s)
                """, ("Administrador BancoSeguro", "admin@bancoseguro.com", admin_hash, "Administrador del Sistema"))
            
            # TABLA 4: transacciones_atm
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transacciones_atm (
                    id_transaccion INT PRIMARY KEY AUTO_INCREMENT,
                    id_tipo INT,
                    id_ciudad INT,
                    id_usuario INT,
                    monto_transaccion_miles DECIMAL(8,1),
                    tiempo_transaccion_seg DECIMAL(6,1),
                    saldo_disponible_miles DECIMAL(9,1),
                    fecha_transaccion DATE,
                    hora_transaccion TIME,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_tipo) REFERENCES tipos_transaccion(id_tipo),
                    FOREIGN KEY (id_ciudad) REFERENCES ciudades_cajero(id_ciudad),
                    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
                )
            """)
            
            conexion.commit()
            return conexion
    
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None


def cerrar_conexion(conexion):
    """
    Cierra la conexión a MySQL.
    """
    if conexion and conexion.is_connected():
        conexion.close()