from fastapi import FastAPI ,HTTPException,Depends,status
from conexion import crear,get_db
from modelo import *
from sqlalchemy.orm import Session 
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
#si no les agarra descarguen esto 'pip install fastapi uvicorn python-jose[cryptography] passlib'
from jose import JWTError,jwt
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
from funciones import *
from funciones_crear_cuenta import *


# DOCUMENTEN EL CODIGO (COMENTAR) PARA QUE NO SE HAGA UN SANCOCHO XFA


#inicializar la app
app=FastAPI()


#PERMITIR EL USO DE LA API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#CREAR LAS TABLAS
base.metadata.create_all(bind=crear)



#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


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
            "usuario": usuario.usuario
            
        }
    if isinstance(usuario, Estudiante):
        datos_token = {
            "rol": "estudiante",
            "usuario": usuario.usuario,
            }
    if isinstance(usuario, Profesor):
        datos_token =  {
            "rol": "profesor",
            "usuario": usuario.usuario
            }

     # Generar el token JWT 
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
        # Obtener el nombre de usuario  desde el token
        print(payload)
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

#funcion para tener la cuenta del estudiante
async def get_current_count_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
        # Obtener el nombre la cuenta  desde el token
        print(payload)
        cuenta: str = payload.get("documento")
        if cuenta is None:
            raise credentials_exception
    except JWTError:
        # Si hay un error en el token o ha expiracion
        raise credentials_exception
    
    #Obtener los mdatos de la cuenta del usuaruio desde la base de datos
    count= obtener_datos_cuenta(cuenta, db)
    if count is None:
        raise credentials_exception

    return count

# Endpoint protegido para obtener el usuario actual
@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    if current_user.__class__.__name__.lower()=="administrador":
        return {
                "rol": "administrador",
                "administrador_id": current_user.administrador_id,
                "usuario": current_user.usuario,
                "contraseña":current_user.contraseña
        }
    elif current_user.__class__.__name__.lower()=="estudiante":
        return{  "rol": "estudiante",
                "documento" : current_user.documento ,
                "tipo_de_documento" : current_user.tipo_de_documento, 
                "nombre": current_user.nombre, 
                "apellido": current_user.apellido, 
                "fecha_nacimiento": current_user.fecha_nacimiento, 
                "genero": current_user.genero, 
                "celular": current_user.celular, 
                "correo": current_user.correo, 
                "direccion": current_user.direccion, 
                "sede": current_user.sede, 
                "usuario": current_user.usuario, 
                "contraseña": current_user.contraseña, 
                "nivel_actual": current_user.nivel_actual, 
                "fecha_inscripcion": current_user.fecha_inscripcion, 
                "plan": current_user.plan, 
                "foto_perfil": current_user.foto_perfil
        }   
    elif current_user.__class__.__name__.lower()=="profesor":
   
        return{  "rol": "profesor",
                "documento" : current_user.documento ,
                "tipo_de_documento" : current_user.tipo_de_documento, 
                "nombre": current_user.nombre, 
                "apellido": current_user.apellido, 
                "fecha_nacimiento": current_user.fecha_nacimiento, 
                "genero": current_user.genero, 
                "celular": current_user.celular, 
                "correo": current_user.correo, 
                "direccion": current_user.direccion, 
                "usuario": current_user.usuario, 
                "contraseña": current_user.contraseña, 
                "fecha_contratacion": current_user.fecha_contratacion, 
                "foto_perfil": current_user.foto_perfil
        }          
 


#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


#METODOS DE AGREGAR (post)


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

    #SE CREA UN NUEVO ADMIN CON LOS DATOS QUE INGRESEN , SEGUIDO A ESTO SE HACE EL ADD, COMMIT Y EL REFRESH A LA DATABASE
    nuevo_administrador=Administrador(administrador_id=datos_administador.administrador_id,usuario=datos_administador.usuario,contraseña=encriptar_contraseña(datos_administador.contraseña))

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




