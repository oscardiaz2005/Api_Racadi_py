from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, Date, Time, ForeignKey, event
from sqlalchemy.orm import relationship
from conexion import base 


#creacion de tablas 

class Administrador(base):
    __tablename__ = 'administrador'
    administrador_id = Column(Integer, primary_key=True)
    correo = Column(String(40), nullable=False)
    usuario = Column(String(30), nullable=False)
    contraseña = Column(String(60), nullable=False)

class Profesor(base):
    __tablename__ = 'profesores'
    documento = Column(String(15), primary_key=True)
    tipo_de_documento = Column(Enum('cedula', 'cedula extranjera'), nullable=False)
    nombre = Column(String(20), nullable=False)
    apellido = Column(String(20), nullable=False)
    celular = Column(String(10), nullable=False)
    correo = Column(String(30), nullable=False)
    usuario = Column(String(30), nullable=False)
    contraseña = Column(String(60), nullable=False)

class Estudiante(base):
    __tablename__ = 'estudiantes'
    documento = Column(String(15), primary_key=True)
    tipo_de_documento = Column(Enum('cedula', 'cedula extranjera', 'tarjeta de identidad'), nullable=False)
    nombre = Column(String(20), nullable=False)
    apellido = Column(String(20), nullable=False)
    celular = Column(String(10), nullable=False)
    correo = Column(String(30), nullable=False)
    usuario = Column(String(30), nullable=False)
    contraseña = Column(String(60), nullable=False)
    sede = Column(Enum('madrid', 'mosquera', 'funza', 'faca', 'bogota'), nullable=False)

class Nivel(base):
    __tablename__ = 'niveles'
    nombre_nivel = Column(String(30), primary_key=True, nullable=False)

class RegistroEstudianteNivel(base):
    __tablename__ = 'registro_estudiante_nivel'
    documento = Column(String(15), ForeignKey('estudiantes.documento'), primary_key=True)
    nivel = Column(String(30), ForeignKey('niveles.nombre_nivel'), primary_key=True)
    speaking = Column(Float, nullable=False)
    listening = Column(Float, nullable=False)
    reading = Column(Float, nullable=False)
    writing = Column(Float, nullable=False)
    nota_evaluacion = Column(Float)
    aprobacion = Column(Boolean, nullable=False)

#funcion para calcular la nota de la evaluacion automaticamente despues de agregar datos
def calcular_nota_evaluacion(mapper, connection, target):
    target.nota_evaluacion = (target.speaking + target.listening + target.reading + target.writing) / 4.0
    target.aprobacion = target.nota_evaluacion >= 3.0

event.listen(RegistroEstudianteNivel, 'before_insert', calcular_nota_evaluacion)
event.listen(RegistroEstudianteNivel, 'before_update', calcular_nota_evaluacion)

class Clase(base):
    __tablename__ = 'clases'
    id_clase = Column(Integer, primary_key=True, autoincrement=True)
    sede = Column(Enum('madrid', 'mosquera', 'funza', 'faca', 'bogota'), nullable=False)
    nivel = Column(Enum('beginner', 'basic 1', 'basic 2', 'intermediate', 'advanced'), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    fecha = Column(Date, nullable=False)
    documento_profesor = Column(String(15), ForeignKey('profesores.documento'), nullable=False)
    cupos = Column(Integer, nullable=False)
    administrador = Column(Integer, ForeignKey('administrador.administrador_id'))

class Reserva(base):
    __tablename__ = 'reservas'
    id_reserva = Column(Integer, primary_key=True, autoincrement=True)
    id_clase = Column(Integer, ForeignKey('clases.id_clase'))
    documento_estudiante = Column(String(15), ForeignKey('estudiantes.documento'))

class Asistencia(base):
    __tablename__ = 'asistencias'
    id_asistencia = Column(Integer, primary_key=True, autoincrement=True)
    id_reserva = Column(Integer, ForeignKey('reservas.id_reserva'), nullable=False)
    asistencia = Column(Boolean, default=False)

class Observacion(base):
    __tablename__ = 'observaciones'
    id_observacion = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(String(300), nullable=False)
    documento = Column(String(15), ForeignKey('estudiantes.documento'), nullable=False)

class Plan(base):
    __tablename__ = 'planes'
    id_plan = Column(String(10), primary_key=True)
    nombre = Column(String(30), nullable=False)
    horas_semanales = Column(Integer, nullable=False)
    costo = Column(Integer, nullable=False)

class Cuenta(base):
    __tablename__ = 'cuentas'
    documento = Column(String(15), ForeignKey('estudiantes.documento'), primary_key=True)
    saldo = Column(Integer, nullable=False)
    pago_minimo = Column(Integer, nullable=False)
    fecha_proximo_pago = Column(Date, nullable=False)
    dias_mora = Column(Integer)
    plan = Column(String(10), ForeignKey('planes.id_plan'), unique=True)

class Pago(base):
    __tablename__ = 'pagos'
    id_pago = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    valor = Column(Integer, nullable=False)
    cuenta = Column(String(15), ForeignKey('cuentas.documento'), nullable=False)

class Solicitud(base):
    __tablename__ = 'solicitudes'
    id_solicitud = Column(Integer, primary_key=True, autoincrement=True)
    documento = Column(String(15), ForeignKey('estudiantes.documento'), nullable=False)
    descripcion = Column(String(400), nullable=False)
    respuesta = Column(String(400))
    costestacion = Column(Boolean, default=False, nullable=False)

class Comunicado(base):
    __tablename__ = 'comunicados'
    id_comunicado = Column(Integer, primary_key=True, autoincrement=True)
    administrador = Column(Integer, ForeignKey('administrador.administrador_id'), nullable=False)
    descripcion = Column(String(400), nullable=False)
