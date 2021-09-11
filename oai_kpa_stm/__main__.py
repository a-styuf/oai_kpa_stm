# модули GUI
from PyQt5 import QtWidgets
import sys
# стандартные модули для работы

# модули ОАИ_КПА
from .oai_kpa_stm import ClientGUIWindow

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QtWidgets.QApplication(sys.argv)
    w = ClientGUIWindow(uniq_name="oai_kpa_stm", widget='False')
    w.show()
    sys.exit(app.exec_())
