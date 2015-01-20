from PySide.QtCore import *
from PySide.QtGui import *
import hiero.ui

class ClipInfoWindow(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(240, 160, 480, 320)
        self.setWindowTitle("Clip Info")

        self.setAttribute( Qt.WA_TranslucentBackground, True )  
        self.setWindowFlags( Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint )
        self.setWindowOpacity(0.9)
        self.setMouseTracking(True)

        self.draggable = True
        self.dragging_threshould = 2
        self.__mousePressPos = None
        self.__mouseMovePos = None

        self.infoDict = []
        self.infoDict += [{"label": "Clip", "value": "None", "enabled":True}]
        self.infoDict += [{"label": "Duration", "value": 0, "enabled":True}]

        self.table_model = MyTableModel(self, self.infoDict)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()

        # set font
        font = QFont()
        font.setPixelSize(16)
        self.table_view.setFont(font)

        self.table_view.setShowGrid(False)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setVisible(False)

        self.table_view.setStyleSheet("QTableView::item { border-width:0px; border-right: 1px solid gray; }")

        # set column width to fit contents (set font first!)
        self.table_view.setSortingEnabled(False)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view)
        self.setMinimumSize(320, 240)        
        self.setLayout(layout)

    def showAt(self, pos):
        # BUILD DATA WHEN SHOWN - is this the best time to do this?
        self.__buildDataForCurrentClip()
        self.updateTableView()
        self.move(pos.x()-self.width()/2, pos.y()-self.height()/2)
        self.show()

    def keyPressEvent(self, e):
        """Close the popover if Escape is pressed"""            
        if e.key() == Qt.Key_Escape:
            self.close()

    def updateTableView(self):
        self.table_model = MyTableModel(self, self.infoDict)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()

    def __buildDataForCurrentClip(self):
        cv = hiero.ui.currentViewer()
        seq = cv.player().sequence()
        self.infoDict = []
        if not seq:
            return
        elif isinstance(seq, hiero.core.Clip):
            self.infoDict += [{"label": "Clip", "value": seq.name(), "enabled":True}]
            self.infoDict += [{"label": "Duration", "value": seq.duration(), "enabled":True}]
            self.infoDict += [{"label": "Filename", "value": seq.mediaSource().fileinfos()[0].filename(), "enabled":True}]
        elif isinstance(seq, hiero.core.Sequence):
            self.infoDict += [{"label": "Sequence", "value": seq.name(), "enabled":True}]
            self.infoDict += [{"label": "Duration", "value": seq.duration(), "enabled":True}]

    def paintEvent(self, event):
        # get current window size
        s = self.size()
        qp = QPainter()
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.begin(self)
        qp.setBrush( self.palette().window() )
        qp.setPen(Qt.black)
        qp.drawRoundedRect(0,0,s.width(), s.height(), 10, 10)
        qp.end()
 
    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton:
            self.__mousePressPos = event.globalPos()                # global
            self.__mouseMovePos = event.globalPos() - self.pos()    # local
        super(ClipInfoWindow, self).mousePressEvent(event)
 
    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & Qt.LeftButton:
            globalPos = event.globalPos()
            moved = globalPos - self.__mousePressPos
            if moved.manhattanLength() > self.dragging_threshould:
                # move when user drag window more than dragging_threshould
                diff = globalPos - self.__mouseMovePos
                self.move(diff)
                self.__mouseMovePos = globalPos - self.pos()
        super(ClipInfoWindow, self).mouseMoveEvent(event)
 
    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            if event.button() == Qt.LeftButton:
                moved = event.globalPos() - self.__mousePressPos
                if moved.manhattanLength() > self.dragging_threshould:
                    # do not call click event or so on
                    event.ignore()
                self.__mousePressPos = None
        super(ClipInfoWindow, self).mouseReleaseEvent(event)
    

class MyTableModel(QAbstractTableModel):
    def __init__(self, parent, infoDict, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.infoDict = infoDict
        self.setupData()

    def setupData(self):
        """Prune the active list of data based on 'enabled' property of data Dict"""
        self.infoDict = [data for data in self.infoDict if data['enabled']]

    def rowCount(self, parent):
        return len(self.infoDict)

    def columnCount(self, parent):
        return 2
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        elif role == Qt.DisplayRole:
            label = self.infoDict[index.row()]["label"]
            value = self.infoDict[index.row()]["value"]

            if index.column() == 0:
                return label
            elif index.column() == 1:
                return value

        elif role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignRight | Qt.AlignVCenter
            elif index.column() == 1:
                return Qt.AlignLeft | Qt.AlignVCenter

        else:
            return

_popover = None
_popoverShown = False
def toggleClipInfoWindow():
    global _popover
    global _popoverShown
    if not _popoverShown:
        _popover = ClipInfoWindow()
        v = hiero.ui.activeView()
        _popover.showAt(QCursor.pos())
        _popoverShown = True
    else:
        _popover.hide()
        _popoverShown = False

action = QAction("Clip Info", None)
action.setShortcut(QKeySequence("Ctrl+Shift+0"))
action.triggered.connect(toggleClipInfoWindow)
hiero.ui.addMenuAction("Window", action)