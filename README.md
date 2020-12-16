﻿# Пример виджета для модуля ОАИ КПА (oai_kpa_stm) 
_______
Данынй виджет служит двум целям: 
-либо использование отдельно в качестве инженерного окна для отлатки и работы с модулем.
-либо в составе большей программы как инженерное окно 

# Материал для предворительного ознакомления
Перед началосм работы с данным примером необходимо ознакомиться со следующими материалами:
- простой туториал по началу работы с pyQt - [тут](https://pythonworld.ru/gui/pyqt5-firstprograms.html)
- использование QtDesigner через наследование класса виджета/окна (важно, используется именно такой подход) - [тут](https://tproger.ru/translations/python-gui-pyqt/)
- [тут](https://cucumbler.ru/blog/articles/nastrojka-pycharm-dlja-raboty-s-bibliotekoj-pyqt5.html) и [тут](https://pythonpyqt.com/how-to-install-pyqt5-in-pycharm/) описан подход использования QtDesigner из под pyCharm
При разработке ~~можно~~ **нужно** обращаться к следующим ресурсам
- длинный [туториал](https://python-scripts.com/pyqt5) по pyQt
- полное [описание](https://doc.qt.io/qt-5/index.html) всех классов Qt5 но все примеры на c++
- [вики](https://wiki.python.org/moin/PyQt/Tutorials) по pyQt
- любой другой ресурс, который вам понравится

# Что такое [Qt](https://ru.wikipedia.org/wiki/Qt)
Rроссплатформенный IDE для разработки программного обеспечения на языке программирования C++. 
Есть также «привязки» ко многим другим языкам программирования: 
-Python — PyQt, PySide;
-Ruby — QtRuby;
-Java — Qt Jambi;
-PHP — PHP-Qt и другие.
Хорошо развит, широко поддерживается, имеет кучу обучающих материалов и примеров. Замечательно документирован. Кроссплатформенный, бесплатный (лицензия GPL3).

# Что такое [pyQt](https://ru.wikipedia.org/wiki/PyQt)
набор расширений (биндингов) графического фреймворка Qt для языка программирования Python, выполненный в виде расширения Python.

# Почему pyQt
pyQt реализует практически весь функционал Qt (т.е. обладает всеми его приимуществами). Имеет встроенное средство создания окон ([QtDesigner](https://ru.wikipedia.org/wiki/Qt_Designer)), что особенно важно при быстром создании инженерных окон.
Не имеет собственно средства рисования графиков, но легко поддерживает [matplotlib](https://pythonspot.com/pyqt5-matplotlib/) (прошлый выбора автора, не очень подходит для онлайн отрисовки) и [pyqtgraph](http://www.pyqtgraph.org/) (выбор автора, отлично подходит для онлайн отрисовки).

# Рекомендумая структура проекта (на примере платы ОАИ КПА СТМ)
* oai_kpa_stm (моудль с виджетом)
	* oai_kpa_stm_data (модуль, обеспечивающий надстройку над регистрами, позволяющий рабоать с платой ничего не зная о нижнем уровне общения)
		* oai_modbus/OAI_Modbus ([модуль](https://github.com/CrinitusFeles/OAI_Modbus), организующий доступ к записи/чтению регистров платы через протокол модбас)
		* oai_kpa_stm_widget_qt (модуль, автоматически сгенеренный из файла, созданного в QtDesigner)

# Naming convention (TBD)
1. Основной модуль - виджет:
    oai_kpa_**xxx** - где xxx сокращение от имени платы или назначения (oai_kpa_stm для модуля сигнальной телеметрии СТМ)
    Существующие сокращения: 
    -mku - матричные команд управления, МКУ
    -power - плата питания
    -mko - MKO
    -etc
2. Модуль обработки данных (TBD):
    oai_kpa_xxx_**data**
3. Модуль для QtDesigner 
    oai_kpa_xxx_**yyy_qt**:
      - yyy - назначение модуля: widget, window, etc (oai_kpa_stm_widget_qt для данного примера)
      - _qt - обозначение источника файла - не написанный руками, а сгенеренный QtDesigner

# Предподготовка
_Обязательно_
1. Pycharm Community Edition (Последняя версия)
2. Python 3.7 или 3.8 (Рекомендуется)
3. pyserial, puQt5, pyqtgraph, matplotlib
_Работа с примером_
4. Скачайте архив с библиотекой или клонируйте репозиторий к себе на локальный диск:
```
git clone https://github.com/a-styuf/oai_kpa_stm
```
5. Переименуйте все необходимые файлы.

# Обязательный функционал
1. Блок подключения (виден толькоо при работе в режиме отдельного окна, иначе подключается через общую программу):
    - кнопка подключения
    - строка ввода serial number
    - строка вывода состояния
2. Параметр уникального имени в объекте: нужно для корректного хранения настроек и логов.
3. Сохранение параметров (например серийного номера) в файл с настройками.
4. Не блокирующая работа: ни одна из функций не должна быть блокирующая. В случае необходимости использования подобных функций используются потоки. Функции по работе с общими данными для потоков защищаются замками.
    - [пример 1](https://habr.com/ru/post/149420/)
    - [пример 2](https://python-scripts.com/threading)
5. Вывод актуального состояния в строку состояния.

------
#Контакты руководителя проекта: __a-styuf@yandex.ru__  



[]: https://pythonworld.ru/gui/pyqt5-firstprograms.html