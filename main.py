from fastapi import FastAPI ,HTTPException,Depends,status
from conexion import crear,get_db
from modelo import *
from sqlalchemy.orm import Session 
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
#si no les agarra descarguen esto 'pip install fastapi uvicorn python-jose[cryptography] passlib'
from jose import JWTError,jwt
from datetime import datetime,timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from funciones import *

# DOCUMENTEN EL CODIGO (COMENTAR) PARA QUE NO SE HAGA UN SANCOCHO XFA
app=FastAPI()

#PERMITIR EL USO DE LA API
app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#CREAR LAS TABLAS
base.metadata.create_all(bind=crear)





# METODO DE LOGIN 
@app.post("/login", response_model=dict)
async def login(datos_login: LoginBase, db: Session = Depends(get_db)):
    # Obtener los datos del usuario (puede ser Administrador, Estudiante o Profesor)
    usuario = obtener_datos_usuario(datos_login.usuario, db)
    
    # Si no se encuentra el usuario en ninguna tabla
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario incorrecto")
    
    # Verificar la contraseña
    if not verificar_contraseña_login(datos_login.contraseña, usuario.contraseña):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    
    # Crear los datos del token
    datos_token = {}


    #  crear datos de usuario según el rol 
    if isinstance(usuario, Administrador):
        datos_token= {
            "rol": "administrador",
                "administrador_id": usuario.administrador_id,
                "correo": usuario.correo,
                "usuario": usuario.usuario
            
        }
    
    if isinstance(usuario, Estudiante):
        datos_token = {
            "rol": "estudiante",
                "documento": usuario.documento,
                "tipo_de_documento": usuario.tipo_de_documento,
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "celular": usuario.celular,
                "correo": usuario.correo,
                "usuario": usuario.usuario,
                "sede": usuario.sede
            }
        

    if isinstance(usuario, Profesor):
        datos_token =  {
            "rol": "profesor",
                "documento": usuario.documento,
                "tipo_de_documento": usuario.tipo_de_documento,
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "celular": usuario.celular,
                "correo": usuario.correo,
                "usuario": usuario.usuario
            }

     # Generar el token JWT con la función creada previamente
    token_acceso = crear_token(datos=datos_token, tiempo_expiracion=timedelta(minutes=MINUTOS_DE_EXPIRACION))
    return {"access_token": token_acceso, "token_type": "bearer"}




# El URL del login para la obtención del token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Excepción de credenciales inválidas
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudo validar el token",
    headers={"WWW-Authenticate": "Bearer"},
)

# Función para obtener el usuario actual basado en el token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
       
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
        
        # Obtener el nombre de usuario (u otro identificador) desde el token
        usuario: str = payload.get("usuario")
        if usuario is None:
            raise credentials_exception
        
    except JWTError:
        # Si hay un error en el token o ha expirado
        raise credentials_exception

    # Obtener los datos del usuario desde la base de datos
    user = obtener_datos_usuario(usuario, db)
    if user is None:
        raise credentials_exception
    
    return user

# Endpoint protegido para obtener el usuario actual
@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    if current_user.__class__.__name__.lower()=="administrador":
        return {
                "rol": "administrador",
                "administrador_id": current_user.administrador_id,
                "correo": current_user.correo,
                "usuario": current_user.usuario
        }
    elif current_user.__class__.__name__.lower()=="estudiante":
        return{
                 "rol": "estudiante",
                "documento": current_user.documento,
                "tipo_de_documento": current_user.tipo_de_documento,
                "nombre": current_user.nombre,
                "apellido": current_user.apellido,
                "celular": current_user.celular,
                "correo": current_user.correo,
                "usuario": current_user.usuario,
                "sede": current_user.sede
        }   
    elif current_user.__class__.__name__.lower()=="profesor":
        return{
                 "rol": "profesor",
                "documento": current_user.documento,
                "tipo_de_documento": current_user.tipo_de_documento,
                "nombre": current_user.nombre,
                "apellido": current_user.apellido,
                "celular": current_user.celular,
                "correo": current_user.correo,
                "usuario": current_user.usuario,
        }          
 
            


   


   
    
























































































































#METODO PARA AGREGAR ADMINISTRADORES
@app.post("/añadiradministrador")
#DATOS_ADMINISTRADOR SON LOS DATOS  QUE ESTAN INGRESANDO
async def add_admin(datos_administador:AdministradorBase , db: Session =Depends(get_db)):
    #ESTA VARIABLE VALIDA SI YA EXISTE ALGUN DATO SIMILAR AL QUE SE ESTA INGRESANDO , CON EL FILTER ESPECIFICAN QUE ATRIBUTO QUIEREN VERIFICAR 
    existe_id=db.query(Administrador).filter(Administrador.administrador_id==datos_administador.administrador_id).first()

    #SI YA EXISTE UN ID Y UN USUARIO IGUAL , SURGE EXCEPTION
    if existe_id:
        raise HTTPException (status_code=400, detail=f"el id de administrador '{datos_administador.administrador_id}' ya esta en uso ")       
    if usuario_existe_globalmente(datos_administador.usuario, db):
        raise HTTPException(status_code=400, detail=f"El usuario '{datos_administador.usuario}' ya está en uso ")
 
    #SE VERIFICA SI LA CONTRASEÑA ES VALIDA
    if not verificar_contraseña(datos_administador.contraseña):
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres , incluyendo números , caracteres especiales y  mayusculas")
    #ENCRIPTACION DE LA CONTRASEÑA
    encriptacion = bcrypt.hashpw(datos_administador.contraseña.encode('utf-8'),bcrypt.gensalt())

    #SE CREA UN NUEVO ADMIN CON LOS DATOS QUE INGRESEN , SEGUIDO A ESTO SE HACE EL ADD, COMMIT Y EL REFRESH A LA DATABASE
    nuevo_administrador=Administrador(administrador_id=datos_administador.administrador_id,correo=datos_administador.correo,usuario=datos_administador.usuario,contraseña=encriptacion.decode('utf-8'))

    #TRY PARA CAPTURAR UN POSIBLE ERROR
    try:
        db.add(nuevo_administrador)
        db.commit()
        db.refresh(nuevo_administrador)
        #MENSAJE BONITO JSJA
        return "administrador agregado exitosamente"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")



