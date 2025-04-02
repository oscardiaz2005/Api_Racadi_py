import os
from fastapi import FastAPI ,HTTPException,Depends,status ,Form ,File ,UploadFile
from fastapi.staticfiles import StaticFiles
from core.conexion import crear,get_db
from db.modelo import *
from sqlalchemy.orm import Session 
from fastapi.middleware.cors import CORSMiddleware
from db.schemas import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text , or_ , and_ ,desc,asc
#si no les agarra descarguen esto 'pip install fastapi uvicorn python-jose[cryptography] passlib'
from jose import JWTError,jwt
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
from services.funciones import *
from services.funciones_crear_cuenta import *
from services.funciones_validacion_clases import *
from typing import List
from sqlalchemy.orm import joinedload



# DOCUMENTEN EL CODIGO (COMENTAR) PARA QUE NO SE HAGA UN SANCOCHO XFA


#inicializar la app
app=FastAPI()

app.mount("/images", StaticFiles(directory="static/micarpetaimg"), name="images")


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
    
    if usuario.estado==False:
        raise HTTPException(status_code=400,detail="Cuenta inactiva. Contacta soporte")
    
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


# Endpoint protegido para obtener el usuario actual
@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    if current_user.__class__.__name__.lower()=="administrador":
        return {
                "rol": "administrador",
                "administrador_id": current_user.administrador_id,
                "usuario": current_user.usuario,
                "contraseña":current_user.contraseña,
                "estado":current_user.estado

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
                "foto_perfil": current_user.foto_perfil,
                "estado":current_user.estado
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
                "foto_perfil": current_user.foto_perfil,
                "estado":current_user.estado
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
async def añadir_estudiante(
    documento: str = Form(...),
    tipo_de_documento: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    celular: str = Form(...),
    correo: str = Form(...),
    direccion: str = Form(...),
    sede: str = Form(...),
    usuario: str = Form(...),
    contraseña: str = Form(...),
    nivel_actual: str = Form(...),
    plan: str = Form(...),
    file: UploadFile = File(None),  
    db: Session = Depends(get_db)
):
    # Validación de documento y usuario
    existe_documento = db.query(Estudiante).filter(Estudiante.documento == documento).first()
    if existe_documento:
        raise HTTPException(status_code=400, detail=f"El documento '{documento}' ya está en uso.")
    
    if usuario_existe_globalmente(usuario, db):
        raise HTTPException(status_code=400, detail=f"El usuario '{usuario}' ya está en uso.")
    
    if not verificar_contraseña(contraseña):
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres, incluyendo números, caracteres especiales y mayúsculas.")
    
    if not verify_cel(celular):
        raise HTTPException(status_code=400, detail="Número de celular inválido, debe tener 10 dígitos.")

    
    if file:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        
        folder_path = "static/micarpetaimg"
        file_location = os.path.join(folder_path, file.filename)

        # Asegúrate de que la carpeta existe
        os.makedirs(folder_path, exist_ok=True)

        # Guarda el archivo en el servidor
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())


        foto_perfil_url = f"/images/{file.filename}"
    else :
        foto_perfil_url=None   

    
    # Crea el nuevo estudiante
    nuevo_estudiante = Estudiante(
        documento=documento,
        tipo_de_documento=tipo_de_documento,
        nombre=nombre,
        apellido=apellido,
        fecha_nacimiento=fecha_nacimiento,
        genero=genero,
        celular=celular,
        correo=correo,
        direccion=direccion,
        sede=sede,
        usuario=usuario,
        contraseña=encriptar_contraseña(contraseña),
        nivel_actual=nivel_actual,
        plan=plan,
        foto_perfil=foto_perfil_url  # Ruta de la imagen guardada
    )

    try:
        db.add(nuevo_estudiante)
        db.commit()
        db.refresh(nuevo_estudiante)
        
        # Crea la cuenta asociada al estudiante
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
async def añadir_estudiante(
    documento: str = Form(...),
    tipo_de_documento: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    celular: str = Form(...),
    correo: str = Form(...),
    direccion: str = Form(...),
    usuario: str = Form(...),
    contraseña: str = Form(...),
    file: UploadFile = File(None),  
    db: Session = Depends(get_db)
):
    # Validación de documento y usuario
    existe_documento = db.query(Profesor).filter(Profesor.documento == documento).first()
    if existe_documento:
        raise HTTPException(status_code=400, detail=f"El documento '{documento}' ya está en uso.")
    
    if usuario_existe_globalmente(usuario, db):
        raise HTTPException(status_code=400, detail=f"El usuario '{usuario}' ya está en uso.")
    
    if not verificar_contraseña(contraseña):
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres, incluyendo números, caracteres especiales y mayúsculas.")
    
    if not verify_cel(celular):
        raise HTTPException(status_code=400, detail="Número de celular inválido, debe tener 10 dígitos.")

    if file:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        
        folder_path = "static/micarpetaimg"
        file_location = os.path.join(folder_path, file.filename)

        # Asegúrate de que la carpeta existe
        os.makedirs(folder_path, exist_ok=True)

        # Guarda el archivo en el servidor
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())


        foto_perfil_url = f"/images/{file.filename}"
    else :
        foto_perfil_url=None 

    
    # Crea el nuevo Profesor
    nuevo_profesor = Profesor(
        documento=documento,
        tipo_de_documento=tipo_de_documento,
        nombre=nombre,
        apellido=apellido,
        fecha_nacimiento=fecha_nacimiento,
        genero=genero,
        celular=celular,
        correo=correo,
        direccion=direccion,
        usuario=usuario,
        contraseña=encriptar_contraseña(contraseña),
        foto_perfil=foto_perfil_url  # Ruta de la imagen guardada
    )

    try:
        db.add(nuevo_profesor)
        db.commit()
        db.refresh(nuevo_profesor)
        
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
    
    validar_dias_mora(estudiante.documento,db)


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
@app.post("/agregar_solicitud")
async def añadir_solicitud(dato_solicitud:SolicitudBase, db:Session=Depends(get_db)):
    try:
        nueva_solicitud=Solicitud(documento=dato_solicitud.documento,descripcion=dato_solicitud.descripcion)
        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")



