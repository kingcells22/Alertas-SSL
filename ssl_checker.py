import json
import ssl
import socket
import datetime as dt
from dateutil import parser
import smtplib 
from email.message import EmailMessage 
import sys 

# --- CONFIGURACIÓN GLOBAL ---
# Días de antelación para enviar una alerta de 'Próximo a vencerse'
UMBRAL_ALERTA_DIAS = 7 

# -----------------------------------------------
# --- CONFIGURACIÓN SMTP (CORREO ELECTRÓNICO) ---
# Clave de Aplicación de Gmail
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  # 587 para TLS (StartTLS)
SMTP_USER = 'soporteotic.fii@gmail.com' # Correo remitente
SMTP_PASSWORD = 'njlpvxfdhowowrvq' 
# -----------------------------------------------

def verificar_ssl_vencimiento(host, port=443):
    """
    Se conecta al host y puerto para obtener las fechas de vigencia y expiración del certificado.
    Retorna la fecha de expiración (datetime), días restantes (int), fecha de vigencia (datetime), y estado (str).
    """
    fecha_vigencia = None
    
    try:
        # 1. Configurar la conexión SSL
        contexto = ssl.create_default_context()
        conn = contexto.wrap_socket(socket.socket(socket.AF_INET), server_hostname=host)
        conn.settimeout(5)
        conn.connect((host, port))
        
        # 2. Obtener la información del certificado
        cert_info = conn.getpeercert()
        
        # 3. Extraer y parsear las fechas (notAfter y notBefore)
        fecha_expiracion_str = cert_info['notAfter'] # type: ignore 
        fecha_vigencia_str = cert_info['notBefore'] 
        
        fecha_expiracion = parser.parse(fecha_expiracion_str)
        fecha_vigencia = parser.parse(fecha_vigencia_str) 

        # 4. Calcular días restantes
        dias_restantes = (fecha_expiracion - dt.datetime.now(fecha_expiracion.tzinfo)).days
        
        conn.close()
        return fecha_expiracion, dias_restantes, fecha_vigencia, "OK" 
        
    except socket.error as e:
        return None, None, fecha_vigencia, f"ERROR DE CONEXIÓN: {e}"
    except ssl.SSLError as e: # type: ignore
        return None, None, fecha_vigencia, f"ERROR SSL: {e}"
    except Exception as e:
        return None, None, fecha_vigencia, f"ERROR DESCONOCIDO: {e}"


def enviar_alerta(asunto, mensaje, destinatario):
    """
    Función para enviar la alerta por correo electrónico.
    """
    if not destinatario:
        print(f"ERROR: No se especificó destinatario. Alerta no enviada: {asunto}")
        return

    msg = EmailMessage()
    msg.set_content(mensaje)
    
    msg['Subject'] = f'[REPORTE SSL] {asunto}'
    msg['From'] = SMTP_USER
    msg['To'] = destinatario
    
    try:
        print(f"\nIntentando conectar a {SMTP_SERVER}:{SMTP_PORT} para enviar reporte/alerta...")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls() 
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Reporte/Alerta enviada exitosamente a: {destinatario}")
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ ERROR SMTP: Fallo de autenticación. Revisa el usuario y la Contraseña de Aplicación de Gmail.")
    except Exception as e:
        print(f"\n❌ ERROR de Conexión/Envío: No se pudo enviar el correo. Detalles: {e}")


