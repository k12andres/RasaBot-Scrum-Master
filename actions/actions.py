# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

# This is a simple example for a custom action which utters "Hello World!"

from os import name
from typing import Any, Text, Dict, List, Union
#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import json
from datetime import datetime
#
#Para los algoritmos de machine learning:
import pandas as pd #Es para un archivo csv
import numpy as np
import matplotlib.pyplot as plt
from sklearn import linear_model
#
ruta_tareas = r'C:\Users\k12_a\Documents\rasabot\Tareas.json'
ruta_empleados = r'C:\Users\k12_a\Documents\rasabot\Empleados.json'
now= datetime.now()
t1 = open(ruta_tareas)
t2 = open(ruta_empleados)
aux1 = t1.read()
aux2 = t2.read()
tareas = json.loads(aux1)
empleados = json.loads(aux2)
#Para ML
data = pd.read_csv(r'C:\Users\k12_a\Documents\rasabot\EmpleadosData.csv')
data.head()
X = data[["edad", "genero", "desempenio"]]
Y = data["isActive"]
#Generacion de modelos de entrenamiento
train = data[:(int((len(data)*0.8)))]
test = data[(int((len(data)*0.8))):]
regr = linear_model.LinearRegression()

train_x = np.array(train[['edad', 'genero', 'desempenio']])
train_y = np.array(train["isActive"])
test_x = np.array(test[['edad', 'genero', 'desempenio']])
test_y = np.array(test["isActive"])


def guardararchivos():
    a1 = json.dumps(tareas, indent=4)
    t1 = open(ruta_tareas,'w')
    t1.write(a1)
    t1.close()
    a2 = json.dumps(empleados, indent=4)
    t2 = open(ruta_empleados,'w')
    t2.write(a2)
    t2.close()

class ActionGuardarNombre(Action):

    def name(self) -> Text:
        return "action_saludo"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        empleado= next(tracker.get_latest_entity_values("empleado"), None)
        hora_actual = now.hour
        if (6 > hora_actual and hora_actual < 13):
            message = "Buenos dias, "
        elif (hora_actual < 20):
            message = "Buenas tardes, "
        else:
            message = "Buenas noches, "
        message = message + str(empleado)
        dispatcher.utter_message(text=str(message))

        guardararchivos()

        return [SlotSet("name",str(empleado))]
        

class ActionDespedida(Action):

    def name(self) -> Text:
        return "action_despedida"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")
        dispatcher.utter_message(text="Nos vemos "+str(name)+". Observaciones: ")

        if (str(name) != "Admin"):
            dispatcher.utter_message(text="Hasta luego, "+str(name)+". Observaciones: ")
            if (empleados[name]["cambio_horario"] > 2):
                dispatcher.utter_message(text="Deberias ser mas fiel a tu horario.")
            
            elif (len(empleados[name]["faltas_trabajo"]) > 2):
                dispatcher.utter_message(text="Si sigues faltando al trabajo se notificara a tu jefe.")

            if (empleados[name]["desempenio"] < 5):
                dispatcher.utter_message(text="Estas teniendo un desempenio bastante flojo, puedes esfuerzate mas.")
            elif (empleados[name]["desempenio"] > 7):
                dispatcher.utter_message(text="Estas teniendo un desempenio bastante bueno.")
            else:
                dispatcher.utter_message(text="Estas teniendo un desempenio decente, todavia puedes mejorar.")
        else:
            regr.fit(train_x, train_y)
            coeff_data = pd.DataFrame(regr.coef_, X.columns, columns=["Coeficientes"])
            Y_pred = regr.predict(test_x)

            dispatcher.utter_message(text=str("Estos son los datos a tener en cuenta en una contratacion: \n"+str(coeff_data)+"\n Indice de prediccion: "+str(Y_pred)))#Asumimos que el admin conoce los modelos analiticos lineales.

        guardararchivos()
        return []


class MostrarPerfil(Action):

    def name(self) -> Text:
        return "mostrar_perfil"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")
        message="Su perfil es: \n"
        message=message+"Nombre: " + str(name)+".\n"+str(empleados[str(name)])
        
        dispatcher.utter_message(text=str(message)) 
        return []