#Metodo para añadir comunicados


@app.post("/crear_comunicados")
async def crear_comunicado(
    titulo: str = Form(...),descripcion: str = Form(...),file: UploadFile = File(...),  db:Session=Depends(get_db)):


    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
    
    folder_path = "static/micarpetaimg"
    file_location = os.path.join(folder_path, file.filename)

    # Asegúrate de que la carpeta existe
    os.makedirs(folder_path, exist_ok=True)

    # Guarda el archivo en el servidor
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())


    foto_comunicado_url = f"/images/{file.filename}"

    nuevo_comunicado=Comunicado(
        titulo=titulo,
        descripcion=descripcion,
        foto=foto_comunicado_url
    )
    try:
        db.add(nuevo_comunicado)
        db.commit()
        db.refresh(nuevo_comunicado)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")




#METODO PARA AÑADIR LAS NOTAS DE EVALUACION


@app.post("/add_notas")
async def add_quiz_results(documento:str,speaking:float,listening:float,reading:float,writing:float,grammar:float,db:Session= Depends(get_db)):
    verify_notes(speaking,listening,reading,writing)
    validar_estudiante(documento,db)
    validar_nivel_estudiante(documento,db)
    borrar_registro_fallido(documento,get_student_level(documento,db),db)
    nuevo_registro=RegistroEstudianteNivel(
        documento=documento,
        nivel=get_student_level(documento,db),
        speaking=speaking,
        listening=listening,
        reading=reading,
        writing=writing,
        grammar=grammar
    )
    try:
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")
    make_quiz_observation(documento,db)
    set_next_level(documento,db)   
      
    



