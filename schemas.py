from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date, time
from sqlalchemy import Enum

# Modelos

class AdministradorBase(BaseModel):
    administrador_id: int
    usuario: str
    contraseña: str


class ProfesorBase(BaseModel):
    documento: str
    tipo_de_documento: Literal['cedula', 'cedula extranjera']
    nombre: str
    apellido: str
    fecha_nacimiento: date
    genero: Literal["masculino", "femenino", "otro"]
    celular: str
    correo: str
    direccion: str
    usuario: str
    contraseña: str
    fecha_contratacion: Optional[date] = None  
    foto_perfil: Optional[str] = None


class EstudianteBase(BaseModel):
    documento: str
    tipo_de_documento: Literal['cedula', 'cedula extranjera', 'tarjeta de identidad']
    nombre: str
    apellido: str
    fecha_nacimiento: date
    genero: Literal["masculino", "femenino", "otro"]
    celular: str
    correo: str
    direccion: str
    sede: Literal['madrid', 'mosquera', 'funza', 'facatativa', 'bogota']
    usuario: str
    contraseña: str
    nivel_actual: Literal['beginner', 'basic 1', 'basic 2', 'intermediate', 'advanced']
    fecha_inscripcion: Optional[date] = None 
    plan: str
    foto_perfil: Optional[str] = None


class NivelBase(BaseModel):
    nombre_nivel: str
    descripcion_nivel: str


class RegistroEstudianteNivelBase(BaseModel):
    documento: str
    nivel: Literal['beginner', 'basic 1', 'basic 2', 'intermediate', 'advanced']  
    speaking: float
    listening: float
    reading: float
    writing: float
    nota_evaluacion: Optional[float] = None
    aprobacion: Optional[bool] = None 


class ClaseBase(BaseModel):
    id_clase: Optional[int]=None 
    sede: Literal['madrid', 'mosquera', 'funza', 'facatativa', 'bogota']
    nivel: Literal['beginner', 'basic 1', 'basic 2', 'intermediate', 'advanced']
    hora_inicio: time 
    hora_fin: time 
    fecha: date
    documento_profesor: str
    cupos: int
    administrador: Optional[int] = None

class VerficarUsuario(BaseModel):
    tipo_de_documento: Literal['cedula','cedula extranjera','tarjeda de identidad']
    documento: str


class ReservaBase(BaseModel):
    id_clase: int
    documento_estudiante: str


class AsistenciaBase(BaseModel):
    id_asistencia: Optional [int] = None
    id_reserva: int
    asistencia: bool


class ObservacionBase(BaseModel):
    id_observacion: Optional [int] = None
    fecha: Optional[date] = None  
    descripcion: str
    documento: str
    creada_por: str

class PlanBase(BaseModel):
    nombre: str
    horas_semanales: int
    costo: int
    meses: int


class CuentaBase(BaseModel):
    pagare: int
    documento: str
    saldo: int
    pago_minimo: int
    fecha_proximo_pago: date
    dias_mora: Optional[int] = None


class PagoBase(BaseModel):
    id_pago: Optional [int] =None
    fecha: Optional[date] = None 
    valor: int
    cuenta_documento: str


class SolicitudBase(BaseModel):
    id_solicitud: Optional[int] = None
    documento: str
    descripcion: str
    respuesta: Optional[str] = None
    contestacion: bool = False
    fecha_creacion: Optional[date] = None  


class ComunicadoBase(BaseModel):
    id_comunicado:  Optional [int] =None
    administrador: Optional[int] = None
    titulo: str
    descripcion: str
    foto: Optional[str] = None


# Clase que maneja los logins
class LoginBase(BaseModel):
    usuario: str
    contraseña: str
    rol: Optional[str] = None

