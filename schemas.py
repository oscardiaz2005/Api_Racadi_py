from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date, time

#modelos

class AdministradorBase(BaseModel):
    administrador_id: int
    correo: str
    usuario: str
    contraseña: str

class ProfesorBase(BaseModel):
    documento: str
    tipo_de_documento: Literal['cedula', 'cedula extranjera']
    nombre: str
    apellido: str
    celular: str
    correo: str
    usuario: str
    contraseña: str

class EstudianteBase(BaseModel):
    documento: str
    tipo_de_documento: Literal['cedula', 'cedula extranjera', 'tarjeta de identidad']
    nombre: str
    apellido: str
    celular: str
    correo: str
    usuario: str
    contraseña: str
    sede: Literal['madrid', 'mosquera', 'funza', 'faca', 'bogota']

class NivelBase(BaseModel):
    nombre_nivel: str

class RegistroEstudianteNivelBase(BaseModel):
    documento: str
    nivel: str  # Enum: Puedes usar Literal aquí si defines los valores posibles
    speaking: float
    listening: float
    reading: float
    writing: float
    nota_evaluacion: Optional[float] = None
    aprobacion: Optional[bool] = None

class ClaseBase(BaseModel):
    id_clase: int
    sede: Literal['madrid', 'mosquera', 'funza', 'faca', 'bogota']
    nivel: Literal['beginner', 'basic 1', 'basic 2', 'intermediate', 'advanced']
    hora_inicio: time
    hora_fin: time
    fecha: date
    documento_profesor: str
    cupos: int
    administrador: int

class ReservaBase(BaseModel):
    id_reserva: int
    id_clase: int
    documento_estudiante: str

class AsistenciaBase(BaseModel):
    id_asistencia: int
    id_reserva: int
    asistencia: bool

class ObservacionBase(BaseModel):
    id_observacion: int
    fecha: date
    descripcion: str
    documento: str

class PlanBase(BaseModel):
    id_plan: str
    nombre: str
    horas_semanales: int
    costo: int

class CuentaBase(BaseModel):
    documento: str
    saldo: int
    pago_minimo: int
    fecha_proximo_pago: date
    dias_mora: Optional[int]
    plan: str

class PagoBase(BaseModel):
    id_pago: int
    fecha: date
    valor: int
    cuenta: str

class SolicitudBase(BaseModel):
    id_solicitud: int
    documento: str
    descripcion: str
    respuesta: Optional[str]
    costestacion: bool

class ComunicadoBase(BaseModel):
    id_comunicado: int
    administrador: int
    descripcion: str

#Clase que maneja los logins
class LoginBase(BaseModel):
    usuario: str
    contraseña: str
    rol: Optional[str] = None 
    mensaje: Optional[str] = None 