## METODOS DE ASISTENCIA
@app.post("/asistencia/{id_reserva:int}")
async def asistencia(id_reserva:int , db:Session=Depends(get_db) ) :
    asistencia=Asistencia(
        id_reserva=id_reserva,
        asistencia=True
    )
      
    try: 
        db.add(asistencia)
        db.commit()
        db.refresh(asistencia)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")   
    

@app.post("/incumplimiento/{id_reserva:int}")
async def incumplimiento(id_reserva:int , db:Session=Depends(get_db) ) :
    asistencia=Asistencia(
        id_reserva=id_reserva,
        asistencia=False
    )
      
    try: 
        db.add(asistencia)
        db.commit()
        db.refresh(asistencia)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")      



#METODO PARA AGREGAR UN PAGO
@app.post("/agregar_pago")
async def agregar_pagos(cuenta_documento:str,valor:int , db:Session=Depends(get_db)):
    
    try:
        if validar_pago(cuenta_documento,valor,db):
            cuenta_encontrada=db.query(Cuenta).filter(Cuenta.documento==cuenta_documento).first()
            actualizar_dias_mora(cuenta_encontrada.documento,db)
            actualizar_pago_minimo(cuenta_encontrada.documento,db)


            if cuenta_encontrada.dias_mora>0:
                valor=calcular_pago_minimo_base(cuenta_documento, db)

            nuevo_pago=Pago(cuenta_documento=cuenta_documento,valor=valor)    


            db.add(nuevo_pago) 
            db.commit()
            db.refresh(nuevo_pago)

            actualizar_saldo(cuenta_documento,valor,db)
            actualizar_fecha_proximo_pago(cuenta_documento,db)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400 ,detail=f"algo salio mal : {str(e)}")
        

           
    


#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


#METODOS DE CONSULTA (GET)


## METODO PARA CONSULTAR TODOS LOS ESTUDIANTES
@app.get("/obtenerestudiantes")
async def get_students( db: Session = Depends(get_db)):
    estudiantes = db.query(Estudiante).all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail="No se encontraron estudiantes")

    # Construye un único objeto para cada estudiante con sus datos y los de la cuenta
    resultados = []
    for estudiante in estudiantes:
        resultados.append({
            "documento": estudiante.documento,
            "tipo_de_documento": estudiante.tipo_de_documento,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "fecha_nacimiento": estudiante.fecha_nacimiento,
            "genero": estudiante.genero,
            "celular": estudiante.celular,
            "correo": estudiante.correo,
            "direccion": estudiante.direccion,
            "sede": estudiante.sede,
            "usuario": estudiante.usuario,
            "contraseña": estudiante.contraseña,
            "nivel_actual": estudiante.nivel_actual,
            "plan": estudiante.plan,
            "fecha_inscripcion": estudiante.fecha_inscripcion,
            "foto_perfil": estudiante.foto_perfil,
            "estado":estudiante.estado,
            # Datos de la cuenta obtenidos con la función :P
            "saldo": obtener_dato_cuenta(estudiante.documento, "saldo", db),
            "pagare": obtener_dato_cuenta(estudiante.documento, "pagare", db),
            "pago_minimo": calcular_pago_minimo_base(estudiante.documento,db),
            "pago_total": obtener_dato_cuenta(estudiante.documento, "pago_total", db),  
            "monto_por_mora": calcular_monto_por_mora(estudiante.documento,db),
            "fecha_proximo_pago": obtener_dato_cuenta(estudiante.documento, "fecha_proximo_pago", db),
            "dias_mora": obtener_dato_cuenta(estudiante.documento, "dias_mora", db),

        })


    return resultados
    



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
            "tipo_de_documento":profesor.tipo_de_documento,
            "nombre": profesor.nombre,
            "apellido": profesor.apellido,
            "fecha_nacimiento":profesor.fecha_nacimiento,
            "genero":profesor.genero,
            "celular":profesor.celular,
            "correo":profesor.correo,
            "direccion":profesor.direccion,
            "usuario":profesor.usuario,
            "contraseña":profesor.contraseña,
            "fecha_contratacion":profesor.fecha_contratacion,
            "foto_perfil":profesor.foto_perfil,
            "estado":profesor.estado,



        }
        for profesor in profesores
    ]
    
    return resultados