@app.post("/añadirestudiante")
async def añadir_estudiante(datos_estudiante: EstudianteBase, db: Session = Depends(get_db)):
    existe_documento = db.query(Estudiante).filter(Estudiante.documento == datos_estudiante.documento).first()
    if existe_documento:
        raise HTTPException(status_code=400, detail=f"El documento '{datos_estudiante.documento}' ya está en uso.")

    if usuario_existe_globalmente(datos_estudiante.usuario, db):
        raise HTTPException(status_code=400, detail=f"El usuario '{datos_estudiante.usuario}' ya está en uso.")

    if not verificar_contraseña(datos_estudiante.contraseña):
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres, incluyendo números, caracteres especiales y mayúsculas.")
    
    if not verify_cel(datos_estudiante.celular):
        raise HTTPException(status_code=400, detail="Numero de Celular Invalido , no cumple con el estandar de 10 digitos")



    nuevo_estudiante = Estudiante(
        documento=datos_estudiante.documento,tipo_de_documento=datos_estudiante.tipo_de_documento,nombre=datos_estudiante.nombre,
        apellido=datos_estudiante.apellido,fecha_nacimiento=datos_estudiante.fecha_nacimiento,genero=datos_estudiante.genero,
        celular=datos_estudiante.celular,correo=datos_estudiante.correo,direccion=datos_estudiante.direccion,
        sede=datos_estudiante.sede,usuario=datos_estudiante.usuario,contraseña=encriptar_contraseña(datos_estudiante.contraseña),
        nivel_actual=datos_estudiante.nivel_actual,
        fecha_inscripcion=datos_estudiante.fecha_inscripcion,plan=datos_estudiante.plan,foto_perfil=datos_estudiante.foto_perfil
    )

    try:
        db.add(nuevo_estudiante)
        db.commit()
        db.refresh(nuevo_estudiante)
        
        nueva_cuenta = Cuenta(
            pagare=None,
            documento=nuevo_estudiante.documento,
            saldo=obtener_saldo(nuevo_estudiante.plan, db),
            pago_minimo=obtener_pago_minimo(nuevo_estudiante.plan, db),
            fecha_proximo_pago=obtener_fecha_proximo_pago(nuevo_estudiante.fecha_inscripcion)
        )
        db.add(nueva_cuenta)
        db.commit()
        db.refresh(nueva_cuenta)

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
    
    nuevo_profesor = Profesor(
        documento=datos_profesor.documento,tipo_de_documento=datos_profesor.tipo_de_documento,nombre=datos_profesor.nombre,
        apellido=datos_profesor.apellido,fecha_nacimiento=datos_profesor.fecha_nacimiento,genero=datos_profesor.genero,
        celular=datos_profesor.celular,correo=datos_profesor.correo,direccion=datos_profesor.direccion,
        usuario=datos_profesor.usuario,contraseña=encriptar_contraseña(datos_profesor.contraseña),
        fecha_contratacion=datos_profesor.fecha_contratacion,foto_perfil=datos_profesor.foto_perfil
    )


    
    try:
        db.add(nuevo_profesor)
        db.commit()
        db.refresh(nuevo_profesor)
        return "Profesor agregado exitosamente"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")
    


#METODO PARA AÑADIR PLANES
@app.post("/añadirplan")
async def añadir_plan(datos_plan:PlanBase,db:Session=Depends(get_db)):
    nuevo_plan=Plan(nombre=datos_plan.nombre,horas_semanales=datos_plan.horas_semanales,costo=datos_plan.costo,
    meses=datos_plan.meses)
    try:
        db.add(nuevo_plan)
        db.commit()
        db.refresh(nuevo_plan)
        return f"Plan Agregado Correctamente"
    except SQLAlchemyError as e :
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")
    


#METODO PARA AÑADIR NIVELES
@app.post("/añadirnivel")
async def añadir_plan(datos_nivel:NivelBase,db:Session=Depends(get_db)):
    nuevo_nivel=Nivel(nombre_nivel=datos_nivel.nombre_nivel,descripcion_nivel=datos_nivel.descripcion_nivel)
    try:
        db.add(nuevo_nivel)
        db.commit()
        db.refresh(nuevo_nivel)
        return f"Nivel Agregado Correctamente"
    except SQLAlchemyError as e :
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")



