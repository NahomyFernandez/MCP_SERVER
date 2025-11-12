# Archivo: mcp_server.py

import os
import datetime
from fastmcp import FastMCP
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. Carga e Inicialización ---

load_dotenv()
mcp = FastMCP(name="Asistente Académico UTEQ")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")
    
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Conexión con Supabase establecida.")


# --- 2. Definición de Herramientas (Tools) ---
# TODO EN MINÚSCULAS PARA COINCIDIR CON EL NUEVO ESQUEMA

@mcp.tool
def get_tareas(asignatura: str | None = None, estado: str = "PENDIENTE") -> list:
    """
    Obtiene la lista de tareas de un estudiante desde el SGA.
    Puedes filtrar por 'asignatura' (opcional) o 'estado' (defecto: PENDIENTE).
    Los estados válidos son: PENDIENTE, EN_PROGRESO, COMPLETADA, VENCIDA.
    """
    print(f"-> Tool 'get_tareas' llamada con: asignatura={asignatura}, estado={estado}")
    try:
        # CORRECCIÓN: "tareas" y "materias(nombre_materia)"
        query = supabase.table("tareas").select(
            "titulo, descripcion, fecha_vencimiento, estado, materias(nombre_materia)"
        )
        
        query = query.eq("estado", estado)
        
        if asignatura:
            # CORRECCIÓN: "materias.nombre_materia"
            query = query.ilike("materias.nombre_materia", f"%{asignatura}%")
            
        response = query.execute()
        
        if response.data:
            return response.data
        else:
            return [{"mensaje": "No se encontraron tareas con esos criterios."}]
            
    except Exception as e:
        print(f"Error en get_tareas: {e}")
        return [{"error": f"Error al consultar la base de datos: {str(e)}"}]

@mcp.tool
def get_horario(fecha: str = None) -> list:
    """
    Obtiene el horario de clases para una fecha específica (formato AAAA-MM-DD).
    Si no se provee 'fecha', se usa el día actual (zona horaria de Ecuador -05:00).
    """
    print(f"-> Tool 'get_horario' llamada con: fecha={fecha}")
    try:
        dias_semana_map = {0: "LUNES", 1: "MARTES", 2: "MIERCOLES", 3: "JUEVES", 4: "VIERNES", 5: "SABADO", 6: "DOMINGO"}
        tz_ecuador = datetime.timezone(datetime.timedelta(hours=-5))

        if fecha:
            try:
                target_date = datetime.datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=tz_ecuador)
            except ValueError:
                return [{"error": "Formato de fecha inválido. Usar AAAA-MM-DD."}]
        else:
            target_date = datetime.datetime.now(tz_ecuador)
            
        dia_semana_num = target_date.weekday()
        dia_semana_str = dias_semana_map.get(dia_semana_num)

        if not dia_semana_str or dia_semana_str in ["SABADO", "DOMINGO"]:
            return [{"mensaje": f"No hay clases programadas para el día {target_date.strftime('%Y-%m-%d')} ({dia_semana_str})."}]

        # CORRECCIÓN: "horarios" y "materias(...)"
        response = supabase.table("horarios").select(
            "dia, hora_inicio, hora_fin, materias(nombre_materia, profesor_materia)"
        ).eq("dia", dia_semana_str).order("hora_inicio").execute()

        if response.data:
            return response.data
        else:
            return [{"mensaje": f"No tienes clases programadas para el día {dia_semana_str}."}]

    except Exception as e:
        print(f"Error en get_horario: {e}")
        return [{"error": f"Error al consultar la base de datos: {str(e)}"}]