import os, sys

from PySide2.QtCore import Slot, Qt, QModelIndex
from PySide2.QtGui import QPixmap
from PySide2.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery, QSqlField, QSqlRecord, QSqlQueryModel
from PySide2.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QTableView
from ui_mainwin import Ui_MainWindow
from ui_addbookwidget import Ui_Form
from deletewin import Ui_DelForm
from areyousure import Ui_SureForm
from ui_search import Ui_SearchForm


class Detail:
    def __init__(self, id, title, podsborka, izdelie):
        self.id = id
        self.title = title
        self.podsborka = podsborka
        self.izdelie = izdelie


class MyTableModel(QSqlTableModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def flags(self, index: QModelIndex):
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def addDetail(self, details: Detail):
        rowCount = self.rowCount()
        details_record = QSqlRecord()

        id_table = QSqlField("id", str)
        id_table.setValue(details.id)
        details_record.insert(0, id_table)

        title = QSqlField("title", str)
        title.setValue(details.title)
        details_record.insert(1, title)

        podsborka = QSqlField("podsborka", str)
        podsborka.setValue(details.podsborka)
        details_record.insert(2, podsborka)

        izdelie = QSqlField("izdelie", str)
        izdelie.setValue(details.izdelie)
        details_record.insert(3, izdelie)

        self.insertRecord(rowCount, details_record)
        self.select()


class DBBuilder:
    @staticmethod
    def build(model_type='select'):
        # Дополнительный путь к SQL драйверу
        QApplication.setLibraryPaths(['./platforms', './plugins'])

        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName('db25.db3')

        if not db.open():
            print('БД не существует')
            sys.exit(-1)

        if model_type == 'query':
            return QSqlQueryModel(), db
        else:
            model = MyTableModel(None, db)

        # model = MyTableModel(None, db, model_type)

        if 'mytable' not in db.tables():
            query = QSqlQuery()
            query.exec_(
                "create table mytable(id text primary key, title text, podsborka text, izdelie text)")

        model.setTable('mytable')
        model.setEditStrategy(QSqlTableModel.OnFieldChange)

        model.select()
        model.setHeaderData(0, Qt.Horizontal, "id")
        model.setHeaderData(1, Qt.Horizontal, "title")
        model.setHeaderData(2, Qt.Horizontal, "podsborka")
        model.setHeaderData(3, Qt.Horizontal, "izdelie")

        return model


class AddWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("add detail")
        self.__gu = Ui_Form()
        self.__gu.setupUi(self)


        # self.model = model
        self.model = DBBuilder().build()

        self.__gu.pushButton.clicked.connect(self.addDetail)
        self.__row = 0

        # self.tableView = QTableView(self)
        # self.tableView.setModel(self.model)
        # self.tableView.hideColumn(0)

    @Slot()
    def addDetail(self):
        details = Detail(self.__gu.lineEdit.text(), self.__gu.lineEdit_2.text(),
                        self.__gu.lineEdit_3.text(), self.__gu.lineEdit_4.text())
        self.model.addDetail(details)
        self.__gu.lineEdit.clear()
        self.__gu.lineEdit_2.clear()
        self.__gu.lineEdit_3.clear()
        self.__gu.lineEdit_4.clear()


class SearchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__sui = Ui_SearchForm()
        self.__sui.setupUi(self)
        self.setFixedSize(650, 300)
        self.model, self.db = DBBuilder().build('query')

        self.__sui.pushButton.clicked.connect(self.search_data)
        self.__sui.pushButton_2.clicked.connect(self.search_quit)

    @Slot()
    def search_data(self):
        if self.__sui.radioButton_2.isChecked():
            self.__sui.tableView.setModel(self.model)
            text = self.__sui.lineEdit.text()
            self.model.setQuery(f"SELECT * FROM mytable WHERE title LIKE '%{text}%'", self.db)
            # print(self.model.lastError())

        else:
            self.__sui.tableView.setModel(self.model)
            text = self.__sui.lineEdit.text()
            self.model.setQuery(f"SELECT * FROM mytable WHERE id = '{text}'", self.db)

    @Slot()
    def search_quit(self):
        self.close()


class AreYouSureDel(QWidget):
    def __init__(self, row):
        super().__init__()
        self.__suid = Ui_SureForm()
        self.__suid.setupUi(self)
        self.setFixedSize(580, 150)
        self.model = DBBuilder().build()
        self.__row_del = row

        self.__suid.pushButton.clicked.connect(self.delete_row)
        self.__suid.pushButton_2.clicked.connect(self.sure_quit)

    @Slot()
    def delete_row(self):
        self.model.removeRow(self.__row_del)
        self.model.select()
        self.close()
        self.delete_widget = DeleteWidget()
        self.delete_widget.resize(400, 400)
        self.delete_widget.show()

    @Slot()
    def sure_quit(self):
        self.close()
        self.delete_widget = DeleteWidget()
        self.delete_widget.resize(400, 400)
        self.delete_widget.show()


class DeleteWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("delete detail")
        self.__uid = Ui_DelForm()
        self.__uid.setupUi(self)
        self.setFixedSize(600, 500)

        self.model = DBBuilder().build()
        self.__uid.tableView.setModel(self.model)

        self.__uid.tableView.clicked.connect(self.printIndex)
        self.__uid.pushButton.clicked.connect(self.open_sure_del)

    @Slot(QModelIndex)
    def printIndex(self, index):
        self.__row = index.row()
        return self.__row

    @Slot()
    def open_sure_del(self):
        self.sure_del_w = AreYouSureDel(self.__row)
        self.sure_del_w.show()
        self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__ui = Ui_MainWindow()
        self.__ui.setupUi(self)
        self.setFixedSize(800, 370)

        self.__ui.pushButton.clicked.connect(self.open_add)
        self.__ui.pushButton_2.clicked.connect(self.open_search)
        self.__ui.pushButton_3.clicked.connect(self.open_delete)


    @Slot()
    def open_add(self):
        self.add_widget = AddWidget()
        self.add_widget.resize(400, 400)
        self.add_widget.show()

        # self.main_widget = AddWidget()
        # main_widget = self.main_widget
        # main_widget.show()

    @Slot()
    def open_search(self):
        self.search_widget = SearchWidget()
        self.search_widget.resize(400, 400)
        self.search_widget.show()

    @Slot()
    def open_delete(self):
        self.delete_widget = DeleteWidget()
        self.delete_widget.resize(400, 400)
        self.delete_widget.show()


def main(argv):
    app = QApplication(argv)

    # label = QLabel()
    # label.setPixmap(QPixmap(':/img/img/detail_ready.png'))
    # label.show()

    main_widget = MainWindow()
    main_widget.show()

    return app.exec_()


if __name__ == "__main__":
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = './platforms'
    exit_status = main(sys.argv)
    sys.exit(exit_status)