#METODO PARA BUSQUEDA REACTIVA DE Estudiantes POR NOMBRE
@app.get("/buscarestudiantes", response_model=List[dict])
async def buscar_estudiantes_completo(nombre: str, db: Session = Depends(get_db)):
    # Filtra estudiantes según el nombre o apellido
    estudiantes = db.query(Estudiante).filter(
        or_(
            Estudiante.nombre.ilike(f"%{nombre}%"),  # Insensible a mayúsculas/minúsculas
            Estudiante.apellido.ilike(f"%{nombre}%")
        )
    ).all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail="No se encontraron estudiantes")

    # Construye un único objeto para cada estudiante con sus datos y los de la cuenta
    resultados = []
    for estudiante in estudiantes:
        resultados.append({
            "documento": estudiante.documento,
            "tipo_de_documento": estudiante.tipo_de_documento,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "fecha_nacimiento": estudiante.fecha_nacimiento,
            "genero": estudiante.genero,
            "celular": estudiante.celular,
            "correo": estudiante.correo,
            "direccion": estudiante.direccion,
            "sede": estudiante.sede,
            "usuario": estudiante.usuario,
            "contraseña": estudiante.contraseña,
            "nivel_actual": estudiante.nivel_actual,
            "plan": estudiante.plan,
            "fecha_inscripcion": estudiante.fecha_inscripcion,
            "foto_perfil": estudiante.foto_perfil,
            "estado":estudiante.estado,
            # Datos de la cuenta obtenidos con la función :P
            "saldo": obtener_dato_cuenta(estudiante.documento, "saldo", db),
            "pagare": obtener_dato_cuenta(estudiante.documento, "pagare", db),
            "pago_minimo": obtener_dato_cuenta(estudiante.documento, "pago_minimo", db),
            "pago_total": obtener_dato_cuenta(estudiante.documento, "pago_minimo", db),  
            "monto_por_mora": calcular_monto_por_mora(estudiante.documento,db),
            "fecha_proximo_pago": obtener_dato_cuenta(estudiante.documento, "fecha_proximo_pago", db),
            "dias_mora": obtener_dato_cuenta(estudiante.documento, "dias_mora", db),
        })

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
        ).order_by(asc(Clase.hora_inicio)).all()
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

    
    

@app.get("/filtro_ObservadoresDocumento/{documento}")
async def filtro_observaciones_por_documento(documento: str, db: Session = Depends(get_db)):
    try:
        observaciones = (
            db.query(Observacion)
            .filter(Observacion.documento == documento)
            .order_by(desc(Observacion.id_observacion))  # Ordenar por fecha de creación descendente
            .all()
        )

        return observaciones

    except SQLAlchemyError as e:
        # Si hay un error en la consulta, se lanza una excepción con el mensaje de error
        raise HTTPException(status_code=400, detail=str(e))

    
    
#Es para mostrar las observaciones del estudiante en la vista estudiante filtrados por fecha
@app.get("/filtro_ObservadoresFecha/{documento}/{fecha}")
async def filtro_observaciones_por_documento(documento: str, fecha: str, db: Session = Depends(get_db)):
    try:
        # Realiza la consulta a la base de datos filtrando por documento y fecha
        observaciones = (
            db.query(Observacion)
            .filter(
                and_(
                    Observacion.documento == documento,
                    Observacion.fecha == fecha
                )
            )
            .order_by(desc(Observacion.id_observacion))
            .all()
        )
        return observaciones
    except SQLAlchemyError as e:
        # Si hay un error en la consulta, se lanza una excepción con el mensaje de error
        raise HTTPException(status_code=400, detail=str(e))
    

