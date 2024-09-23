from fastapi import FastAPI ,HTTPException,Depends
from conexion import crear,get_db
from modelo import *
from sqlalchemy.orm import Session 
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text


app=FastAPI()

# DOCUMENTEN EL CODIGO (COMENTAR) PARA QUE NO SE HAGA UN SANCOCHO XFA

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
    


#METODO DE LOGIN 
@app.post("/login")
async def login(datos_login: LoginBase, db: Session = Depends(get_db)):
    # Verificar si el usuario existe en Administradores
    usuario_admin = db.query(Administrador).filter(Administrador.usuario == datos_login.usuario).first()
    if usuario_admin:
        if bcrypt.checkpw(datos_login.contraseña.encode('utf-8'), usuario_admin.contraseña.encode('utf-8')):
            return {"rol": "administrador",
                    "datos_admin":{
                        "administrador_id":usuario_admin.administrador_id,
                        "correo":usuario_admin.correo,
                        "usuario":usuario_admin.usuario,
                        "contraseña":usuario_admin.contraseña
                    }}
        else:
            raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    # Verificar si el usuario existe en Estudiantes
    usuario_estudiante = db.query(Estudiante).filter(Estudiante.usuario == datos_login.usuario).first()
    if usuario_estudiante:
        if bcrypt.checkpw(datos_login.contraseña.encode('utf-8'), usuario_estudiante.contraseña.encode('utf-8')):
            return {
            "rol": "estudiante",
            "datos_estudiante": {
                "documento": usuario_estudiante.documento,
                "tipo_de_documento": usuario_estudiante.tipo_de_documento,
                "nombre": usuario_estudiante.nombre,
                "apellido": usuario_estudiante.apellido,
                "celular": usuario_estudiante.celular,
                "correo": usuario_estudiante.correo,
                "usuario":usuario_estudiante.usuario,
                "contraseña":usuario_estudiante.contraseña,
                "sede": usuario_estudiante.sede,
            }
        }
        else:
            raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    # Verificar si el usuario existe en Profesores
    usuario_profesor = db.query(Profesor).filter(Profesor.usuario == datos_login.usuario).first()
    if usuario_profesor:
        if bcrypt.checkpw(datos_login.contraseña.encode('utf-8'), usuario_profesor.contraseña.encode('utf-8')):
            return {
                    "rol": "profesor",
                    "datos_profesor": {
                        "documento": usuario_profesor.documento,
                        "tipo_de_documento": usuario_profesor.tipo_de_documento,
                        "nombre": usuario_profesor.nombre,
                        "apellido": usuario_profesor.apellido,
                        "celular": usuario_profesor.celular,
                        "correo": usuario_profesor.correo,
                        "usuario":usuario_profesor.usuario,
                        "contraseña":usuario_profesor.contraseña                      
                    }
                }            

        else:
            raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    # Si no se encuentra el usuario en ninguna tabla
    raise HTTPException(status_code=400, detail="Usuario incorrecto")



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