#METODO PARA AÑADIR CLASES
@app.post("/añadirclase")
async def añadir_clase(datos_clase:ClaseBase,db:Session=Depends(get_db)):
    nueva_clase=Clase(
      sede= datos_clase.sede,nivel = datos_clase.nivel,
      hora_inicio =datos_clase.hora_inicio,hora_fin =datos_clase.hora_fin,
      fecha =datos_clase.fecha,documento_profesor =datos_clase.documento_profesor, 
      cupos= datos_clase.cupos
)
    try:
        db.add(nueva_clase)
        db.commit()
        db.refresh(nueva_clase)
        return f"clase Agregada Correctamente"
    except SQLAlchemyError as e :
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")


#METODO PARA VER SI EL USUARIO DE PAGO EXISTE
@app.post('/verificar_pago')
async def verificar_usuario_pago(datos_cuenta:VerficarUsuario, db:Session=Depends(get_db)):
    #Obtener datos de la cuenta
    cuentabd= obtener_datos_cuenta(datos_cuenta.documento, db)


    cuenta=db.query(Estudiante).filter(Estudiante.documento==datos_cuenta.documento).first()
    datos=db.query(Cuenta).filter(Cuenta.documento==datos_cuenta.documento).first()

    if not cuenta:
        return {f'El documento que ingreso no se encuentra en la base de datos', datos_cuenta.documento}
    # Crear los datos del token
    datos_token = {
        "pagare": cuentabd.pagare,
        "documento": cuentabd.documento,
        "saldo": cuentabd.saldo,
        "pago_minimo": cuentabd.pago_minimo,
        #Se pone isoformat para que tome la rfecha como un string y no como tipo date
        "fecha_proximo_pago": cuentabd.fecha_proximo_pago.isoformat(),
        "dias_mora": cuentabd.dias_mora
    }

    db.commit()
    db.refresh(cuenta)
    # Generar el token JWT 
    token_acceso = crear_token(datos=datos_token, tiempo_expiracion=timedelta(minutes=MINUTOS_DE_EXPIRACION))
    return {"access_token": token_acceso, 
            "token_type": "bearer",
            "documento": datos_token}




#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


#METODOS DE CONSULTA (GET)


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
        profesores = db.query(Profesor).all()  # Obtener  todos los profesores
        return profesores  # retornar los profsores,claramente no?

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    


## METODO PARA CONSULTAR EL NOMBRE DE LOS PLANES
@app.get("/obtenernombreplanes")
async def obtener_nombre_planes (db:Session=Depends(get_db)):
    try:
        nombres_planes = db.query(Plan.nombre).all()  #se hace una busqueda de nombres (query es consulta en español) 
        return [nombre[0] for nombre in nombres_planes ]  #Convierto el resultado que es un diccionario a un array

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    


## METODO PARA CONSULTAR EL NOMBRE DE LOS NIVELES
@app.get("/obtenernombreniveles")
async def obtener_nombre_nivels (db:Session=Depends(get_db)):
    try:
        nombres_niveles = db.query(Nivel.nombre_nivel).all()  #se hace una busqueda de nombres (query es consulta en español) 
        return [nombre[0] for nombre in nombres_niveles ]  #Convierto el resultado que es un diccionario a un array

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
#METODO PARA TRAER LA INFORMACION DE LA CUENTA
@app.get("/datos_cuenta")
async def obtener_cuenta(cuenta : dict =Depends(get_current_count_student)):
            return {
                    "Pagare": cuenta.pagare,
                    "Documento": cuenta.documento,
                    "Saldo": cuenta.saldo,
                    "Pago Minimo":cuenta.pago_minimo,
                    "Fecha del proximo pago": cuenta.fecha_proximo_pago,
                    "Dias de mora": cuenta.dias_mora
                    }

#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


#METODOS DE ELIMINACION (DELETE)    


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





#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


#METODOS DE EDICION/ACTUALIZACION (PUT)  
























