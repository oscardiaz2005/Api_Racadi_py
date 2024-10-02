from fastapi import FastAPI ,HTTPException,Depends,status
from conexion import crear,get_db
from modelo import *
from sqlalchemy.orm import Session 
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text , or_ , and_
#si no les agarra descarguen esto 'pip install fastapi uvicorn python-jose[cryptography] passlib'
from jose import JWTError,jwt
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
from funciones import *
from funciones_crear_cuenta import *
from funciones_validacion_clases import *
from typing import List


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
async def añadir_clase(datos_clase: ClaseBase, db: Session = Depends(get_db)):
    # Verificar si hora_inicio y hora_fin son cadenas y convertirlas a time
    if isinstance(datos_clase.hora_inicio, str):
        try:
            hora_inicio = datetime.strptime(datos_clase.hora_inicio, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de hora de inicio no válido. Use HH:MM.")
    else:
        hora_inicio = datos_clase.hora_inicio

    if isinstance(datos_clase.hora_fin, str):
        try:
            hora_fin = datetime.strptime(datos_clase.hora_fin, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de hora de fin no válido. Use HH:MM.")
    else:
        hora_fin = datos_clase.hora_fin

    # Realizar validaciones
    validar_fecha(datos_clase.fecha)
    validar_horas(hora_inicio, hora_fin)  
    validar_horarios_disponibles(hora_inicio)
    validar_clases_duplicadas(datos_clase, db)
    validar_conflictos_profesor(datos_clase.documento_profesor, datos_clase.fecha, hora_inicio, db)
    validar_profesor(datos_clase.documento_profesor,db)

    if not verify_cupos(datos_clase.cupos):
        raise HTTPException(status_code=400, detail="Cupos inválidos, rango aceptado de 1 a 15")

    nueva_clase = Clase(
        sede=datos_clase.sede,
        nivel=datos_clase.nivel,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        fecha=datos_clase.fecha,
        documento_profesor=datos_clase.documento_profesor,
        cupos=datos_clase.cupos
    )

    try:
        db.add(nueva_clase)
        db.commit()
        db.refresh(nueva_clase)
        return "Clase agregada correctamente"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")
    


#METODO PARA RESERVAR CLASES
@app.post("/reservar_clase")
async def reservar_clase(datos_reserva: ReservaBase, db: Session = Depends(get_db)):
    clase = db.query(Clase).filter(Clase.id_clase == datos_reserva.id_clase).first()
    estudiante = db.query(Estudiante).filter(Estudiante.documento == datos_reserva.documento_estudiante).first()
    
    if clase is None:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    
    if estudiante is None:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Combinar fecha y hora de inicio para obtener un objeto datetime
    hora_inicio_clase = datetime.combine(clase.fecha, clase.hora_inicio)

    ahora = datetime.now()
    if hora_inicio_clase - ahora < timedelta(hours=2):
        raise HTTPException(status_code=400, detail="No se puede reservar con menos de 2 horas de antelación")
    
    existe_reserva = db.query(Reserva).filter(
        and_(Reserva.id_clase == datos_reserva.id_clase,
             Reserva.documento_estudiante == datos_reserva.documento_estudiante)
    ).first()
    if existe_reserva:
        raise HTTPException(status_code=400, detail="Clase ya reservada")

    if clase.cupos == 0:
        raise HTTPException(status_code=400, detail="Esta clase ya no tiene cupos disponibles")


    # Verificar las horas semanales reservadas por el estudiante

    plan = db.query(Plan).filter(Plan.nombre == estudiante.plan).first()

    if plan is None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    # Calcular el inicio de la semana (lunes) y el fin de la semana (domingo)
    hoy = ahora.date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())  
    fin_semana = inicio_semana + timedelta(days=6)  


    reservas_semana = db.query(Reserva).join(Clase, Reserva.id_clase == Clase.id_clase).filter(
        and_(
            Reserva.documento_estudiante == datos_reserva.documento_estudiante,
            Clase.fecha >= inicio_semana,
            Clase.fecha <= fin_semana
        )
    ).all()

    horas_reservadas = len(reservas_semana) * 2  # *2 porque Cada clase dura 2 horas

    if horas_reservadas + 2 > plan.horas_semanales:
        raise HTTPException(status_code=400, detail=f"Has alcanzado tu límite semanal de {plan.horas_semanales} horas")

    try:
        nueva_reserva = Reserva(
            documento_estudiante=datos_reserva.documento_estudiante,
            id_clase=datos_reserva.id_clase
        )
        db.add(nueva_reserva)
        
        # Disminuir cupos disponibles de la clase
        clase.cupos -= 1
        
        db.commit()
        db.refresh(nueva_reserva)
        
        return {"message": "Clase reservada exitosamente"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")


    






        

    





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




#METODO PARA MOSTRAR LAS OBSEVACIONES AGREGADAS
@app.post("/añadirObservacion")
async def añadir_observacion(datos_observacion:ObservacionBase , db:Session=Depends(get_db)):
    
    try:
          nueva_observacion=Observacion(descripcion=datos_observacion.descripcion,documento=datos_observacion.documento,creada_por=datos_observacion.creada_por)
          db.add(nueva_observacion) 
          db.commit()
          db.refresh(nueva_observacion)
          return f"Observacion fue agregada"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")
        
        
#METODO PARA AGREGAR SOLICITUDES 
@app.post("/añadir_Solicitud")
async def añadir_solicitud(dato_solicitud:SolicitudBase, db:Session=Depends(get_db)):
    try:
        nueva_solicitud=Solicitud(documento=dato_solicitud.documento,descripcion=dato_solicitud.descripcion)
        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud)
        return f"Solicitud fue agregada con exito"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")


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
    


## METODO PARA CONSULTAR ESTUDIANTE POR DOCUMENTO
@app.get("/obtenerestudiante/{documento}")
async def get_estudiantes_documento( documento:str,db: Session = Depends(get_db)):
    
     estudiante = db.query(Estudiante).filter(Estudiante.documento==documento).first()  # Comparar documentos
     if estudiante:
        return estudiante # retornar el estudiantee,claramente no?
     else:
        raise HTTPException (status_code=400, detail="no se encontro estudiante")
        
         
         





## METODO PARA CONSULTAR TODOS LOS PROFESORES
@app.get("/obtenerprofesores")
async def get_profesores(db: Session = Depends(get_db)):
    try:
        profesores = db.query(Profesor).all()  # Obtener  todos los profesores
        return profesores  # retornar los profsores,claramente no?

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    


#METODO PARA BUSQUEDA REACTIVA DE PROFESORES POR NOMBRE
@app.get("/buscarprofesores", response_model=List[dict])
async def buscar_profesores(nombre: str, db: Session = Depends(get_db)):
    # Filtra los profesores directamente en la consulta
    profesores = db.query(Profesor).filter(
        or_(
            Profesor.nombre.ilike(f"%{nombre}%"),  # Búsqueda insensible a mayúsculas/minúsculas
            Profesor.apellido.ilike(f"%{nombre}%")
        )
    ).all()

    resultados = [
        {
            "documento": profesor.documento,
            "nombre": profesor.nombre,
            "apellido": profesor.apellido,
        }
        for profesor in profesores
    ]
    
    return resultados

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



#METODO PARA OBTENER LAS CLASES CORRESPONDIENTES A UN ESTUDIANTE
@app.get("/obtenerclasesestudiante/{sede}/{nivel}")
async def obtenerclasesestudiante(sede:str,nivel:str , db:Session=Depends(get_db)):
    try :
        clases_estudiante=db.query(Clase).filter(
            and_(
                Clase.sede==sede,
                Clase.nivel==nivel
            )
        ).all()
        resultados=[
            {
                "id_clase":clase.id_clase,
                "sede" :clase.sede,
                "nivel" :clase.nivel ,
                "hora_inicio" :clase.hora_inicio,
                "hora_fin" :clase.hora_fin,
                "fecha" :clase.fecha,
                "profesor":get_name_teacher_by_dni(clase.documento_profesor,db),
                "cupos" :clase.cupos
            }
            for clase in clases_estudiante
        ]    
        if resultados:
            return resultados
        else:
            raise HTTPException(status_code=400,detail=f"No Hay Clases Para la Sede {sede} y nivel {nivel} esta semana")
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    


#METODO PARA OBTENER RESERVAS DE UN ESTUDIANTE    
@app.get("/obtener_reservas/{documento_estudiante}")
async def obtener_reservas(documento_estudiante: str, db: Session = Depends(get_db)):
    reservas = db.query(Reserva).filter(Reserva.documento_estudiante == documento_estudiante).all()
    
    if not reservas:
        return []

    return reservas

    
    
##filtrar los observadores por documento de estudiante
@app.get("/filtro_ObservadoresDocumento/{documento}")
async def filtro_observaciones_por_documento(documento: str, db: Session = Depends(get_db)):
    try:
        # Realiza la consulta a la base de datos para filtrar por documento
        observaciones = db.query(Observacion).filter(Observacion.documento == documento).all()

        # Si no se encontraron observaciones, se lanza una excepción
        if not observaciones:
            raise HTTPException(status_code=404, detail="No se encontraron observaciones para el documento proporcionado.")
        
        return observaciones

    except SQLAlchemyError as e:
        # Si hay un error en la consulta, se lanza una excepción con el mensaje de error
        raise HTTPException(status_code=400, detail=str(e))
    
    
    
#Es para mostrar las observaciones del estudinate en la vista estudiante flitrados por fecha
@app.get("/filtro_ObservadoresFecha/{documento}/{fecha}")
async def filtro_observaciones_por_documento(documento: str,fecha:str, db: Session = Depends(get_db)):
    try:
        # Realiza la consulta a la base de datos para filtrar por documento
        observaciones = db.query(Observacion).filter(Observacion.documento == documento) and db.query(Observacion).filter(Observacion.fecha == fecha) .all()

        # Si no se encontraron observaciones, se lanza una excepción
        if not observaciones:
            raise HTTPException(status_code=404, detail="No se encontraron observaciones para el documento proporcionadoo.")
        
        return observaciones

    except SQLAlchemyError as e:
        # Si hay un error en la consulta, se lanza una excepción con el mensaje de error
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



#METODO PARA TRAER LA INFORMACION DE LAS SOLICITUDES
@app.get("/traer_datos_solicitudes")
async def obtener_solicitudes(db:Session=Depends(get_db)):
    try:
        info_solicitudes = db.query(Solicitud).all()
        if info_solicitudes:
            return info_solicitudes
        else: 
            return {"message": "No hay solicitudes"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
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



#METODO PARA ELIMINAR UNA SOLICITUD 
@app.delete("/elimina_solicitud/{id}")
async def delete_solicitud(id:int,db:Session=Depends(get_db)):
    solicitud_encontrada=db.query(Solicitud).filter(id==Solicitud.id_solicitud).first()
    if solicitud_encontrada:
        db.delete(solicitud_encontrada)
        db.commit()
        return {"":f"Solicitud con id {id} eliminada"}
    else:
        raise HTTPException (status_code=400, detail="no se encontro solicitud")



#METODO PARA CANCELAR UNA RESERVA
@app.delete("/cancelar_reserva")
async def cancelar_reserva(datos_reserva: ReservaBase, db: Session = Depends(get_db)):
    clase = db.query(Clase).filter(Clase.id_clase == datos_reserva.id_clase).first()
    
    if clase is None:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    # Combinar fecha y hora de inicio para obtener un objeto datetime
    hora_inicio_clase = datetime.combine(clase.fecha, clase.hora_inicio)
    
    # Verificar si faltan menos de 2 horas para la clase
    ahora = datetime.now()
    if hora_inicio_clase - ahora < timedelta(hours=2):
        raise HTTPException(status_code=400, detail="No se puede cancelar con menos de 2 horas de antelación")

    # Buscar la reserva
    reserva = db.query(Reserva).filter(
        and_(Reserva.id_clase == datos_reserva.id_clase,
             Reserva.documento_estudiante == datos_reserva.documento_estudiante)
    ).first()
    
    if reserva is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    try:
        # Eliminar la reserva
        db.delete(reserva)
        
        # Aumentar los cupos disponibles de la clase
        clase.cupos += 1
        
        db.commit()
        
        return {"message": "Reserva cancelada exitosamente"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")








#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


#METODOS DE EDICION/ACTUALIZACION (PUT)  
#ACABO DE INAGURAR ESTE APARTADO YO SOY MUY ASPERO JSJSJSJJSJS


#METODO PARA ACTUALIZAR LA SOLICITUD
@app.put("/actualizar_solicitud/{id}")
async def actualizar_solicitud(id: int, solicitud: SolicitudBase, db: Session = Depends(get_db)):
    db.query(Solicitud).filter(Solicitud.id_solicitud == id).update({
        Solicitud.descripcion: solicitud.descripcion,
        Solicitud.respuesta: solicitud.respuesta,
        Solicitud.contestacion: solicitud.contestacion
    })
    db.commit()
    return {"message": "Solicitud actualizada con éxito"}















