from modelo import *
from sqlalchemy.orm import Session 
from schemas import *
from datetime import date
from dateutil.relativedelta import relativedelta

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


    