#METODO PARA TRAER LA INFORMACION DE LA CUENTA
@app.get("/datos_cuenta/{documento}")
async def obtener_cuenta(documento:str, db:Session=Depends(get_db)):
    Cuenta_encontrada=db.query(Cuenta).filter(Cuenta.documento==documento).first()
    
    actualizar_dias_mora(Cuenta_encontrada.documento,db)
    actualizar_pago_minimo(Cuenta_encontrada.documento,db)
    monto_por_mora=calcular_monto_por_mora(Cuenta_encontrada.documento,db)

    return {
        "saldo":Cuenta_encontrada.saldo,
        "pagare":Cuenta_encontrada.pagare,
        "documento": Cuenta_encontrada.documento,
        "pago_minimo":calcular_pago_minimo_base(Cuenta_encontrada.documento,db) ,
        "pago_total":Cuenta_encontrada.pago_minimo ,
        "monto_por_mora":monto_por_mora,
        "fecha_proximo_pago":Cuenta_encontrada.fecha_proximo_pago,
        "dias_mora":Cuenta_encontrada.dias_mora,
    }




#Metodo para tener solicitudes del estudiante 
@app.get("/obtenersolicitudestudiante/{documento}")
async def obtener_solicitudes_estudiante(documento: str, db: Session = Depends(get_db)):
    try:
        solicitudes_estudiante = db.query(Solicitud).filter(  Solicitud.documento == documento ).order_by(desc(Solicitud.fecha_creacion)).all()
        resultados = [
            {
                "id_solicitud": solicitud.id_solicitud,
                "documento": solicitud.documento,
                "descripcion": solicitud.descripcion,
                "respuesta": solicitud.respuesta,
                "contestacion": solicitud.respuesta,
                "fecha_creacion": solicitud.fecha_creacion,
            }
            for solicitud in solicitudes_estudiante
        ]

        if resultados:
            return resultados
        else:
            return None

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e)) 





#METODO PARA OBTENER TODAS LAS SOLICITUDES
@app.get("/obtenersolicitudes")
async def obtener_solicitudes(db: Session = Depends(get_db)):
    try:
        solicitudes = db.query(Solicitud).all()
        resultados = [
            {
                "id_solicitud": solicitud.id_solicitud,
                "documento": solicitud.documento,
                "descripcion": solicitud.descripcion,
                "respuesta": solicitud.respuesta,
                "contestacion": solicitud.respuesta,
                "fecha_creacion": solicitud.fecha_creacion,
            }
            for solicitud in solicitudes
        ]

        if resultados:
            return resultados
        else:
            return None

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))         








#Metodo para traer todos los comunicados
@app.get("/obtener_comunicados")
async def get_comunicados(db: Session = Depends(get_db)):
    try:
        comunicados = db.query(Comunicado).all()  # Obtener  todos los comunicados
        return comunicados  # retornar los comunicaos,claramente no?

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
    
    #metodo get para traer las clases reservadas
