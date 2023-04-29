
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
import sys
import parametros as p

WINDOW_NAME_1, BASE_CLASS_1 = uic.loadUiType("ventana_inicio.ui")
WINDOW_NAME_3, BASE_CLASS_3 = uic.loadUiType("ventana_post_ronda.ui")
WINDOW_NAME_4, BASE_CLASS_4 = uic.loadUiType("final.ui")

class VentanaInicio(WINDOW_NAME_1, BASE_CLASS_1):

    #Señales:
    signal_cargar_juego = pyqtSignal()
    signal_crear_juego = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_gui()
        imagen = QPixmap(p.LOGO)
        self.imagen.setPixmap(imagen)
        self.imagen.setScaledContents(True)

    def init_gui(self):
        self.boton_juego_cargar.clicked.connect(self.cargar_juego)
        self.boton_juego_crear.clicked.connect(self.crear_juego)

    def cargar_juego(self):
        self.signal_cargar_juego.emit()
        self.hide()

    def crear_juego(self):
        self.signal_crear_juego.emit()
        self.hide()

class VentanaPostRonda(WINDOW_NAME_3, BASE_CLASS_3):

    signal_post_ronda = None
    signal_guardar = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def init_signal(self):
        self.signal_post_ronda.connect(self.mostrar_datos)
        self.boton_salir.clicked.connect(self.salir)
        self.boton_continuar.clicked.connect(self.continuar)
        self.boton_guardar.clicked.connect(self.guardar)

    def mostrar_datos(self, datos):
        self.perdidos_lcd.display(datos['perdidos'])
        self.atendidos_lcd.display(datos['atendidos'])
        self.reputacion_valor.setText(f'{datos["reputacion"]}/5')
        self.dinero_lcd.display(datos['dinero'])
        self.show()

    def guardar(self):
        self.signal_guardar.emit()

    def continuar(self):
        self.hide()

    def salir(self):
        sys.exit()

class Final(WINDOW_NAME_4, BASE_CLASS_4):

    signal_fin_juego = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def init_signals(self):
        self.boton_salir.clicked.connect(self.salir)
        self.signal_fin_juego.connect(self.mostrar)

    def mostrar(self):
        self.show()

    def salir(self):
        sys.exit()