#METODO PARA AÑADIR ESTUDIANTES
@app.post("/añadirestudiante")
async def añadir_estudiante(datos_estudiante:EstudianteBase, db: Session =Depends(get_db)):
    existe_documento=db.query(Estudiante).filter(Estudiante.documento==datos_estudiante.documento).first()
    if existe_documento:
        raise HTTPException (status_code=400, detail=f"el documento '{datos_estudiante.documento}' ya esta en uso ") 
          
    if usuario_existe_globalmente(datos_estudiante.usuario, db):
        raise HTTPException(status_code=400, detail=f"El usuario '{datos_estudiante.usuario}' ya está en uso ")  
    
    if not verificar_contraseña(datos_estudiante.contraseña):
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres , incluyendo números , caracteres especiales y  mayusculas")
    
    encriptacion=bcrypt.hashpw(datos_estudiante.contraseña.encode('utf-8'),bcrypt.gensalt())

    nuevo_estudiante=Estudiante(
        documento=datos_estudiante.documento,tipo_de_documento=datos_estudiante.tipo_de_documento,nombre=datos_estudiante.nombre,
        apellido=datos_estudiante.apellido,celular=datos_estudiante.celular,correo=datos_estudiante.correo,usuario=datos_estudiante.usuario,contraseña=encriptacion.decode('utf-8'),
        sede=datos_estudiante.sede)
    
    try:
        db.add(nuevo_estudiante)
        db.commit()
        db.refresh(nuevo_estudiante)
        return "Estudiante agregado exitosamente"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")
    


#METODO PARA AÑADIR PROFESORES
@app.post("/añadirprofesor")
async def añadir_profesor(datos_profesor:ProfesorBase, db: Session =Depends(get_db)):
    existe_documento=db.query(Profesor).filter(Profesor.documento==datos_profesor.documento).first()
    if existe_documento:
        raise HTTPException (status_code=400, detail=f"el documento '{datos_profesor.documento}' ya esta en uso ") 
          
    if usuario_existe_globalmente(datos_profesor.usuario, db):
        raise HTTPException(status_code=400, detail=f"El usuario '{datos_profesor.usuario}' ya está en uso ")  
    
    if not verificar_contraseña(datos_profesor.contraseña):
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres , incluyendo números , caracteres especiales y  mayusculas")
    
    encriptacion=bcrypt.hashpw(datos_profesor.contraseña.encode('utf-8'),bcrypt.gensalt())

    nuevo_profesor=Profesor(
        documento=datos_profesor.documento,tipo_de_documento=datos_profesor.tipo_de_documento,nombre=datos_profesor.nombre,
        apellido=datos_profesor.apellido,celular=datos_profesor.celular,correo=datos_profesor.correo,usuario=datos_profesor.usuario,contraseña=encriptacion.decode('utf-8'),)
    
    try:
        db.add(nuevo_profesor)
        db.commit()
        db.refresh(nuevo_profesor)
        return "Profesor agregado exitosamente"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")
    

## METODO PARA CONSULTAR TODOS LOS ESTUDIANTES
@app.get("/obtenerestudiantes")
async def get_estudiantes(db: Session = Depends(get_db)):
    try:
        estudiantes = db.query(Estudiante).all()  # Obtener  todos los estudiantes
        return estudiantes  # retornar los estudiantes,claramente no?

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

## METODO PARA CONSULTAR TODOS LOS PROFESORES
@app.get("/obtenerprofesores")
async def get_profesores(db: Session = Depends(get_db)):
    try:
        profesores = db.query(Profesor).all()  # Obtener  todos los estudiantes
        return profesores  # retornar los estudiantes,claramente no?

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))


#METODO PARA ELIMINAR UN ESTUDIANTE
@app.delete("/eliminarestudiante/{documento}")
async def delete_estudiante(documento:str,db:Session=Depends(get_db)):
    estudiante_encontrado=db.query(Estudiante).filter(documento==Estudiante.documento).first()
    if estudiante_encontrado:
        db.delete(estudiante_encontrado)
        db.commit()
        return {"":f"estudiante con documento {documento} eliminado"}
    else:
        raise HTTPException (status_code=400, detail="no se encontro estudiante")





