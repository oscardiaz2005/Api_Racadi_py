from modelo import *
from sqlalchemy.orm import Session 
from schemas import *
#si no les agarra descarguen esto 'pip install fastapi uvicorn python-jose[cryptography] passlib'
from jose import jwt
from datetime import datetime,timedelta
from passlib.context import CryptContext
from fastapi import HTTPException
from sqlalchemy import or_ , and_





#CONFIGURACION PARA LOS TOKENS
SECRET_KEY="racadiacademyadso"
ALGORITMO = "HS256" 
MINUTOS_DE_EXPIRACION = 30


## Encriptacion de contraseñas
encriptacion = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Función para verificar la contraseña
def verificar_contraseña_login(contraseña, hashed_contraseña):
    return encriptacion.verify(contraseña, hashed_contraseña) 

    
# Función para obtener el hash de una contraseña
def encriptar_contraseña(password):
    return encriptacion.hash(password)





#FUNCION PARA VALIDAR CONTRASEÑAS
def verificar_contraseña(contraseña):
    numeros = set("0123456789")
    caracteresEspeciales = set('@#$%^&*()_+-={}[]|\\:;"\'<>,./?~`')
    mayusculas = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    existe_numero = False
    existe_char_especial = False
    existe_mayuscula = False
    
    for char in contraseña:
        if char in numeros:
            existe_numero = True
        elif char in caracteresEspeciales:
            existe_char_especial = True
        elif char in mayusculas:
            existe_mayuscula = True
        
        if existe_numero and existe_char_especial and existe_mayuscula:
            break

    contraseña_valida = (existe_numero and existe_char_especial and existe_mayuscula and len(contraseña) >= 8)
    return contraseña_valida


#FUNCION PARA VALIDAR LONGITUD DE NUMERO
def verify_cel(cel):
    if len(cel)==10:
        return True
    else :
        return False




#FUNCION PARA VERIFICAR SI EL USUARIO EXISTE GLOBALMENTE 
def usuario_existe_globalmente(usuario: str, db: Session):
    # Verificar en la tabla de Administradores
    existe_en_admin = db.query(Administrador).filter(Administrador.usuario == usuario).first()
    if existe_en_admin:
        return True
    
    # Verificar en la tabla de Estudiantes
    existe_en_estudiante = db.query(Estudiante).filter(Estudiante.usuario == usuario).first()
    if existe_en_estudiante:
        return True
    
    # Verificar en la tabla de Profesores
    existe_en_profesor = db.query(Profesor).filter(Profesor.usuario == usuario).first()
    if existe_en_profesor:
        return True
    
    # Si no se encuentra en ninguna tabla, entonces no existe xd ajsj , se devuelve false
    return False


#FUNCION PARA OBTENER DATOS DE UN USUARIO
def obtener_datos_usuario(usuario: str, db: Session):
    # Verificar en la tabla de Administradores
    existe_en_admin = db.query(Administrador).filter(Administrador.usuario == usuario).first()
    if existe_en_admin:
        return existe_en_admin
    
    # Verificar en la tabla de Estudiantes
    existe_en_estudiante = db.query(Estudiante).filter(Estudiante.usuario == usuario).first()
    if existe_en_estudiante:
        return existe_en_estudiante
    
    # Verificar en la tabla de Profesores
    existe_en_profesor = db.query(Profesor).filter(Profesor.usuario == usuario).first()
    if existe_en_profesor:
        return existe_en_profesor
    
    # Si no se encuentra en ninguna tabla, entonces no existe xd ajsj , se devuelve none
    return None



#funcion para validar usuario
def autenticar_usuario(db : Session , usuario: str, contraseña: str):
    usuario = obtener_datos_usuario(db, usuario)
    if not usuario:
        return False
    if not verificar_contraseña(contraseña, usuario["contraseña"]):
        return False
    return usuario

#CREAR TOKEN
def crear_token(datos: dict, tiempo_expiracion: timedelta = None):
    dato_codificado = datos.copy()
    if tiempo_expiracion:
        expiracion = datetime.utcnow() + tiempo_expiracion
    else:
        expiracion = datetime.utcnow() + timedelta(minutes=15)

    dato_codificado.update({"exp": expiracion})
    jwt_token = jwt.encode(dato_codificado, SECRET_KEY, algorithm=ALGORITMO)
    return jwt_token



#OBTENER NOMBRE Y APELIIDO DE PROFESOR POR DOCUMENTO 
def get_name_teacher_by_dni(documento:str , db:Session):
    P=db.query(Profesor).filter(Profesor.documento==documento).first()
    return f"{P.nombre} {P.apellido}"

 
#FUNCION PARA CONTAR CUANTOS ESTUDIANTES HAN RESERVADO UNA CLASE
def count_students(id_clase:int , db :Session):
    students=db.query(Reserva).filter(id_clase==Reserva.id_clase).all()
    return len(students)


#Funcion para validar las notas 
def verify_notes(speaking:float,listening:float,reading:float,writing:float):
    if speaking>5.0 or speaking<0.0 or listening>5.0 or listening<0.0 or writing>5.0 or writing<0.0 or reading>5.0 or reading<0.0:
        raise HTTPException (status_code=400, detail="las notas no pueden ser inferiores a 0.0 o supriores a 5.0")    


def validar_estudiante(documento:str , db :Session) :
    exist=db.query(Estudiante).filter(documento == Estudiante.documento).first()
    if not exist:
        raise HTTPException(status_code=400, detail="El documento no coincide con ninguno de nuestros estudiantes.")
    
def validar_nivel_estudiante(documento:str , db :Session) :
    estudiante=db.query(Estudiante).filter(documento == Estudiante.documento).first()
    if estudiante.nivel_actual=="advanced":
        raise HTTPException(status_code=400, detail="El documento coincide con un estudiante que se encuentra en el ultimo nivel de apredizaje.")
 
def get_student_level(documento:str , db :Session):
    estudiante=db.query(Estudiante).filter(Estudiante.documento==documento).first()
    return estudiante.nivel_actual


def borrar_registro_fallido(documento:str,nivel:str,db=Session):
    existe_registro_fallido=db.query(RegistroEstudianteNivel).filter( and_(documento==RegistroEstudianteNivel.documento,nivel==RegistroEstudianteNivel.nivel )  ).first()
    if existe_registro_fallido:
        db.delete(existe_registro_fallido)
        db.commit()




def set_next_level(documento:str,db:Session):
    estudiante=db.query(Estudiante).filter(documento == Estudiante.documento).first()
    nivel_actual=estudiante.nivel_actual
    registro_de_nivel=db.query(RegistroEstudianteNivel).filter( and_(documento==RegistroEstudianteNivel.documento,nivel_actual==RegistroEstudianteNivel.nivel )  ).first()
    if registro_de_nivel.aprobacion==True:
        if estudiante.nivel_actual=="beginner":
            estudiante.nivel_actual="basic 1"
        elif estudiante.nivel_actual=="basic 1":
            estudiante.nivel_actual="basic 2"
        elif estudiante.nivel_actual=="basic 2":
            estudiante.nivel_actual="intermediate"    
        elif estudiante.nivel_actual=="intermediate":
            estudiante.nivel_actual="advanced"  
    db.commit()
    db.refresh(estudiante)            




