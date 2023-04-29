import parametros as p
from PyQt5.QtCore import pyqtSignal, QThread
from entidades import Mesero, Chef, Mesa, Cliente
import random
from collections import defaultdict
import time
from math import floor

class DCCafe(QThread):

    signal_cargar_juego = None
    signal_crear_juego = None
    signal_comenzar_juego = pyqtSignal(dict)
    signal_drag_and_drop = None
    signal_crear_drag_and_drop = pyqtSignal(str, int, int, int)
    signal_comenzar_ronda = None
    signal_eliminar = None
    signal_eliminar_label = pyqtSignal(str, int, int)
    signal_mover_mesero = None
    signal_mover_mesero_2 = None
    signal_update_posicion_mesero = pyqtSignal(int, int, int, str, bool)
    signal_crear_cliente = pyqtSignal(int, int)
    signal_update_animacion_cliente = pyqtSignal(dict)
    signal_cliente_se_fue = None
    signal_pausar_ronda = None
    signal_colision_objeto = None
    signal_update_animacion_chef = pyqtSignal(dict)
    signal_update_display = pyqtSignal(dict)
    signal_post_ronda = pyqtSignal(dict)
    signal_guardar = None
    signal_fin_juego = pyqtSignal()
    signal_trampas = None

    def __init__(self):
        super().__init__()
        self.mesero = None
        self.chefs = dict()
        self.bocadillos = None
        self.clientes = dict()
        self.mesas = dict()
        self.dinero = p.DINERO_INICIAL
        self.reputacion = p.REPUTACION_INICIAL
        self.rondas_terminadas = 0
        self.disponibilidad = True
        # Pixeles del mapa que están libres y ocupados
        self.pixeles_mapa = defaultdict(lambda: "Hay puntos del objeto fuera del mapa")
        for i in range(0, p.ANCHO_PISO + 1):
            for j in range(0, p.LARGO_PISO + 1):
                # Le saco los arbustos de las esquinas
                if i < 30 and j < 60:
                    self.pixeles_mapa[f'({i},{j})'] = "arbol"
                elif i < 30 and j > p.LARGO_PISO - p.LARGO_ARBOL:
                    self.pixeles_mapa[f'({i},{j})'] = "arbol"
                else:
                    self.pixeles_mapa[f'({i},{j})'] = "libre"
        #Ocupo este diccionario para mandar todas las actualizaciones
        self.diccionario_datos = dict()
        self.diccionario_display = dict()
        # Truquito para eliminar "revertir" el cambio de posicion del mesero
        self.tecla_contraria = None
        self.clientes_atendidos = 0
        self.clientes_perdidos = 0
        self.clientes_proximos = 0
        self.clientes_eliminados = 0
        self.pausa = False

    def init_signals(self):
        self.signal_cargar_juego.connect(self.cargar)
        self.signal_crear_juego.connect(self.crear)
        self.signal_drag_and_drop.connect(self.drag_and_drop)
        self.signal_comenzar_ronda.connect(self.comenzar_ronda)
        self.signal_eliminar.connect(self.eliminar)
        self.signal_mover_mesero.connect(self.mover_mesero)
        self.signal_cliente_se_fue.connect(self.eliminar_cliente)
        self.signal_colision_objeto.connect(self.colisiones)
        self.signal_guardar.connect(self.guardar_partida)
        self.signal_trampas.connect(self.trampas)

    # Carga en el mapa una partida guardada
    def cargar(self):
        print("Se carga juego antiguo")
        self.disponibilidad = False
        with open(p.RUTA_DATOS, "r", encoding="utf-8") as archivo:
            fila_1 = archivo.readline()
            fila_1 = fila_1.strip().split(",")
            self.dinero = float(fila_1[0])
            self.reputacion = int(fila_1[1])
            self.rondas_terminadas += int(fila_1[2])
            fila_2 = archivo.readline()
            fila_2 = fila_2.strip().split(",")
        with open(p.RUTA_MAPA, "r", encoding = "utf-8") as archivo:
            filas = archivo.readlines()
            listas = [fila.strip().split(",") for fila in filas]
            for lista in listas:
                if lista[0] == 'mesero':
                    self.mesero = Mesero(int(lista[1]), int(lista[2]))
                    self.ocupar_pixel(
                        int(lista[1]), int(lista[2]), p.ANCHO_MESERO, p.LARGO_MESERO, 'mesero')
                    self.mesero.start()
                elif lista[0] == 'chef':
                    self.chefs[f'({lista[1]},{lista[2]})'] = Chef(int(lista[1]), int(lista[2]))
                    self.chefs[f'({lista[1]},{lista[2]})'].start()
                    self.ocupar_pixel(
                        int(lista[1]), int(lista[2]), p.ANCHO_CHEF, p.LARGO_CHEF, 'chef')
                elif lista[0] == 'mesa':
                    self.mesas[f'({lista[1]},{lista[2]})'] = Mesa(int(lista[1]), int(lista[2]))
                    self.ocupar_pixel(
                        int(lista[1]), int(lista[2]), p.ANCHO_MESA, p.LARGO_MESA, 'mesa')
        i = 0
        for chef in self.chefs:
            self.chefs[chef].platos_terminados = int(fila_2[i])
            i += 1
        self.update_diccionario_datos()
        self.signal_comenzar_juego.emit(self.diccionario_datos)
        self.start()

    # Cambia el estado del pixel para que se vea que ahora está ocupado
    def ocupar_pixel(self, x, y, ancho, largo, tipo):
        for i in range(x, x + ancho + 1):
            for j in range(y, y + largo + 1):
                self.pixeles_mapa[f'({i},{j})'] = [tipo, x, y]

    # Crea una nueva partida con objetos nuevos
    def crear(self):
        print("Se crea nuevo juego")
        self.agregar_figuras_aleatorias('mesero', p.ANCHO_MESERO, p.LARGO_MESERO, 1)
        self.agregar_figuras_aleatorias('chef', p.ANCHO_CHEF, p.LARGO_CHEF, p.CHEFS_INICIALES)
        self.agregar_figuras_aleatorias('mesa', p.ANCHO_MESA, p.LARGO_MESA, p.MESAS_INICIALES)
        self.update_diccionario_datos()
        self.signal_comenzar_juego.emit(self.diccionario_datos)
        self.start()

    # Retorna si algún pixel que se quiere llenar ya está ocupado
    def pixel_ocupado(self, pos_x, y, ancho, largo, tipo):
        ocupado = False
        # Para la mesa le agrego el ancho del cliente para que no se peguen
        if tipo == 'mesa':
            x = pos_x - p.ANCHO_CLIENTE
            ancho = ancho + p.ANCHO_CLIENTE
        else:
            x = pos_x
        for i in range(x, x + ancho):
            for j in range(y, y + largo):
                if self.pixeles_mapa[f'({i},{j})'] != 'libre':
                    print('Hay un pixel ocupado')
                    ocupado = True
                    return ocupado
        return ocupado

    # Agrega figuras aleatorias a los pixeles del mapa al crear un juego nuevo
    def agregar_figuras_aleatorias(self, tipo, ancho, largo, cantidad_inicial):
        for valor in range(cantidad_inicial):
            ocupado = True
            while ocupado:
                x = random.randint(15, p.ANCHO_PISO - ancho)
                y = random.randint(0, p.LARGO_PISO - largo)
                ocupado = self.pixel_ocupado(x, y, ancho, largo, tipo)
                if not ocupado:
                    for i in range(x, x + ancho + 1):
                        for j in range(y, y + largo + 1):
                            self.pixeles_mapa[f'({i},{j})'] = [tipo, x, y]
                    if tipo == 'chef':
                        self.chefs[f'({x},{y})'] = Chef(x, y)
                        self.chefs[f'({x},{y})'].start()
                    elif tipo == 'mesa':
                        self.mesas[f'({x},{y})'] = Mesa(x, y)
                    elif tipo == 'mesero':
                        self.mesero = Mesero(x, y)
                        self.mesero.start()

    # Permite agregar objetos por Drag and Drop
    def drag_and_drop(self, pos_x, pos_y, nombre):
        if nombre == 'chef' and self.dinero >= p.PRECIO_CHEF and not self.disponibilidad:
            ocupado = self.pixel_ocupado(pos_x, pos_y, p.ANCHO_CHEF, p.LARGO_CHEF, nombre)
            if not ocupado:
                self.dinero -= p.PRECIO_CHEF
                self.chefs[f'({int(pos_x)},{int(pos_y)})'] = Chef(int(pos_x), int(pos_y))
                self.chefs[f'({int(pos_x)},{int(pos_y)})'].start()
                self.agregar_figuras_drag_drop(pos_x, pos_y, p.ANCHO_CHEF, p.LARGO_CHEF, 'chef')
                # Enviar aprobación a front-end para que visualice
                self.signal_crear_drag_and_drop.emit('chef', self.dinero, pos_x, pos_y)
                self.update_diccionario_datos()
        elif nombre == 'mesa' and self.dinero >= p.PRECIO_MESA and not self.disponibilidad:
            ocupado = self.pixel_ocupado(pos_x, pos_y, p.ANCHO_MESA, p.LARGO_MESA, nombre)
            if not ocupado:
                self.dinero -= p.PRECIO_MESA
                self.mesas[f'({int(pos_x)},{int(pos_y)})'] = Mesa(int(pos_x), int(pos_y))
                self.agregar_figuras_drag_drop(pos_x, pos_y, p.ANCHO_MESA, p.LARGO_MESA, 'mesa')
                self.signal_crear_drag_and_drop.emit('mesa', self.dinero, pos_x, pos_y)
                self.update_diccionario_datos()

    # Agrega objeto por Drag and Drop a los pixeles ocupados
    def agregar_figuras_drag_drop(self, x, y, ancho, largo, tipo):
        for i in range(x, x + ancho + 1):
            for j in range(y, y + largo + 1):
                self.pixeles_mapa[f'({i},{j})'] = [tipo, x, y]

    # Elimina objeto del mapa
    def eliminar(self, x, y):
        print(self.pixeles_mapa[f'({x},{y})'][0])
        if self.pixeles_mapa[f'({x},{y})'] != 'libre' and not self.disponibilidad :
            x_origen = self.pixeles_mapa[f'({x},{y})'][1]
            y_origen = self.pixeles_mapa[f'({x},{y})'][2]
            if self.pixeles_mapa[f'({x},{y})'][0] == 'chef' and len(self.chefs) > 1:
                self.liberar_pixeles(x_origen, y_origen, p.ANCHO_CHEF, p.LARGO_CHEF)
                self.chefs.pop(f'({x_origen},{y_origen})')
                self.signal_eliminar_label.emit('chef', x_origen, y_origen)
                self.update_diccionario_datos()
                print('Chef eliminado')
            elif self.pixeles_mapa[f'({x},{y})'][0] == 'mesa' and len(self.mesas) > 1:
                self.liberar_pixeles(x_origen, y_origen, p.ANCHO_MESA, p.LARGO_MESA)
                self.mesas.pop(f'({x_origen},{y_origen})')
                self.signal_eliminar_label.emit('mesa', x_origen, y_origen)
                self.update_diccionario_datos()
                print('Mesa eliminada')

    # Libera el espacio en pixeles al eliminar un objeto del mapa
    def liberar_pixeles(self, x, y, ancho, largo):
        for i in range(x, x + ancho + 1):
            for j in range(y, y + largo + 1):
                self.pixeles_mapa[f'({i},{j})'] = 'libre'

    # Permite actualizar la posicion al mesero y envía la señal al frontend para mover al mesero
    def mover_mesero(self, tecla):
        if self.disponibilidad:
            if tecla != 'ocupado':
                self.liberar_pixeles(self.mesero.x, self.mesero.y, p.ANCHO_MESERO, p.LARGO_MESERO)
                self.tecla_contraria, frame, posicion = self.mesero.mover(tecla)
                self.signal_update_posicion_mesero.emit(
                    self.mesero.x, self.mesero.y, frame, posicion, self.mesero.ocupado)
            elif tecla == 'ocupado':
                self.mesero.mover(self.tecla_contraria)

    # La ocupo para no escribir esto muchas veces...
    def update_diccionario_datos(self):
        self.diccionario_datos = {'mesero': self.mesero,
                            'chefs': self.chefs,
                            'mesas': self.mesas,
                            'dinero': self.dinero,
                            'reputacion': self.reputacion,
                            'rondas_terminadas': self.rondas_terminadas}

    # Cambia la disponibilidad para que el thread cambie y comience el loop de la ronda
    def comenzar_ronda(self):
        if not self.disponibilidad:
            print('Se comienza ronda')
            self.disponibilidad = True

    def run(self):
        while True:
            self.signal_update_display.emit(self.update_diccionario_display())
            while not self.disponibilidad:
                pass
            while self.disponibilidad:
                for chef in self.chefs:
                    self.chefs[chef].restart = False
                print('Empieza ronda')
                cantidad_clientes = self.clientes_ronda()
                self.clientes_proximos = cantidad_clientes
                print(f'Clientes ronda: {cantidad_clientes}')
                self.signal_update_display.emit(self.update_diccionario_display())
                while self.clientes_proximos > 0:
                    time.sleep(p.LLEGADA_CLIENTES)
                    if self.crear_cliente():
                        self.clientes_proximos -= 1
                        self.signal_update_display.emit(self.update_diccionario_display())
                while self.clientes_eliminados < cantidad_clientes:
                    pass
                self.finalizar_ronda()

    def finalizar_ronda(self):
        self.calcular_reputacion(self.clientes_ronda())
        self.signal_update_display.emit(self.update_diccionario_display())
        print('Fin de la ronda')
        for chef in self.chefs:
            self.chefs[chef].signal_update_animacion_chef = self.signal_update_animacion_chef
            self.chefs[chef].restart = True #Reinicio cada chef que estaba cocinando
        self.mesero.ocupado = False
        self.disponibilidad = False
        time.sleep(1)
        if self.reputacion > 0:
            self.rondas_terminadas += 1
            self.signal_post_ronda.emit(self.update_diccionario_display())
            self.clientes_atendidos = 0
            self.clientes_perdidos = 0
            self.clientes_proximos = 0
            self.clientes_eliminados = 0
        elif self.reputacion == 0:
            self.signal_fin_juego.emit()

    # Crea un cliente si es que hay una mesa disponible
    def crear_cliente(self):
        j = 0
        mesa_disponible = None
        for mesa in self.mesas:
            if self.mesas[mesa].disponibilidad == 'libre':
                self.mesas[mesa].disponibilidad = 'ocupada'
                mesa_disponible = mesa
                j += 1
                break
        if j == 1:
            x = self.mesas[mesa_disponible].x
            y = self.mesas[mesa_disponible].y
            prob = random.randint(0,1)
            if prob <= p.PROB_RELAJADO:
                self.clientes[(x, y)] = Cliente(x, y, 'relajado')
                print('Aparece un cliente relajado')
            else:
                self.clientes[(x, y)] = Cliente(x, y, 'apurado')
                print('Aparece un cliente apurado')
            self.signal_crear_cliente.emit(x, y)
            self.clientes[(x, y)].signal_update_animacion_cliente = \
                self.signal_update_animacion_cliente
            self.clientes[(x, y)].start()
            return True

    # Llega la señal de que el cliente se fue y libera la mesa
    def eliminar_cliente(self, cliente):
        x = cliente['x'] + p.ANCHO_CLIENTE
        y = cliente['y']
        self.clientes.pop((x, y))
        self.mesas[f'({x},{y})'].disponibilidad = 'libre'
        self.clientes_eliminados += 1
        if not cliente['paga']:
            self.clientes_perdidos += 1
            self.signal_update_display.emit(self.update_diccionario_display())

    # Calcula la cantidad de clientes que van a aparecer en la ronda
    def clientes_ronda(self):
        clientes_ronda = 5 * (1 + self.rondas_terminadas)
        return clientes_ronda

    # Modela las colisiones especiales del mesero con las mesas y los chefs
    def colisiones(self, objeto):
        tipo = objeto[0]
        x = objeto[1]
        y = objeto[2]
        if tipo == 'chef':
            self.chefs[f'({x},{y})'].signal_update_animacion_chef = \
                self.signal_update_animacion_chef
            if not self.chefs[f'({x},{y})'].ocupado and not self.chefs[f'({x},{y})'].plato_listo \
                    and not self.mesero.ocupado:
                print('El chef comenzará a preparar el pedido')
                self.chefs[f'({x},{y})'].reputacion_cafe = self.reputacion
                self.chefs[f'({x},{y})'].activado = True
            elif self.chefs[f'({x},{y})'].plato_listo and not self.mesero.ocupado:
                print('El chef te entregó el pedido listo')
                self.chefs[f'({x},{y})'].activado = True
                self.mesero.nivel_chef = self.chefs[f'({x},{y})'].nivel
                self.mesero.ocupado = True
        if self.mesero.ocupado:
            if tipo == 'cliente':
                print('Le entrego plato a cliente tocando al cliente')
                self.entregar_plato(x + p.ANCHO_CLIENTE, y)
            elif tipo == 'mesa' and self.mesas[f'({x},{y})'].disponibilidad == 'ocupada':
                print('Le entrego plato a cliente tocando la mesa')
                self.entregar_plato(x, y)

    # Cambia los datos después de entregar el plato
    def entregar_plato(self, x, y):
        self.clientes[(x, y)].atendido = True
        self.mesero.ocupado = False
        self.clientes_atendidos += 1
        self.dinero += p.PRECIO_BOCADILLO
        self.mesero.wait(80) # Espero para que se calcule la propina y se agregue
        print(self.mesero.propina)
        self.dinero += self.mesero.propina
        self.signal_update_display.emit(self.update_diccionario_display())

    def update_diccionario_display(self):
        self.diccionario_display = {'reputacion': self.reputacion, 'dinero': self.dinero,
                                    'ronda': self.rondas_terminadas,
                                    'atendidos': self.clientes_atendidos,
                                    'perdidos': self.clientes_perdidos,
                                    'proximos': self.clientes_proximos}
        return self.diccionario_display

    def calcular_reputacion(self, clientes_totales):
        nueva_reputacion = max(0, min(5, self.reputacion
                                      + floor(4 *(self.clientes_atendidos/clientes_totales) - 2)))
        self.reputacion = nueva_reputacion

    def guardar_partida(self):
        print('Partida guardada con éxito')
        linea_1_nueva = f'{self.dinero},{self.reputacion},{self.rondas_terminadas}\n'
        lista_2_nueva = []
        for chef in self.chefs:
            lista_2_nueva.append(str(self.chefs[chef].platos_terminados))
        linea_2_nueva = ','.join(lista_2_nueva)
        with open(p.RUTA_DATOS, "w", encoding="utf-8") as archivo:
            archivo.write(linea_1_nueva)
            archivo.write(linea_2_nueva)
        with open(p.RUTA_MAPA, "w", encoding="utf-8") as archivo:
            archivo.write(f'mesero,{self.mesero.x},{self.mesero.y}\n')
            for mesa in self.mesas:
                x = self.mesas[mesa].x
                y = self.mesas[mesa].y
                archivo.write(f'mesa,{x},{y}\n')
            for chef in self.chefs:
                x = self.chefs[chef].x
                y = self.chefs[chef].y
                archivo.write(f'chef,{x},{y}\n')

    def trampas(self, tipo):
        if tipo == 'dinero':
            print('DINERO TRAMPA')
            self.dinero += p.DINERO_TRAMPA
            self.signal_update_display.emit(self.update_diccionario_display())
        elif tipo == 'finalizar':
            if self.disponibilidad:
                print('FINALIZAR TRAMPA')
                self.clientes_proximos = 0 # Termino la creacion de nuevos clientes
                time.sleep(3) # Espero por si ya habia uno en proceso de creacion
                self.clientes_proximos = 0
                for cliente in self.clientes:
                    self.clientes[cliente].wait(100)
                    self.clientes[cliente].stop = True # Borro a los clientes del mapa
                self.clientes_eliminados = self.clientes_ronda() #Lo ocupo para finalizar la ronda
        elif tipo == 'reputacion':
            print('REPUTACIÓN TRAMPA')
            self.reputacion = p.REPUTACION_TRAMPA
            self.signal_update_display.emit(self.update_diccionario_display())