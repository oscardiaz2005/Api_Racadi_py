from db.modelo import *
from sqlalchemy.orm import Session 
from db.schemas import *
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import datetime
from fastapi import HTTPException




def obtener_saldo(plan:str ,db: Session):
    plan=db.query(Plan).filter(Plan.nombre==plan).first()
    saldo=plan.costo
    return saldo

def obtener_pago_minimo(plan:str,db:Session):
    plan=db.query(Plan).filter(Plan.nombre==plan).first()
    Pago_minimo=plan.costo/plan.meses
    return Pago_minimo

def obtener_fecha_proximo_pago(fecha_inscripcion: date) -> date:
    fecha_proximo_pago = fecha_inscripcion + relativedelta(months=1)
    return fecha_proximo_pago


#FUNCIONES PARA VERIFICAR DIAS DE MORA Y ACTUALIZAR SALDO

#DiAS DE MORA
def actualizar_dias_mora(documento: str, db: Session):

    cuenta_encontrada = db.query(Cuenta).filter(Cuenta.documento == documento).first()

    fecha_actual = datetime.now().date()
    fecha_proximo_pago = cuenta_encontrada.fecha_proximo_pago

    if fecha_actual > fecha_proximo_pago:
        dias_mora_actualizados = (fecha_actual - fecha_proximo_pago).days

        cuenta_encontrada.dias_mora = dias_mora_actualizados
        
        db.commit()
        db.refresh(cuenta_encontrada)

    else:
        cuenta_encontrada.dias_mora = 0
    db.commit()
    db.refresh(cuenta_encontrada)


#INCREMENTAR PAGO MINIMO
def actualizar_pago_minimo(documento: str, db: Session):
    cuenta_encontrada = db.query(Cuenta).filter(Cuenta.documento == documento).first()
    
    if cuenta_encontrada:
        dias_mora = cuenta_encontrada.dias_mora
        pago_minimo_base = calcular_pago_minimo_base(cuenta_encontrada.documento,db) 
    
        
        if dias_mora > 0:
            pago_minimo_actualizado = pago_minimo_base * (1.02 ** dias_mora)
            
        # aqui limito el incremento a un 40% del precio original para que no sea abusivo 
            limite = pago_minimo_base * 1.4
            cuenta_encontrada.pago_minimo = min(pago_minimo_actualizado, limite)
        else :
            cuenta_encontrada.pago_minimo = pago_minimo_base

        db.commit()
        db.refresh(cuenta_encontrada)



def calcular_pago_minimo_base(documento: str, db: Session):
    estudiante_encontrado=db.query(Estudiante).filter(Estudiante.documento==documento).first()
    plan_encontrado = db.query(Plan).filter(estudiante_encontrado.plan==Plan.nombre).first()

    pago_minimo_base= round(plan_encontrado.costo/plan_encontrado.meses)
    return pago_minimo_base


#CALCULAR MONTO POR MORA
def calcular_monto_por_mora(documento: str, db: Session):
    estudiante_encontrado = db.query(Estudiante).filter(Estudiante.documento == documento).first()
    cuenta_encontrada = db.query(Cuenta).filter(Cuenta.documento == documento).first()
    plan_encontrado = db.query(Plan).filter(estudiante_encontrado.plan == Plan.nombre).first()
    pago_minimo_base = round(plan_encontrado.costo / plan_encontrado.meses)

    if cuenta_encontrada.dias_mora > 0:
        monto_por_mora = cuenta_encontrada.pago_minimo - pago_minimo_base
    else:
        monto_por_mora=0

    return monto_por_mora



#FUNCION PARA RETORNAR DATOS DE CUENTA
def obtener_dato_cuenta(documento: str, atributo: str, db: Session):

    cuenta = db.query(Cuenta).filter(Cuenta.documento == documento).first()

    if not cuenta:
        return None
    
    if atributo == "dias_mora":
        actualizar_dias_mora(cuenta.documento, db)
        return cuenta.dias_mora
    elif atributo == "pago_total":
        actualizar_pago_minimo(cuenta.documento, db)
        return cuenta.pago_minimo
    elif atributo == "monto_por_mora":
        return calcular_monto_por_mora(cuenta.documento, db)
    else:
        return getattr(cuenta, atributo, None) 


##FUNCION PARA VALIDAR PAGOS
def validar_pago(cuenta_documento:str,valor:int, db:Session):
    cuenta_encontrada=db.query(Cuenta).filter(Cuenta.documento==cuenta_documento).first()
    if not cuenta_encontrada:
        raise HTTPException(status_code=404, detail="El documento no coincide con ninguno de nuestros estudiantes")

    actualizar_dias_mora(cuenta_encontrada.documento,db)
    actualizar_pago_minimo(cuenta_encontrada.documento,db)

    if valor < cuenta_encontrada.pago_minimo:
        raise HTTPException(status_code=400, detail="El valor Ingresado es menor al del pago minimo requerido")
    if valor > cuenta_encontrada.saldo:
        raise HTTPException(status_code=400, detail="El valor Ingresado es mayor al saldo total")   

    return True 

## METODO PARA ACTUALIZAR SALDO
def actualizar_saldo(documento:str,valor:int,db:Session):
    cuenta_encontrada=db.query(Cuenta).filter(Cuenta.documento==documento).first()
    cuenta_encontrada.saldo-=valor
    db.commit()
    db.refresh(cuenta_encontrada)


## METODO PARA ACTUALIZAR FECHA DEL PROXIMO PAGO
def actualizar_fecha_proximo_pago(documento: str, db: Session):
    cuenta_encontrada = db.query(Cuenta).filter(Cuenta.documento == documento).first()

    if cuenta_encontrada.fecha_proximo_pago:
        cuenta_encontrada.fecha_proximo_pago += relativedelta(months=1)
    db.commit()
    db.refresh(cuenta_encontrada)


#NO PERMITIR RESERVAR A LOS QUR TIENEN MAS DE $% DIAS DE MORA
def validar_dias_mora(documento:str,db:Session):
    cuenta=db.query(Cuenta).filter(documento==Cuenta.documento).first()
    actualizar_dias_mora(documento,db)
    if cuenta.dias_mora>=45:
        raise HTTPException (status_code=400, detail=f"Tu cuenta tiene {cuenta.dias_mora} días de mora. Para acceder a las reservas de clases, es necesario regularizar tu pago a la mayor brevedad")
    return True


