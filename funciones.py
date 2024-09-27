from modelo import *
from sqlalchemy.orm import Session 
from schemas import *
#si no les agarra descarguen esto 'pip install fastapi uvicorn python-jose[cryptography] passlib'
from jose import jwt
from datetime import datetime,timedelta
from passlib.context import CryptContext



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


#OBTENER DATOS DE LA CUENTA
def obtener_datos_cuenta(documento:str, db:Session):
    #Verifica si la cuenta esta creada o no
    cuenta = db.query(Cuenta).filter(Cuenta.documento == documento).first()
    return cuenta