@app.get("/clases_reservadas/{documento_estudiante}")
async def obtener_reservas(documento_estudiante: str, db: Session = Depends(get_db)):
    try:
        # Realiza la consulta a la base de datos para filtrar por documento_estudiante
        reservas = db.query(Reserva, Clase)\
            .join(Clase)\
            .filter(Reserva.documento_estudiante == documento_estudiante)\
            .all()

        # Formatea la respuesta
        result = []
        for reserva, clase in reservas:
            result.append({
                'id_reserva': reserva.id_reserva,
                'id_clase': clase.id_clase,
                'sede': clase.sede,
                'nivel': clase.nivel,
                'hora_inicio': str(clase.hora_inicio),  # Convertir Time a string
                'hora_fin': str(clase.hora_fin),        # Convertir Time a string
                'fecha': str(clase.fecha),              # Convertir Date a string
                'documento_profesor':get_name_teacher_by_dni(clase.documento_profesor,db) ,
                'documento_estudiante': reserva.documento_estudiante,
                'cupos': clase.cupos
            })

        return result

    except SQLAlchemyError as e:
        # Si hay un error en la consulta, se lanza una excepción con el mensaje de error
        return {"message": "No hay clases Reservadas"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
    

##filtrar las clases por documento de profesor
@app.get("/filtro_ClasesDocumento/{documento}")
async def filtro_Clases_por_documento(documento: str, db: Session = Depends(get_db)):
    try:
        # Realiza la consulta a la base de datos para filtrar por documento
        Clases = db.query(Clase).filter(Clase.documento_profesor == documento).all()
        result=[]
        for clase in Clases:
            result.append({
                'id_clase': clase.id_clase,
                'sede': clase.sede,
                'nivel': clase.nivel,
                'hora_inicio': str(clase.hora_inicio),  # Convertir Time a string
                'hora_fin': str(clase.hora_fin),        # Convertir Time a string
                'fecha': str(clase.fecha),              # Convertir Date a string
                'documento_profesor':get_name_teacher_by_dni(clase.documento_profesor,db) ,
                'estudiantes': count_students(clase.id_clase,db)
            })

        return result 

    except SQLAlchemyError as e:
        # Si hay un error en la consulta, se lanza una excepción con el mensaje de error
        raise HTTPException(status_code=400, detail=str(e))
         

#METODO PARA OBTENER TODOS LOS ESTUDIANTES DE UNA CLASE / ASISTENCIA

@app.get("/getStudentsByClass/{id_clase}")
async def getStudentsByClass(id_clase: int, db: Session = Depends(get_db)):
    try:
        estudiantes_encontrados = db.query( Estudiante,Reserva,Clase,Asistencia.asistencia  ).join(
            Reserva, Reserva.documento_estudiante == Estudiante.documento).join(
            Clase, Reserva.id_clase == Clase.id_clase).outerjoin(
            Asistencia, Reserva.id_reserva == Asistencia.id_reserva  ).filter(
            Clase.id_clase == id_clase).all()
        
        result = []
        for estudiante, reserva, clase, asistencia in estudiantes_encontrados:
            result.append({
                'documento': estudiante.documento,
                'nombre': estudiante.nombre,
                'apellido': estudiante.apellido,
                "id_reserva": reserva.id_reserva,
                'sede': clase.sede,
                'nivel': clase.nivel,
                'hora_inicio': str(clase.hora_inicio),  
                'hora_fin': str(clase.hora_fin),
                'fecha': str(clase.fecha),
                'asistencia': asistencia 
            })

        return result

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))



#METODO PARA OBTENER LAS NOTAS DE LOS ESTUDIANTE

@app.get("/getStudentsNotes/{nivel}/{documento}")
async def getStudentsNotes(nivel: str,documento:str, db: Session = Depends(get_db)):
    try:
        notas_encontradas=db.query(RegistroEstudianteNivel).filter(
            and_(
                RegistroEstudianteNivel.documento==documento,
                RegistroEstudianteNivel.nivel==nivel)).first()
        if notas_encontradas:
            return notas_encontradas
        else:
            return None               
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))  



@app.get("/getStudentpayments/{documento}")
async def getStudentspayments(documento:str,db:Session = Depends(get_db)):
    try:
        pagos_encontradas=db.query(Pago).filter(Pago.cuenta_documento==documento).order_by(desc(Pago.id_pago)).all()
        if pagos_encontradas:
            return pagos_encontradas
        else:
            return None               
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))                















#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            
#-------------------------------------------------------------------------------------------------------------------------            


#METODOS DE ELIMINACION (DELETE)    

#METODO PARA ELIMINAR UNA SOLICITUD 
@app.delete("/eliminar_solicitud/{id}")
async def delete_solicitud(id:int,db:Session=Depends(get_db)):
    solicitud_encontrada=db.query(Solicitud).filter(id==Solicitud.id_solicitud).first()
    if solicitud_encontrada:
        db.delete(solicitud_encontrada)
        db.commit()
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

