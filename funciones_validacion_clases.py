from modelo import *
from sqlalchemy.orm import Session 
from schemas import *
from datetime import datetime
from fastapi import HTTPException

#FUNCIONES PARA VALIDAR CLASES
#VERIFICAR CUPOS
def verify_cupos(cupos:int):
    if cupos<1 or cupos>15:
        return False
    return True


# Validación de horas
def validar_horas(hora_inicio: time, hora_fin: time):
    if hora_fin <= hora_inicio:
        raise HTTPException(status_code=400, detail="La hora de fin no puede ser menor a la hora de inicio.")

    if (hora_fin.hour - hora_inicio.hour) * 60 + (hora_fin.minute - hora_inicio.minute) != 120:
        raise HTTPException(status_code=400, detail="La duración de la clase debe ser de 2 horas.")

# Validación de horarios disponibles
def validar_horarios_disponibles(hora_inicio: time):
    horarios_permitidos = [
        time(8, 0),
        time(10, 0),
        time(16, 0),
        time(18, 0),
    ]
    
    if hora_inicio not in horarios_permitidos:
        raise HTTPException(status_code=400, detail="La hora de inicio debe ser en uno de los horarios permitidos: 8-10am, 10am-12pm, 4-6pm, 6-8pm.")

# Validación de clases duplicadas
def validar_clases_duplicadas(datos_clase, db: Session):
    clase_existente = db.query(Clase).filter(
        Clase.sede == datos_clase.sede,
        Clase.nivel == datos_clase.nivel,
        Clase.fecha == datos_clase.fecha,
        Clase.hora_inicio == datos_clase.hora_inicio
    ).first()

    if clase_existente:
        raise HTTPException(status_code=400, detail="Ya existe una clase para esta sede, nivel y horario.")

# Validación de conflictos de horario para el profesor
def validar_conflictos_profesor(documento_profesor: str, fecha: datetime, hora_inicio: time, db: Session):
    clase_conflicto = db.query(Clase).filter(
        Clase.documento_profesor == documento_profesor,
        Clase.fecha == fecha,
        Clase.hora_inicio == hora_inicio
    ).first()

    if clase_conflicto:
        raise HTTPException(status_code=400, detail="El profesor ya tiene clase asignada en este horario.")

# Validación de la fecha
def validar_fecha(fecha: datetime):
    if fecha < datetime.now().date():
        raise HTTPException(status_code=400, detail="La fecha no puede ser anterior al día de hoy.")