class DarTiempo(Action):

    def name(self) -> Text:
        return "dar_tiempo"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")

        if (str(name) != "Admin"):
            if (empleados[name]["Tarea"]["Nombre"] == None):
                dispatcher.utter_message(text=str(name)+", no tienes ninguna tarea asignada, por lo que no puedes pedir mas tiempo.")
            else:
                if (empleados[name]["pidio_tiempo"] < 3):
                    empleados[name]["pidio_tiempo"]= empleados[name]["pidio_tiempo"]+1
                    dispatcher.utter_message(text=str("Tienes una semana mas."))
                else:
                    message="No, " + str(name) + " has exedido tu tiempo prestado."
                    empleados["Admin"]["Tiempo prestado"].append(str(name)+" ,"+str(now))
                    dispatcher.utter_message(text=str(message))
                    if (empleados[name]["desempenio"] > 0):
                        empleados[name]["desempenio"] = empleados[name]["desempenio"] - 1
        else:
            dispatcher.utter_message(text=str("Usted es el Admin, no puede acceder a las funciones de empleados."))
                
        guardararchivos()
        return []


class DarDias(Action):

    def name(self) -> Text:
        return "dar_dia"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")
        motivo = next(tracker.get_latest_entity_values("falta_trabajo"), None)
        ban1 = True
        ban2 = True

        if (str(name) != "Admin"):
            if (empleados[name]["faltas_trabajo"].count(str(motivo)) > 0):
                dispatcher.utter_message(text="El motivo por el cual vas a faltar ya lo habias mencionado antes.")
                empleados["Admin"]["Faltas al trabajo"].append(str(name)+" ,fala por el mismo motivo. Aviso el dia: "+str(now))
                if (empleados[name]["desempenio"] > 0):
                    empleados[name]["desempenio"] = empleados[name]["desempenio"] - 1
                ban1 = False
            empleados[name]["faltas_trabajo"].append(motivo)

            if (len(empleados[name]["faltas_trabajo"]) > 2):
                message=str(name) + ", has exedido la cantidad de dias. Se informara al administrador."
                empleados["Admin"]["Faltas al trabajo"].append(str(name)+" ,"+str(now))
                dispatcher.utter_message(text=str(message))
                empleados[name]["desempenio"] = empleados[name]["desempenio"] - 1
                ban2 = False
            if (ban1 and ban2):
                message="Si, " + str(name) + " puedes tomarte el dia sin problemas.\nYa vas pidiendo " + str(len(empleados[name]["faltas_trabajo"])) + "."
                dispatcher.utter_message(text=str(message))
        else:
            dispatcher.utter_message(text=str("Usted es el Admin, no puede acceder a las funciones de empleados."))

        guardararchivos()
        return []

class ActionGuardarNombre(Action):

    def name(self) -> Text:
        return "guardar_empleado_molesto"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        empleado_molesto = next(tracker.get_latest_entity_values("empleado"), None)
        dispatcher.utter_message(text="¿Cual es el motivo?")
        
        guardararchivos()

        return [SlotSet("empleado_molesto",str(empleado_molesto))]

class Problema_Compa(Action):

    def name(self) -> Text:
        return "problem_compa"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        empleado_molesto = tracker.get_slot("empleado_molesto")
        empleado_actual = tracker.get_slot("name")

        if (str(empleado_actual) != "Admin"):
            if (str(empleado_actual) == str(empleado_molesto)):
                message="No puede hacer quejas por tener problemas con usted mismo, deberia a un psicologo."
                dispatcher.utter_message(text=str(message))
            else:
                message="Se le informara al Administrador del problema."
                dispatcher.utter_message(text=str(message))
                motivo = next(tracker.get_latest_entity_values("motivo_problema"), None)
                empleados[empleado_molesto]["molesto_a"].append("molesto a "+str(empleado_actual)+ ", el dia "+ str(now) + ", motivo: "+str(motivo))
                empleados[empleado_actual]["fue_molestado_por"].append("fue molestado por "+str(empleado_molesto)+ ", el dia "+ str(now) + ", motivo: "+str(motivo))
                empleados["Admin"]["Registro de conflictos"].append("El empleado: "+str(empleado_molesto)+", molesto a "+str(empleado_actual)+ ", el dia "+ str(now) + ", motivo: "+str(motivo))
        else:
            dispatcher.utter_message(text=str("Usted es el Admin, no puede acceder a las funciones de empleados."))
            
        guardararchivos()
        return []

