
from PyQt5.QtCore import QThread
import parametros as p
import time
from reloj import Reloj
import random

class Mesero(QThread):

    def __init__(self, x, y):
        super().__init__()
        self.__x = x
        self.__y = y
        self.direccion = 'down'
        self.__frame = 2
        self.ocupado = False
        self.propina = 0
        self.nivel_chef = 0

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, valor):
        if 0 <= valor <= p.ANCHO_PISO - p.ANCHO_MESERO:
            self.__x = valor

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, valor):
        if 0 <= valor <= p.LARGO_PISO - p.LARGO_MESERO:
            self.__y = valor

    @property
    def frame(self):
        return self.__frame

    @frame.setter
    def frame(self, valor):
        if valor > 3:
            self.__frame = 1
        else:
            self.__frame = valor

    def mover(self, event):
        self.frame += 1
        if event == 'D':
            self.x += p.VEL_MOVIMIENTO
            self.direccion = 'right'
            return 'A', self.frame, self.direccion
        if event == 'A':
            self.x -= p.VEL_MOVIMIENTO
            self.direccion = 'left'
            return 'D', self.frame, self.direccion
        if event == 'W':
            self.y -= p.VEL_MOVIMIENTO
            self.direccion = 'up'
            return 'S', self.frame, self.direccion
        if event == 'S':
            self.y += p.VEL_MOVIMIENTO
            self.direccion = 'down'
            return 'W', self.frame, self.direccion

    def run(self):
        while True:
            if self.ocupado:
                self.llevar_pedido()

    # Calcula la propina que da el cliente al mesero
    def llevar_pedido(self):
        tiempo = Reloj(p.INTERVALO_TIEMPO)
        tiempo.start()
        while self.ocupado:
            pass
        tiempo_espera = tiempo.value
        tiempo.finish()
        print('Calculando propina')
        propina = max(0, (self.nivel_chef*(1-tiempo_espera*0.05)/3))
        prob = random.randint(0, 1)
        if prob <= propina:
            print(f'El cliente dejó propina')
            self.propina = p.PROPINA
        else:
            print('El cliente no dejó propina')

class Chef(QThread):

    signal_update_animacion_chef = None

    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.platos_terminados = 0
        self.nivel = 1
        self.ocupado = False
        self.__frame = 1
        self.plato_listo = False
        self.activado = False
        self.reputacion_cafe = None

        self.restart = False

    @property
    def frame(self):
        return self.__frame

    @frame.setter
    def frame(self, valor):
        if valor > 15:
                self.__frame = 1
        else:
            self.__frame = valor

    def run(self):
        while True:
            while not self.restart:
                if not self.ocupado and self.activado:
                    if self.platos_terminados >= p.PLATOS_EXPERTO and self.nivel < 3:
                        self.nivel = 3
                        print('¡Ahora soy chef experto!')
                    elif self.platos_terminados >= p.PLATOS_INTERMEDIO and self.nivel < 2:
                        self.nivel = 2
                        print('¡Ahora soy chef intermedio!')
                    self.ocupado = True
                    self.cocinar()
                elif self.plato_listo and self.activado:
                    self.entregar_plato()
            self.signal_update_animacion_chef.emit({'x': self.x, 'y': self.y, 'frame': 1})
            self.plato_listo = False
            self.ocupado = False
            self.activado = False

    # Emite las señales para cambiar de imagen en el front-end
    def cocinar(self):
        bocadillo = Bocadillo()
        tiempo_preparacion = bocadillo.tiempo_preparacion(self.reputacion_cafe, self.nivel)
        tiempo_cocina = Reloj(p.INTERVALO_TIEMPO)
        tiempo_cocina.start()
        while tiempo_cocina.value < tiempo_preparacion and not self.restart:
            time.sleep(p.VELOCIDAD_CAMBIO_SPRITE)
            self.signal_update_animacion_chef.emit({'x': self.x, 'y': self.y, 'frame': self.frame})
            self.frame += 1
        prob = random.randint(0, 1)
        if prob < 0.3/(self.nivel + 1):
            print('Chef se equivocó en el plato')
            self.signal_update_animacion_chef.emit({'x': self.x, 'y': self.y, 'frame': 17})
            time.sleep(p.VELOCIDAD_CAMBIO_SPRITE)
            self.signal_update_animacion_chef.emit({'x': self.x, 'y': self.y, 'frame': 1})
            self.ocupado = False
        else:
            self.plato_listo = True
            self.platos_terminados += 1
            self.signal_update_animacion_chef.emit({'x': self.x, 'y': self.y, 'frame': 16})
        self.activado = False
        tiempo_cocina.finish()

    # Reinicia al chef
    def entregar_plato(self):
        self.signal_update_animacion_chef.emit({'x': self.x, 'y': self.y, 'frame': 1})
        self.plato_listo = False
        self.activado = False
        self.ocupado = False