def main():
    try:
        with open('servicios.json', 'r') as f:
            servicios = json.load(f)
    except FileNotFoundError:
        print("ERROR: No se encontró el archivo 'servicios.json'. Asegúrate de crearlo.")
        return
    except json.JSONDecodeError:
        print("ERROR: El archivo 'servicios.json' tiene un formato JSON inválido.")
        return

    # Si se ejecuta con el argumento --modo-alerta, SÓLO se envían correos para estados críticos.
    modo_alerta = '--modo-alerta' in sys.argv 
    print(f"--- INICIO DE VERIFICACIÓN (Modo Alerta: {modo_alerta}) ---")

    alertas_generadas = 0
    
    for servicio in servicios:
        dominio = servicio['dominio']
        puerto = servicio.get('puerto', 443) 
        
        # Llama a la función de verificación
        fecha_expiracion, dias_restantes, fecha_vigencia, estado_conexion = verificar_ssl_vencimiento(dominio, puerto)

        # --- Determinación del Status y Excepciones ---
        enviar_email = False 
        
        # 🚨 LÓGICA DE EXCEPCIÓN PARA DOMINIO HTTP/NO-SSL 🚨
        if dominio == 'publicador.fii.gob.ve' and estado_conexion != "OK":
            status_certificado = f"RECOMENDACIÓN 🟡 (Conexión fallida: {estado_conexion})"
            
            # Solo envía esta recomendación si NO estamos en modo alerta (reporte semanal)
            if not modo_alerta:
                enviar_email = True
            else:
                # En modo alerta, registra en consola y omite el envío de email.
                print(f"[{dominio}] Revisado. {status_certificado}. Modo Alerta Activo. No se envió email.")
                continue # Pasa al siguiente servicio.

        # CASO CRÍTICO 1: Error de Conexión/SSL (Para cualquier otro dominio)
        elif estado_conexion != "OK":
            status_certificado = f"ERROR DE VERIFICACIÓN ❌ ({estado_conexion})"
            enviar_email = True # CRÍTICO: SIEMPRE se alerta
            
        # CASO CRÍTICO 2: Vencido
        elif dias_restantes is not None and dias_restantes < 0:
            status_certificado = f"VENCIDO 🔴 (Venció hace {-dias_restantes} días)"
            enviar_email = True # CRÍTICO: SIEMPRE se alerta
            
        # CASO ALERTA: Próximo a Vencerse
        elif dias_restantes is not None and dias_restantes <= UMBRAL_ALERTA_DIAS:
            status_certificado = f"PRÓXIMO A VENCERSE ⚠️ (Quedan {dias_restantes} días)"
            alertas_generadas += 1
            enviar_email = True # ALERTA: SIEMPRE se alerta
            
        # CASO VÁLIDO / OK.
        else:
            dias_restantes_ok = dias_restantes if dias_restantes is not None else "muchos"
            status_certificado = f"VÁLIDO ✅ (Quedan {dias_restantes_ok} días)"
            
            # Si NO es modo alerta (reporte semanal), SÍ envía OK.
            if not modo_alerta:
                 enviar_email = True
            else:
                 # Registro de chequeo silencioso en la consola para el modo diario
                 print(f"[{dominio}] Revisado. {status_certificado}. Modo Alerta Activo. No se envió email.")
                 continue # Pasa al siguiente servicio

        # --- Construcción del Mensaje ---
        
        tiempo_vigencia = fecha_vigencia.strftime('%Y-%m-%d %H:%M:%S') if fecha_vigencia else "N/A (No disponible)" 
        fecha_exp_str = fecha_expiracion.strftime('%Y-%m-%d %H:%M:%S') if fecha_expiracion else "N/A"
        
        # Ajustamos el título y el cuerpo si es una recomendación
        es_recomendacion = 'RECOMENDACIÓN' in status_certificado
        titulo_mensaje = "[RECOMENDACIÓN SSL]" if es_recomendacion else "[REPORTE SSL AUTOMATIZADO - STATUS]"

        # Contenido del mensaje dinámico
        mensaje_cuerpo = ""
        if es_recomendacion:
            mensaje_cuerpo = """
Se detectó una falla al intentar la conexión HTTPS. Revise si el servicio es HTTP o no está activo en el puerto 443.
Se recomienda **integrar un certificado SSL** para asegurar el dominio.
"""
        else:
            mensaje_cuerpo = f"""
Fecha de Expiración: {fecha_exp_str}
Tiempo de vigencia (Inicio): {tiempo_vigencia}
"""

        mensaje = f"""
        {titulo_mensaje}
        
        Nombre del Dominio: {servicio['nombre']}
        URL del Servicio: https://{dominio}:{puerto}
        
        -------------------------------------------------
        Status del Certificado SSL: {status_certificado}
        
        {'--- RECOMENDACIÓN DE SEGURIDAD ---' if es_recomendacion else ''}
        
        {mensaje_cuerpo}
        
        -------------------------------------------------
        Responsable IT (Jefe): {servicio['jefe_servicios']}
        Desarrollador encargado: {servicio['desarrollador']}
        """
        
        # Generar el Asunto
        asunto = f"Status: {status_certificado} para {servicio['dominio']}"
        
        # Llamar a la función de envío SOLAMENTE si enviar_email es True
        if enviar_email:
             enviar_alerta(asunto, mensaje, servicio['email_alerta'])
             
    if alertas_generadas == 0:
        print("\n✅ Verificación completada. Ningún certificado entró en la fase de alerta crítica.")
    else:
        print(f"\n⚠️ Verificación completada. Se generaron {alertas_generadas} alertas críticas. Se enviaron los correos.")

    print(f"--- FIN DE VERIFICACIÓN ---")

if __name__ == "__main__":
    main()