class Cambiar_horario(Action):

    def name(self) -> Text:
        return "cambiar_horario"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")
        if (str(name) != "Admin"):
            if (empleados[name]["cambio_horario"] > 2):
                dispatcher.utter_message(text="Ya has cambiado tu horario anteriormente numerosas veces, no es posible volver a cambiarlo.")
                empleados["Admin"]["Cambios de horario"].append(str(name)+" ,"+str(now))
                if (empleados[name]["desempenio"] > 0):
                    empleados[name]["desempenio"] = empleados[name]["desempenio"] - 1
            else:
                nuevo_horario = next(tracker.get_latest_entity_values("horario"), None)
            
                if (str(empleados[name]["Horario"]) == str(nuevo_horario)):
                    dispatcher.utter_message(text="El horario ingresado es el mismo que ya estaba asignado.")
                else:
                    dispatcher.utter_message(text="Su horario paso de ser "+str(empleados[name]["Horario"])+" a "+str(nuevo_horario))
                    empleados[name]["Horario"] = str(nuevo_horario)
                    empleados[name]["cambio_horario"] = empleados[name]["cambio_horario"] + 1
        else:
            dispatcher.utter_message(text=str("Usted es el Admin, no puede acceder a las funciones de empleados."))

        guardararchivos()
        return []

class Mostrar_Tareas(Action):

    def name(self) -> Text:
        return "mostrar_tareas"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        for tareita in tareas:
            dispatcher.utter_message(text=str(tareita)+": "+str(tareas[tareita]))
        return []

class Asignar_Tarea(Action):

    def name(self) -> Text:
        return "asignar_una_tarea"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")

        if (str(name) != "Admin"):
            tarea_pedida = next(tracker.get_latest_entity_values("tarea"), None)
            if (empleados[name]["Tarea"]["Nombre"] != None):
                dispatcher.utter_message(text="Ya tenias una tarea asignada, no se puede pedir otra tarea hasta terminar la actual.")
            else:
                bandera = False
                for tareita in tareas: #Me fijo si existe la tarea pedida
                    if (str(tareita) == str(tarea_pedida)):
                        bandera = True
                        break 
                bandera2 = False
                if (bandera):
                    bandera2 = True
                    for req in tareas[tarea_pedida]["Requisito_Lenguajes"]: # Me fijo si cumple los requisitos
                        cant = empleados[name]["lenguajes"].count(req)
                        if (cant == 0):
                            bandera2 = False
                            break
                    if (empleados[name]["desempenio"] < tareas[tarea_pedida]["Requisito_Calidad"]):
                        bandera2 = False

                if (bandera and bandera2):
                    empleados[name]["Tarea"]["Nombre"] = str(tarea_pedida)
                    empleados[name]["Tarea"]["Caracteristicas"] = tareas[tarea_pedida]["Caracteristicas"]
                    empleados[name]["Tarea"]["Requisito_Lenguajes"] = tareas[tarea_pedida]["Requisito_Lenguajes"]
                    empleados[name]["Tarea"]["Requisito_Calidad"] = tareas[tarea_pedida]["Requisito_Calidad"]
                    empleados[name]["Tarea"]["Semanas_Restantes"] = tareas[tarea_pedida]["Semanas_Restantes"]
                    empleados["Admin"]["Tarea asignada"].append("A "+str(name)+" se le asigno la tarea "+str(tarea_pedida)+", el dia "+str(now))

                    dispatcher.utter_message(text="La tarea "+tarea_pedida+" fue asignada.")
                    tareas.pop(tarea_pedida)
                elif (not bandera):
                    dispatcher.utter_message(text="La tarea "+tarea_pedida+" no existe.")
                else:
                    dispatcher.utter_message(text="No cumples los requisitos suficientes.")
        else:
            dispatcher.utter_message(text=str("Usted es el Admin, no puede acceder a las funciones de empleados."))
        guardararchivos()
        return []

class Finalizar_Tarea(Action):

    def name(self) -> Text:
        return "terminar_tarea"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")

        if (str(name) != "Admin"):
            if (empleados[name]["Tarea"]["Nombre"] == None):
                dispatcher.utter_message(text="No tenias ninguna tarea asignada.")
            else:
                empleados["Admin"]["Tareas finalizadas"].append(str(name)+" finalizo la tarea "+str(empleados[name]["Tarea"]["Nombre"])+str(now))
                empleados[name]["Tarea"]["Nombre"] = None
                empleados[name]["Tarea"]["Caracteristicas"] = None
                empleados[name]["Tarea"]["Requisito_Lenguajes"] = None
                empleados[name]["Tarea"]["Requisito_Calidad"] = None
                empleados[name]["Tarea"]["Semanas_Restantes"] = None
                dispatcher.utter_message(text="Excelente "+str(name)+", tu tarea ha sido completada.")

                empleados[name]["desempenio"] = empleados[name]["desempenio"] + 2
                if (empleados[name]["desempenio"] > 10):
                        empleados[name]["desempenio"] = 10
        else:
            dispatcher.utter_message(text=str("Usted es el Admin, no puede acceder a las funciones de empleados."))
                    
        guardararchivos()
        return []