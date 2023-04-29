
# https://recursospython.com/guias-y-manuales/drag-and-drop-con-pyqt-4/
# https://stackoverflow.com/questions/50232639/drag-and-drop-qlabels-with-pyqt5

# Las clases de este módulo fueron sacadas de los link señalados arriba.
# Se les hizo algunas modificaciones para la tarea.

from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QDrag, QPainter, QPixmap

class DropLabel(QLabel):

    signal_drag_and_drop = None

    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.setAcceptDrops(True)  # Aceptar objetos

    def dragEnterEvent(self, event):
        # Ignorar objetos arrastrados sin información
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        pos = event.pos()
        # Guardamos el nombre del label
        nombre = event.mimeData().text()
        #Envío señal para que el juego vea si se cumplen los requisitos
        self.signal_drag_and_drop.emit(pos.x(), pos.y(), nombre)

class DraggableLabel(QLabel):

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < \
                QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimedata = QMimeData()
        # Aquí cambie para que reconozca el nombre del label y no un texto de label
        mimedata.setText(self.name)
        drag.setMimeData(mimedata)
        pixmap = QPixmap(self.size())
        painter = QPainter(pixmap)
        painter.drawPixmap(self.rect(), self.grab())
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.CopyAction | Qt.MoveAction)