class Mesa:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.disponibilidad = 'libre'

class Cliente(QThread):

    signal_update_animacion_cliente = None

    def __init__(self, x, y, tipo):
        super().__init__()
        self.x = x - p.ANCHO_CLIENTE
        self.y = y
        self.tipo = tipo #RELAJADO O APURADO o 'se fue' o 'bocadillo'
        self.tiempo_espera = Reloj(p.INTERVALO_TIEMPO)
        self.atendido = False
        self.__frame_desatendido = 26
        self.__frame_enojado = 18
        self.__frame_feliz = 13
        self.diccionario_datos = dict()
        self.paga = True
        self.stop = False

    @property
    def frame_desatendido(self):
        return self.__frame_desatendido

    @frame_desatendido.setter
    def frame_desatendido(self, valor):
        if valor > 30:
            self.__frame_desatendido = 26
        else:
            self.__frame_desatendido = valor

    @property
    def frame_enojado(self):
        return self.__frame_enojado

    @frame_enojado.setter
    def frame_enojado(self, valor):
        if valor > 24:
            self.__frame_enojado = 18
        else:
            self.__frame_enojado = valor

    @property
    def frame_feliz(self):
        return self.__frame_feliz

    @frame_feliz.setter
    def frame_feliz(self, valor):
        if valor > 14:
            self.__frame_feliz = 13
        else:
            self.__frame_feliz = valor

    def run(self):
        if not self.atendido:
            if self.tipo == 'relajado':
                self.espera_cliente(p.TIEMPO_ESPERA_RELAJADO)
            elif self.tipo == 'apurado':
                self.espera_cliente(p.TIEMPO_ESPERA_APURADO)

    # Emite las eñales para cambiar las visualizaciones de los clientes según sus estados.
    def espera_cliente(self, tiempo_espera):
        k = 1
        j = 1
        self.tiempo_espera.start()
        while True:
            if self.stop:
                self.signal_update_animacion_cliente.emit(
                    self.diccionario('se fue', self.frame_feliz))
                break
            elif not self.atendido:
                if self.tiempo_espera.value < tiempo_espera:
                    if self.tiempo_espera.value >= tiempo_espera / 2:
                        if self.tiempo_espera.value >= tiempo_espera - 2:
                            time.sleep(p.VELOCIDAD_CAMBIO_SPRITE)
                            self.signal_update_animacion_cliente.emit(
                                self.diccionario(self.tipo, self.frame_enojado))
                            self.frame_enojado += 3
                            self.paga = False
                        else:
                            time.sleep(p.VELOCIDAD_CAMBIO_SPRITE)
                            self.signal_update_animacion_cliente.emit(
                                self.diccionario(self.tipo, self.frame_desatendido))
                            self.frame_desatendido += 1
                else:
                    print('Cliente se va enojado porque no lo atendieron')
                    self.signal_update_animacion_cliente.emit(
                        self.diccionario('se fue', self.frame_desatendido))
                    self.tiempo_espera.finish()
                    break
            else:
                self.signal_update_animacion_cliente.emit(
                    self.diccionario('bocadillo', self.frame_feliz))
                while j <= 5:
                    time.sleep(p.VELOCIDAD_CAMBIO_SPRITE)
                    self.signal_update_animacion_cliente.emit(
                        self.diccionario(self.tipo, self.frame_feliz))
                    self.frame_feliz += 1
                    j += 1
                print('Cliente se va contento porque fue atendido')
                self.signal_update_animacion_cliente.emit(
                    self.diccionario('se fue', self.frame_feliz))
                self.signal_update_animacion_cliente.emit(
                    self.diccionario('bocadillo se fue', self.frame_feliz))
                break

    def diccionario(self, tipo, frame):
        return {'x': self.x,
                'y': self.y,
                'tipo': tipo,
                'atendido': self.atendido,
                'frame': frame,
                'paga': self.paga}

class Bocadillo:

    def __init__(self):
        self.precio = p.PRECIO_BOCADILLO

    def tiempo_preparacion(self, reputacion, nivel):
        tiempo_preparacion = max(0, 15 - reputacion - nivel * 2)
        return tiempo_preparacion

    def calidad_pedido(self, nivel, tiempo_espera):
        propina = max(0, (nivel * (1 - tiempo_espera * 0.05) / 3))
        return propina