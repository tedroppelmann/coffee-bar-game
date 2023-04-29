import sys
from PyQt5.QtWidgets import QApplication

from ventanas import VentanaInicio, VentanaPostRonda, Final
from ventana_juego import VentanaPrincipal
from DCCafe import DCCafe

import os


if __name__ == '__main__':

    os.environ["QT_MAC_WANTS_LAYER"] = "1"

    def hook(type, value, traceback):
        print(type)
        print(traceback)
    sys.__excepthook__ = hook

    app = QApplication(sys.argv)

    #Instancio clases
    juego = DCCafe()
    ventana_inicio = VentanaInicio()
    ventana_principal = VentanaPrincipal()
    ventana_post_ronda = VentanaPostRonda()
    ventana_final = Final()

    # Conectar señales:
    # cargar juego
    juego.signal_cargar_juego = ventana_inicio.signal_cargar_juego
    ventana_principal.signal_comenzar_juego = juego.signal_comenzar_juego
    # crear juego
    juego.signal_crear_juego = ventana_inicio.signal_crear_juego
    # drag and drop
    juego.signal_drag_and_drop = ventana_principal.signal_drag_and_drop
    ventana_principal.signal_crear_drag_and_drop = juego.signal_crear_drag_and_drop
    # eliminar compra
    juego.signal_eliminar = ventana_principal.signal_eliminar
    ventana_principal.signal_eliminar_label = juego.signal_eliminar_label
    # comenzar ronda
    juego.signal_comenzar_ronda = ventana_principal.signal_comenzar_ronda
    # mover mesero
    juego.signal_mover_mesero = ventana_principal.signal_mover_mesero
    ventana_principal.signal_update_posicion_mesero = juego.signal_update_posicion_mesero
    # crear cliente
    ventana_principal.signal_crear_cliente = juego.signal_crear_cliente
    # update animacion cliente
    ventana_principal.signal_update_animacion_cliente = juego.signal_update_animacion_cliente
    # actualizar cuando cliente se va
    juego.signal_cliente_se_fue = ventana_principal.signal_cliente_se_fue
    # pausar ronda
    juego.signal_pausar_ronda = ventana_principal.signal_pausar_ronda
    # colsiones con objetos
    juego.signal_colision_objeto = ventana_principal.signal_colision_objeto
    # update animacion chef
    ventana_principal.signal_update_animacion_chef = juego.signal_update_animacion_chef
    # update datos del display
    ventana_principal.signal_update_display = juego.signal_update_display
    # mostrar ventana post-ronda
    ventana_post_ronda.signal_post_ronda = juego.signal_post_ronda
    # guardar partida
    juego.signal_guardar = ventana_post_ronda.signal_guardar
    # fin del juego
    ventana_final.signal_fin_juego = juego.signal_fin_juego
    # teclas trampa
    juego.signal_trampas = ventana_principal.signal_trampas


    # Iniciar señales:
    juego.init_signals()
    ventana_principal.init_signals()
    ventana_post_ronda.init_signal()
    ventana_final.init_signals()

    ventana_inicio.show()
    sys.exit(app.exec_())