#METODO PARA AÑADIR LA CONTESTACION
@app.put("/actualizar_contestacion/{id_solicitud}/{respuesta}")
async def actualizar_contestacion(id_solicitud: int, respuesta: str, db: Session = Depends(get_db)):
    solicitud = db.query(Solicitud).filter(Solicitud.id_solicitud == id_solicitud).first()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")

    # Actualizar los campos
    solicitud.contestacion = True
    solicitud.respuesta = respuesta  

    db.commit()
    








##METODO PARA ACTUALIZAR ESTUDIANTE
@app.put("/actualizarestudiante/{documento}")
async def actualizar_estudiante(
    documento: str,
    tipo_de_documento: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    celular: str = Form(...),
    correo: str = Form(...),
    direccion: str = Form(...),
    sede: str = Form(...),
    usuario: str = Form(...),
    contraseña: str = Form(...),
    nivel_actual: str = Form(...),
    plan: str = Form(...),
    file: UploadFile = File(None),  
    db: Session = Depends(get_db)
):
    estudiante_existente = db.query(Estudiante).filter(Estudiante.documento == documento).first()
    
    if not estudiante_existente:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    if usuario != estudiante_existente.usuario:  # Solo verificar si el usuario ha cambiado
        if usuario_existe_globalmente(usuario, db):
            raise HTTPException(status_code=400, detail=f"El usuario '{usuario}' ya está en uso.")
    
    if not verify_cel(celular):
        raise HTTPException(status_code=400, detail="Número de celular inválido, debe tener 10 dígitos.")
    
    if file:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        
        folder_path = "static/micarpetaimg"
        file_location = os.path.join(folder_path, file.filename)

        os.makedirs(folder_path, exist_ok=True)

        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())

        foto_perfil_url = f"/images/{file.filename}"
    else:
        foto_perfil_url = estudiante_existente.foto_perfil  

    # Actualizar datos del estudiante
    estudiante_existente.tipo_de_documento = tipo_de_documento
    estudiante_existente.nombre = nombre
    estudiante_existente.apellido = apellido
    estudiante_existente.fecha_nacimiento = fecha_nacimiento
    estudiante_existente.genero = genero
    estudiante_existente.celular = celular
    estudiante_existente.correo = correo
    estudiante_existente.direccion = direccion
    estudiante_existente.sede = sede

    # Verificar si el usuario ha cambiado
    if usuario != estudiante_existente.usuario:
        estudiante_existente.usuario = usuario  # Actualizar usuario solo si ha cambiado

    # Verificar si la contraseña fue modificada
    if contraseña != estudiante_existente.contraseña:
        if not verificar_contraseña(contraseña):
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres, incluyendo números, caracteres especiales y mayúsculas.")
        estudiante_existente.contraseña = encriptar_contraseña(contraseña)  # Encriptar solo si se cambió

    estudiante_existente.nivel_actual = nivel_actual
    estudiante_existente.plan = plan
    estudiante_existente.foto_perfil = foto_perfil_url  

    try:
        db.commit()
        db.refresh(estudiante_existente)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")





