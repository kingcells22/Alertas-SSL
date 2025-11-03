🛡️ Alertas-SSL: Monitor de Certificados (SSL Checker)Este repositorio contiene un script de Python diseñado para monitorear automáticamente la vigencia de certificados SSL/TLS en múltiples servicios. El sistema está configurado para operar en un modo dual (silencioso diario y reporte semanal) y enviar alertas por correo electrónico ante la detección de fallos críticos o vencimiento inminente.🚀 1. Características PrincipalesMonitoreo Dual: Ejecución diaria en modo silencioso (solo alertas críticas) y un reporte completo semanal.Alerta Inmediata: Envío de correo electrónico inmediato si un certificado está VENCIDO, presenta un ERROR de conexión, o está PRÓXIMO a VENCERSE (menos de 7 días).Excepción para HTTP: Manejo especial para dominios que no utilizan SSL/TLS, enviando una recomendación solo en el reporte semanal.Configuración Externa: Los servicios a monitorear y sus destinatarios de alerta se gestionan a través de un archivo JSON (servicios.json).🛠️ 2. Instalación y DependenciasEl script requiere Python 3.x y el módulo python-dateutil para el manejo de fechas.Requisitos PreviosPython 3.x instalado en el servidor (VM).Clave de Aplicación de Gmail: Se requiere una clave de aplicación específica de Google (no la contraseña de la cuenta) para el campo SMTP_PASSWORD del script.Pasos de InstalaciónClonar el Repositorio:Bashgit clone https://github.com/kingcells22/Alertas-SSL.git
cd Alertas-SSL
Crear y Activar el Entorno Virtual (Recomendado):Bashpython3 -m venv .venv
source .venv/bin/activate  # En Linux/macOS
# .venv\Scripts\activate   # En Windows
Instalar Dependencias:Bashpip install python-dateutil
⚙️ 3. Configuración del SistemaA. Configuración de Credenciales (Dentro de ssl_checker.py)Abre el archivo ssl_checker.py y actualiza la sección CONFIGURACIÓN SMTP con tus datos de Gmail y el Token de Acceso Personal (Clave de Aplicación):Python# --- CONFIGURACIÓN SMTP (CORREO ELECTRÓNICO) ---
# Clave de Aplicación de Gmail
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  
SMTP_USER = 'soporteotic.fii@gmail.com' # Correo remitente
SMTP_PASSWORD = 'TU_CLAVE_DE_APLICACION_DE_GMAIL' 
# -----------------------------------------------
B. Configuración de Servicios (servicios.json)Crea un archivo llamado servicios.json en la misma carpeta que el script. Este archivo debe contener una lista de diccionarios, uno por cada servicio a monitorear:CampoTipoDescripciónEjemplonombrestringNombre descriptivo del servicio."Web Principal FII"dominiostringDominio o IP a verificar."www.fii.gob.ve"puertointPuerto de conexión SSL (opcional, por defecto 443).443email_alertastringCorreo donde se enviarán las alertas."soporte@fii.gob.ve"jefe_serviciosstringNombre o cargo del responsable IT."Ing. Pérez"desarrolladorstringNombre del desarrollador a notificar."Juan Rojas"Ejemplo de servicios.json:JSON[
    {
        "nombre": "Servidor Principal",
        "dominio": "csice.fii.gob.ve",
        "puerto": 443,
        "email_alerta": "alerta-csice@fii.gob.ve",
        "jefe_servicios": "Jefe de IT",
        "desarrollador": "Equipo Backend"
    },
    {
        "nombre": "Dominio HTTP (Excepción)",
        "dominio": "publicador.fii.gob.ve",
        "puerto": 443,
        "email_alerta": "direccion@fii.gob.ve",
        "jefe_servicios": "Dirección General",
        "desarrollador": "N/A"
    }
]
🚦 4. Modo de Ejecución y Lógica de AlertasEl script utiliza un argumento de línea de comandos para determinar su comportamiento de envío de correos:1. Modo Diario: Alerta SilenciosaEste modo se utiliza para la ejecución frecuente (ej. diaria a las 6:00 a.m.). Solo genera email si la acción es urgente.Bashpython ssl_checker.py --modo-alerta
Estado DetectadoUmbralAcción de EmailVENCIDO 🔴(Días < 0)SÍ: Alerta inmediata.ERROR ❌(Conexión/SSL fallida)SÍ: Alerta inmediata.PRÓXIMO A VENCERSE ⚠️(Días $\le$ 7)SÍ: Alerta inmediata (advertencia urgente).VÁLIDO ✅(Días > 7)NO: Solo registra en consola (silencioso).RECOMENDACIÓN 🟡 (publicador.fii.gob.ve)(Error de conexión)NO: Se omite.2. Modo Semanal: Reporte CompletoEste modo se utiliza para el resumen semanal (ej. cada Lunes a las 7:00 a.m.). Envía un email con el estado de TODOS los servicios.Bashpython ssl_checker.py
Estado DetectadoAcción de EmailTodos los estados (incluido VÁLIDO)SÍ: Se envía el reporte completo.RECOMENDACIÓN 🟡 (publicador.fii.gob.ve)SÍ: Se envía la nota de recomendación SSL.📅 5. Programación (Crontab en Linux/VM)Para automatizar la ejecución, utiliza la tabla de tareas de Linux (crontab -e). Asegúrate de usar la ruta completa al ejecutable de Python de tu entorno virtual (.venv/bin/python).Bash# Ejecución diaria a las 6:00 AM para alertas críticas (silencioso para dominios OK)
0 6 * * * /ruta/al/venv/bin/python /ruta/al/Alertas-SSL/ssl_checker.py --modo-alerta > /dev/null 2>&1

# Ejecución semanal a las 7:00 AM del Lunes para reporte completo de todos los estados
0 7 * * 1 /ruta/al/venv/bin/python /ruta/al/Alertas-SSL/ssl_checker.py
(Recuerda ajustar la ruta (/ruta/al/venv/bin/python y /ruta/al/Alertas-SSL/ssl_checker.py) a tu configuración específica de la VM.)
