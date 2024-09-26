from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, Date, Time, ForeignKey, event, delete
from sqlalchemy.orm import relationship, backref
from conexion import base
from sqlalchemy.sql import func


# Creación de tablas

class Administrador(base):
    __tablename__ = 'administrador'
    administrador_id = Column(Integer, primary_key=True)
    usuario = Column(String(30), nullable=False)
    contraseña = Column(String(60), nullable=False)


class Profesor(base):
    __tablename__ = 'profesores'
    documento = Column(String(15), primary_key=True)
    tipo_de_documento = Column(Enum('cedula', 'cedula extranjera'), nullable=False)
    nombre = Column(String(20), nullable=False)
    apellido = Column(String(20), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(Enum('masculino', 'femenino', 'otro') ,nullable=False)
    celular = Column(String(10), nullable=False)
    correo = Column(String(30), nullable=False)
    direccion = Column(String(200), nullable=False)
    usuario = Column(String(30), nullable=False)
    contraseña = Column(String(60), nullable=False)
    fecha_contratacion = Column(Date, nullable=True, default=func.now())
    foto_perfil = Column(String(300), nullable=True)


class Estudiante(base):
    __tablename__ = 'estudiantes'
    documento = Column(String(15), primary_key=True)
    tipo_de_documento = Column(Enum('cedula', 'cedula extranjera', 'tarjeta de identidad'), nullable=False)
    nombre = Column(String(20), nullable=False)
    apellido = Column(String(20), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(Enum('masculino', 'femenino', 'otro') ,nullable=False)
    celular = Column(String(10), nullable=False)
    correo = Column(String(30), nullable=False)
    direccion = Column(String(200), nullable=False)
    sede = Column(Enum('madrid', 'mosquera', 'funza', 'facatativa', 'bogota'), nullable=False)
    usuario = Column(String(30), nullable=False)
    contraseña = Column(String(60), nullable=False)
    nivel_actual = Column(Enum('beginner', 'basic 1', 'basic 2', 'intermediate', 'advanced'), nullable=False)
    fecha_inscripcion = Column(Date, nullable=True, default=func.now())
    plan = Column(String(30), ForeignKey('planes.nombre'), nullable=False)
    foto_perfil = Column(String(300), nullable=True)


class Nivel(base):
    __tablename__ = 'niveles'
    nombre_nivel = Column(String(30), primary_key=True, nullable=False)
    descripcion_nivel = Column(String(300), primary_key=True, nullable=False)


class RegistroEstudianteNivel(base):
    __tablename__ = 'registro_estudiante_nivel'
    documento = Column(String(15), ForeignKey('estudiantes.documento'), primary_key=True)
    nivel = Column(String(30), ForeignKey('niveles.nombre_nivel'), primary_key=True)
    speaking = Column(Float, nullable=False)
    listening = Column(Float, nullable=False)
    reading = Column(Float, nullable=False)
    writing = Column(Float, nullable=False)
    nota_evaluacion = Column(Float, nullable=True)
    aprobacion = Column(Boolean, nullable=True)

    # Función para calcular automáticamente la nota de evaluación
    def calcular_nota_evaluacion(self):
        self.nota_evaluacion = (self.speaking + self.listening + self.reading + self.writing) / 4.0
        self.aprobacion = self.nota_evaluacion >= 3.0


# Evento para calcular la nota antes de insertar o actualizar el registro
event.listen(RegistroEstudianteNivel, 'before_insert', RegistroEstudianteNivel.calcular_nota_evaluacion)
event.listen(RegistroEstudianteNivel, 'before_update', RegistroEstudianteNivel.calcular_nota_evaluacion)


class Clase(base):
    __tablename__ = 'clases'
    id_clase = Column(Integer, primary_key=True, autoincrement=True)
    sede = Column(Enum('madrid', 'mosquera', 'funza', 'faca', 'bogota'), nullable=False)
    nivel = Column(Enum('beginner', 'basic 1', 'basic 2', 'intermediate', 'advanced'), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    fecha = Column(Date, nullable=False)
    documento_profesor = Column(String(15), ForeignKey('profesores.documento', ondelete='CASCADE'), nullable=False)
    cupos = Column(Integer, nullable=False)
    administrador = Column(Integer, ForeignKey('administrador.administrador_id'), nullable=True)


class Reserva(base):
    __tablename__ = 'reservas'
    id_reserva = Column(Integer, primary_key=True, autoincrement=True)
    id_clase = Column(Integer, ForeignKey('clases.id_clase', ondelete='CASCADE'), nullable=False)
    documento_estudiante = Column(String(15), ForeignKey('estudiantes.documento' , ondelete='CASCADE'), nullable=False)


class Asistencia(base):
    __tablename__ = 'asistencias'
    id_asistencia = Column(Integer, primary_key=True, autoincrement=True)
    id_reserva = Column(Integer, ForeignKey('reservas.id_reserva' , ondelete='CASCADE'), nullable=False,unique=True)
    asistencia = Column(Boolean, default=False)


class Observacion(base):
    __tablename__ = 'observaciones'
    id_observacion = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=True, default=func.now())
    descripcion = Column(String(300), nullable=False)
    documento = Column(String(15), ForeignKey('estudiantes.documento', ondelete='CASCADE'), nullable=False)
    creada_por =Column(String(50), nullable=False)


class Plan(base):
    __tablename__ = 'planes'
    nombre = Column(String(30), primary_key = True)
    horas_semanales = Column(Integer, nullable=False)
    costo = Column(Integer, nullable=False)
    meses = Column(Integer, nullable=False)


class Cuenta(base):
    __tablename__ = 'cuentas'
    documento = Column(String(15), ForeignKey('estudiantes.documento', ondelete='CASCADE'), primary_key=True)
    saldo = Column(Integer, nullable=False)
    pago_minimo = Column(Integer, nullable=False)
    fecha_proximo_pago = Column(Date, nullable=False)
    dias_mora = Column(Integer)

    


class Pago(base):
    __tablename__ = 'pagos'
    id_pago = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False, default=func.now())
    valor = Column(Integer, nullable=False)
    cuenta_documento = Column(String(15), ForeignKey('cuentas.documento', ondelete='CASCADE'), nullable=False)


class Solicitud(base):
    __tablename__ = 'solicitudes'
    id_solicitud = Column(Integer, primary_key=True, autoincrement=True)
    documento = Column(String(15), ForeignKey('estudiantes.documento', ondelete='CASCADE'), nullable=False)
    descripcion = Column(String(400), nullable=False)
    respuesta = Column(String(400), nullable=True)
    contestacion = Column(Boolean, default=False, nullable=False)
    fecha_creacion = Column(Date, nullable=False, default=func.now())


class Comunicado(base):
    __tablename__ = 'comunicados'
    id_comunicado = Column(Integer, primary_key=True, autoincrement=True)
    administrador = Column(Integer, ForeignKey('administrador.administrador_id'), nullable=True)
    titulo = Column(String(400), nullable=False)
    descripcion = Column(String(400), nullable=False)
    foto = Column(String(300), nullable=True)