##METODO PARA ACTUALIZAR PROFESOR
@app.put("/actualizarprofesor/{documento}")
async def actualizar_profesor(
    documento: str,
    tipo_de_documento: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    celular: str = Form(...),
    correo: str = Form(...),
    direccion: str = Form(...),
    usuario: str = Form(...),
    contraseña: str = Form(...),
    file: UploadFile = File(None),  
    db: Session = Depends(get_db)
):
    profesor_existente = db.query(Profesor).filter(Profesor.documento == documento).first()
    
    if not profesor_existente:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    
    if usuario != profesor_existente.usuario:  # Solo verificar si el usuario ha cambiado
        if usuario_existe_globalmente(usuario, db):
            raise HTTPException(status_code=400, detail=f"El usuario '{usuario}' ya está en uso.")
    
    if not verify_cel(celular):
        raise HTTPException(status_code=400, detail="Número de celular inválido, debe tener 10 dígitos.")
    
    if file:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        
        folder_path = "static/micarpetaimg"
        file_location = os.path.join(folder_path, file.filename)

        os.makedirs(folder_path, exist_ok=True)

        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())

        foto_perfil_url = f"/images/{file.filename}"
    else:
        foto_perfil_url = profesor_existente.foto_perfil  

    # Actualizar datos del estudiante
    profesor_existente.tipo_de_documento = tipo_de_documento
    profesor_existente.nombre = nombre
    profesor_existente.apellido = apellido
    profesor_existente.fecha_nacimiento = fecha_nacimiento
    profesor_existente.genero = genero
    profesor_existente.celular = celular
    profesor_existente.correo = correo
    profesor_existente.direccion = direccion

    # Verificar si el usuario ha cambiado
    if usuario != profesor_existente.usuario:
        profesor_existente.usuario = usuario  # Actualizar usuario solo si ha cambiado

    # Verificar si la contraseña fue modificada
    if contraseña != profesor_existente.contraseña:
        if not verificar_contraseña(contraseña):
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres, incluyendo números, caracteres especiales y mayúsculas.")
        profesor_existente.contraseña = encriptar_contraseña(contraseña)  # Encriptar solo si se cambió

    profesor_existente.foto_perfil = foto_perfil_url  

    try:
        db.commit()
        db.refresh(profesor_existente)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Algo salió mal: {str(e)}")



#METODO PARA DESACTIVAR LA CUENTA UN ESTUDIANTE
@app.put("/desactivarestudiante/{documento}")
async def delete_estudiante(documento:str,db:Session=Depends(get_db)):
    estudiante_encontrado=db.query(Estudiante).filter(documento==Estudiante.documento).first()
    if estudiante_encontrado:
        estudiante_encontrado.estado=False
        db.commit()
        db.refresh(estudiante_encontrado)
        return f"estudiante con documento {documento} deshabilitado"
    else:
        raise HTTPException (status_code=400, detail="no se encontro estudiante")



#METODO PARA DESACTIVAR LA CUENTA DE UN PROFESOR
@app.put("/desactivarprofesor/{documento}")
async def delete_estudiante(documento:str,db:Session=Depends(get_db)):
    profesor_encontrado=db.query(Profesor).filter(documento==Profesor.documento).first()
    if profesor_encontrado:
        profesor_encontrado.estado=False
        db.commit()
        db.refresh(profesor_encontrado)
        return f"profesor con documento {documento} deshabilitado"
    else:
        raise HTTPException (status_code=400, detail="no se encontro profesor")
    


#METODO PARA DESACTIVAR LA CUENTA UN ESTUDIANTE
@app.put("/activarestudiante/{documento}")
async def activar_estudiante(documento:str,db:Session=Depends(get_db)):
    estudiante_encontrado=db.query(Estudiante).filter(documento==Estudiante.documento).first()
    if estudiante_encontrado:
        estudiante_encontrado.estado=True
        db.commit()
        db.refresh(estudiante_encontrado)
        return f"estudiante con documento {documento} habilitado"
    else:
        raise HTTPException (status_code=400, detail="no se encontro estudiante")



#METODO PARA DESACTIVAR LA CUENTA DE UN PROFESOR
@app.put("/activarprofesor/{documento}")
async def activar_estudiante(documento:str,db:Session=Depends(get_db)):
    profesor_encontrado=db.query(Profesor).filter(documento==Profesor.documento).first()
    if profesor_encontrado:
        profesor_encontrado.estado=True
        db.commit()
        db.refresh(profesor_encontrado)
        return f"profesor con documento {documento} habilitado"
    else:
        raise HTTPException (status_code=400, detail="no se encontro profesor")    
