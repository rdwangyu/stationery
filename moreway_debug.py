import sys
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSql import *
from PyQt5.QtGui import *
import psycopg2


BARCODE = ""
DB_INST = None


def InitDB():
    inst = psycopg2.connect(
        "dbname=postgres user=postgres password=123456")
    cursor = inst.cursor()
    cursor.execute("SELECT version()")
    if cursor.fetchone() is None:
        QMessageBox.critical('ERROR', 'database connected failed')
        exit()
    return inst


def DoKeyPressEvent(e, handle_barcode_cb):
    global BARCODE

    keycode = e.key()
    if keycode == Qt.Key_Enter or keycode == Qt.Key_Return:
        print("barcode:", BARCODE)
        handle_barcode_cb(BARCODE)
        BARCODE = ""
    elif keycode not in [*range(48, 58), *range(65, 91), *range(97, 123)]:
        print('out of range:', keycode)
        BARCODE = ""
    else:
        BARCODE += chr(keycode)


def FindRow(kw, tbl, col):
    for row in range(tbl.rowCount()):
        item = tbl.item(row, col)
        if kw == item.text():
            return row
    return -1


class ClassSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.cur = DB_INST.cursor()
        self.class_id_selected = 0
        self.initUI()

    def initUI(self):
        self.class_tree = QTreeView()
        self.buildClassTree()
        self.class_tree.clicked.connect(self.class_tree.expand)
        self.class_tree.doubleClicked.connect(self.doConfirm)

        confirm_btn = QPushButton('Confirm')
        cancel_btn = QPushButton('Cancel')
        confirm_btn.clicked.connect(self.doConfirm)
        cancel_btn.clicked.connect(self.reject)

        hbox = QHBoxLayout()
        hbox.addWidget(confirm_btn)
        hbox.addWidget(cancel_btn)
        vbox = QVBoxLayout()
        vbox.addWidget(self.class_tree)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.resize(1920, 1080)

    def buildClassTree(self):
        self.cur.execute(
            "SELECT class0,class1,ext0,ext1,ext2,ext3,ext4,id FROM mwclass ORDER BY class0,class1,ext0,ext1,ext2,ext3,ext4")
        self.model = QStandardItemModel()
        self.class_tree.setModel(self.model)

        temp = ['', '', '', '', '', '', '']
        root = self.model.invisibleRootItem()
        while True:
            data = self.cur.fetchone()
            if data is None:
                break
            id = data[7]
            if ''.join(temp[0:1]) != ''.join(data[0:1]):
                class0 = QStandardItem(data[0])
                class0.setEditable(False)
                root.appendRow(class0)
                temp[0] = data[0]

            if ''.join(temp[0:2]) != ''.join(data[0:2]):
                class1 = QStandardItem(data[1])
                class0.appendRow(class1)
                temp[1] = data[1]

            if len(data[2]) == 0:
                class1.setFlags(class1.flags() & ~Qt.ItemFlag.ItemIsEditable)
                class1.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:3]) != ''.join(data[0:3]):
                ext0 = QStandardItem(data[2])
                class1.appendRow(ext0)
                temp[2] = data[2]

            if len(data[3]) == 0:
                ext0.setFlags(ext0.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext0.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:4]) != ''.join(data[0:4]):
                ext1 = QStandardItem(data[3])
                ext0.appendRow(ext1)
                temp[3] = data[3]

            if len(data[4]) == 0:
                ext1.setFlags(ext1.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext1.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:5]) != ''.join(data[0:5]):
                ext2 = QStandardItem(data[4])
                ext1.appendRow(ext2)
                temp[4] = data[4]

            if len(data[5]) == 0:
                ext2.setFlags(ext2.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext2.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:6]) != ''.join(data[0:6]):
                ext3 = QStandardItem(data[5])
                ext2.appendRow(ext3)
                temp[5] = data[5]

            if len(data[6]) == 0:
                ext3.setFlags(ext3.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext3.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:7]) != ''.join(data[0:7]):
                ext4 = QStandardItem(data[6])
                ext3.appendRow(ext4)
                temp[6] = data[6]
                ext4.setFlags(ext4.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext4.setData(id, Qt.ItemDataRole.UserRole)

    def doConfirm(self, e):
        index = self.class_tree.selectedIndexes()
        if len(index) == 0:
            return
        item = self.model.itemFromIndex(index[0])
        if item.hasChildren():
            return
        self.class_id_selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


class StockWidget(QWidget):
    col_sys_id = 0
    col_barcode = 1
    col_goods_name = 2
    col_class_id = 3
    col_stock_num = 4
    col_input_price = 5
    col_sale_price = 6
    col_remark = 7
    col_brand = 8
    col_op = 9

    title = ["SYSID", "Barcode", "Goods Name", "Class ID", "Stock Num",
             "Input Price", "Sale Price", "Remark", "Brand", "..."]

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.db = DB_INST
        self.cur = DB_INST.cursor()
        self.initUI()

    def eventFilter(self, obj, e):
        if e.type() == QEvent.MouseButtonPress:
            if obj.objectName() == 'lineedit_popup_dialog':
                self.class_selector.open()
                return True
        if e.type() == QEvent.FocusIn:
            if obj.objectName() == 'spinbox_selectall':
                obj.selectAll()
                return True
        return self.parent.eventFilter(obj, e)

    def initUI(self):
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(self.title))
        self.tbl.setHorizontalHeaderLabels(self.title)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.installEventFilter(self)

        self.class_selector = ClassSelector()
        self.class_selector.finished.connect(self.updateClass)

        btn_clear = QPushButton('Clear')
        btn_import = QPushButton('Import')
        vbox = QVBoxLayout()
        vbox.addWidget(btn_clear)
        vbox.addStretch(1)
        vbox.addWidget(btn_import)
        btn_clear.clicked.connect(self.clearTbl)
        btn_import.clicked.connect(self.doImport)

        hbox = QHBoxLayout()
        hbox.addWidget(self.tbl)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

    def addRow(self, data, barcode):
        print('data:', data, barcode)

        row = FindRow(barcode, self.tbl, self.col_barcode)
        if row != -1:
            item = self.tbl.cellWidget(row, self.col_stock_num)
            item.setValue(item.value() + 1)
            return

        row = self.tbl.rowCount()
        self.tbl.setRowCount(row + 1)

        stock_id = 0
        class_id = 0
        stock_num = 1
        goods_name = ''
        remark = ''
        brand = ''
        input_price = 0.00
        sale_price = 0.00
        if data:
            stock_id, barcode, goods_name, class_id, stock_num, input_price, sale_price, remark, brand = data

        item_sys_id = QTableWidgetItem(str(stock_id))
        item_sys_id.setFlags(item_sys_id.flags() & ~Qt.ItemFlag.ItemIsEditable)

        item_barcode = QTableWidgetItem(barcode)
        item_barcode.setFlags(item_barcode.flags() & ~
                              Qt.ItemFlag.ItemIsEditable)

        item_goods_name = QTableWidgetItem(goods_name)
        item_goods_name.setFlags(
            item_goods_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

        item_stock_num = QSpinBox(objectName='spinbox_selectall')
        item_stock_num.setValue(stock_num)

        item_class_id = QLineEdit(objectName='lineedit_popup_dialog')
        item_class_id.setReadOnly(True)
        item_class_id.setText(str(class_id))
        item_class_id.setProperty('index', item_goods_name)
        item_class_id.textChanged.connect(self.updateGoodsName)
        item_class_id.installEventFilter(self)

        item_input_price = QDoubleSpinBox(objectName='spinbox_selectall')
        item_input_price.setSingleStep(0.5)
        item_input_price.setValue(input_price)

        item_sale_price = QDoubleSpinBox(objectName='spinbox_selectall')
        item_sale_price.setSingleStep(0.5)
        item_sale_price.setValue(sale_price)

        item_remark = QLineEdit(remark)
        item_brand = QLineEdit(brand)

        btn_remove = QPushButton('Remove')
        btn_remove.clicked.connect(self.removeRow)

        self.tbl.setItem(row, self.col_sys_id, item_sys_id)
        self.tbl.setItem(row, self.col_barcode, item_barcode)
        self.tbl.setItem(row, self.col_goods_name, item_goods_name)
        self.tbl.setCellWidget(row, self.col_stock_num, item_stock_num)
        self.tbl.setCellWidget(row, self.col_class_id, item_class_id)
        self.tbl.setCellWidget(row, self.col_input_price, item_input_price)
        self.tbl.setCellWidget(row, self.col_sale_price, item_sale_price)
        self.tbl.setCellWidget(row, self.col_remark, item_remark)
        self.tbl.setCellWidget(row, self.col_brand, item_brand)
        self.tbl.setCellWidget(row, self.col_op, btn_remove)

    def clearTbl(self):
        self.tbl.setRowCount(0)

    def updateClass(self, code):
        item = self.focusWidget()
        if code == QDialog.DialogCode.Accepted:
            item.setText(str(self.class_selector.class_id_selected))

    def doImport(self):
        if self.tbl.rowCount() == 0:
            return

        for row in range(self.tbl.rowCount()):
            stock_id = int(self.tbl.item(row, self.col_sys_id).text())
            barcode = self.tbl.item(row, self.col_barcode).text()
            class_id = int(self.tbl.cellWidget(row, self.col_class_id).text())
            stock_num = self.tbl.cellWidget(row, self.col_stock_num).value()
            input_price = self.tbl.cellWidget(
                row, self.col_input_price).value()
            sale_price = self.tbl.cellWidget(row, self.col_sale_price).value()
            remark = self.tbl.cellWidget(row, self.col_remark).text()
            brand = self.tbl.cellWidget(row, self.col_brand).text()

            if stock_id == 0:
                sql = """
                    INSERT INTO mwstock(barcode,num,saleprice,inputprice,classid,brand,remark)
                    VALUES(%s,%s,%s,%s,%s,%s,%s)
                    """
                self.cur.execute(
                    sql, (barcode, stock_num, sale_price, input_price, class_id, brand, remark))
            else:
                sql = """
                    UPDATE mwstock
                    SET num=%s, saleprice=%s, inputprice=%s, classid=%s, brand=%s, remark=%s
                    WHERE id=%s
                    """
                self.cur.execute(
                    sql, (stock_num, sale_price, input_price, class_id, brand, remark, stock_id))

            print(row, self.cur.query)
            if self.cur.rowcount != 1:
                QMessageBox.critical(self, 'ERROR', 'stock import failed')
                exit()

        self.db.commit()
        self.clearTbl()
        QMessageBox.information(self, 'WELL', 'OK!')

    def updateGoodsName(self, class_id):
        self.cur.execute(
            "SELECT CONCAT(class0, class1, ext0, ext1, ext2, ext3, ext4) AS goodsname FROM mwclass WHERE id=%s", (class_id,))
        data = self.cur.fetchone()
        item = self.sender().property('index')
        item.setText(data[0])

    def handleBarcode(self, barcode):
        if barcode == "":
            QMessageBox.warning(self, 'WARNING', 'barcode null')
            return

        sql = """

            SELECT  s.id,
                    s.barcode,
                    CONCAT(c.class0, c.class1, c.ext0, c.ext1, c.ext2, c.ext3, c.ext4) AS goodsname,
                    s.classid,
                    s.num,
                    CAST(s.inputprice AS DECIMAL(5, 2)),
                    CAST(s.saleprice AS DECIMAL(5, 2)),
                    s.remark,
                    s.brand
            FROM mwstock AS s
            LEFT JOIN mwclass AS c ON s.classid = c.id
            WHERE barcode='{}'

            """.format(barcode)
        self.cur.execute(sql)
        data = self.cur.fetchone()
        self.addRow(data, barcode)

    def removeRow(self):
        btn = self.sender()
        if btn:
            row = self.tbl.indexAt(btn.pos()).row()
            self.tbl.removeRow(row)


class SettleWidget(QWidget):
    col_sys_id = 0
    col_barcode = 1
    col_goods_name = 2
    col_sale_price = 3
    col_num = 4
    col_price = 5
    col_op = 6
    title = ["SYSID", "Barcode", "Goods Name",
             "Sale Price", "Num", "Price", "..."]

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.db = DB_INST
        self.cur = DB_INST.cursor()
        self.initUI()

    def eventFilter(self, obj, e):
        return self.parent.eventFilter(obj, e)

    def initUI(self):
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(self.title))
        self.tbl.setHorizontalHeaderLabels(self.title)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.installEventFilter(self)

        self.total_form = QFormLayout()
        self.total_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.total_form.addRow("Total Num:", QLabel(
            "0", alignment=Qt.AlignmentFlag.AlignRight))
        self.total_form.addRow("Total Price:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))
        btn_clear = QPushButton("Clear")
        btn_settle = QPushButton("Settle")
        btn_clear.clicked.connect(self.clearTbl)
        btn_settle.clicked.connect(self.doSettle)
        vbox = QVBoxLayout()
        vbox.addWidget(btn_clear)
        vbox.addStretch(1)
        vbox.addWidget(btn_settle)
        layout_grid = QGridLayout()
        layout_grid.addWidget(self.tbl, 0, 0, 2, 1)
        layout_grid.addLayout(vbox, 0, 1, 1, 1)
        layout_grid.addLayout(self.total_form, 1, 1, 1, 1)
        self.setLayout(layout_grid)

    def addRow(self, data, barcode):
        print('data:', data, barcode)

        row = FindRow(barcode, self.tbl, self.col_barcode)
        if row != -1:
            item_sale_price = self.tbl.item(row, self.col_sale_price)
            item_price = self.tbl.item(row, self.col_price)
            item_num = self.tbl.cellWidget(row, self.col_num)

            item_num.setValue(item_num.value() + 1)
            item_price.setText(
                format(float(item_price.text()) + float(item_sale_price.text()), ".2f"))
        else:
            row = self.tbl.rowCount()
            self.tbl.setRowCount(row + 1)

            item_sys_id = QTableWidgetItem(str(data[0]))
            item_sys_id.setFlags(item_sys_id.flags() & ~
                                 Qt.ItemFlag.ItemIsEditable)

            item_barcode = QTableWidgetItem(data[1])
            item_barcode.setFlags(item_barcode.flags() &
                                  ~Qt.ItemFlag.ItemIsEditable)

            item_goods_name = QTableWidgetItem(data[2])
            item_goods_name.setFlags(
                item_goods_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_sale_price = QTableWidgetItem(str(data[3]))
            item_sale_price.setFlags(
                item_sale_price.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_price = QTableWidgetItem(item_sale_price.text())
            item_price.setFlags(item_price.flags() & ~
                                Qt.ItemFlag.ItemIsEditable)

            item_num = QSpinBox()
            item_num.setValue(1)
            item_num.valueChanged.connect(self.updateTotal)

            btn_remove = QPushButton('Remove')
            btn_remove.clicked.connect(self.removeRow)

            self.tbl.setItem(row, self.col_sys_id, item_sys_id)
            self.tbl.setItem(row, self.col_barcode, item_barcode)
            self.tbl.setItem(row, self.col_goods_name, item_goods_name)
            self.tbl.setItem(row, self.col_sale_price, item_sale_price)
            self.tbl.setItem(row, self.col_price, item_price)
            self.tbl.setCellWidget(row, self.col_num, item_num)
            self.tbl.setCellWidget(row, self.col_op, btn_remove)

        self.updateTotal()

    def updateTotal(self):
        total_num = 0
        total_price = 0.00
        for i in range(self.tbl.rowCount()):
            item_num = self.tbl.cellWidget(i, self.col_num)
            item_sale_price = self.tbl.item(i, self.col_sale_price)
            item_price = self.tbl.item(i, self.col_price)

            price = item_num.value() * float(item_sale_price.text())
            item_price.setText(format(price, ".2f"))
            total_num += item_num.value()
            total_price += float(price)

        total_num_item = self.total_form.itemAt(
            0, QFormLayout.FieldRole).widget()
        total_price_item = self.total_form.itemAt(
            1, QFormLayout.FieldRole).widget()

        total_num_item.setText(str(total_num))
        total_price_item.setText(format(total_price, ".2f"))

    def handleBarcode(self, barcode):
        if barcode == "":
            QMessageBox.warning(self, 'WARNING', 'barcode null')
            return

        sql = '''
            
            SELECT  s.id,
                    s.barcode,
                    CONCAT(c.class0, c.class1, c.ext0, c.ext1, c.ext2, c.ext3, c.ext4) AS goodsname,
                    CAST(s.saleprice AS DECIMAL(5, 2))
            FROM mwstock AS s
            LEFT JOIN mwclass AS c ON s.classid = c.id
            WHERE barcode='{}'
            
            '''.format(barcode)
        self.cur.execute(sql)
        data = self.cur.fetchone()
        if data:
            self.addRow(data, barcode)
        else:
            QMessageBox.warning(self, 'WARNING', "barcode not found")

    def removeRow(self):
        btn = self.sender()
        if btn:
            row = self.tbl.indexAt(btn.pos()).row()
            self.tbl.removeRow(row)
        self.updateTotal()

    def doSettle(self):
        if self.tbl.rowCount() == 0:
            return

        total_num_item = self.total_form.itemAt(
            0, QFormLayout.FieldRole).widget()
        total_price_item = self.total_form.itemAt(
            1, QFormLayout.FieldRole).widget()
        deduction = 0
        payment = total_price_item.text()

        sql = """
            
            INSERT INTO mwordersummary(num,price,deduction,payment)
            VALUES(%s,%s,%s,%s)
            RETURNING id

            """
        self.cur.execute(sql, (total_num_item.text(),
                         total_price_item.text(), deduction, payment))
        if self.cur.rowcount != 1:
            QMessageBox.critical(self, 'ERROR', 'order add failed')
            exit()
        last_id = self.cur.fetchone()[0]

        for row in range(self.tbl.rowCount()):
            item_stock_id = self.tbl.item(row, self.col_sys_id)
            item_price = self.tbl.item(row, self.col_price)
            item_num = self.tbl.cellWidget(row, self.col_num)

            sql = """
                INSERT INTO mworderdetail(stockid,num,price,orderid)
                VALUES(%s,%s,%s,%s)
                """
            self.cur.execute(sql, (item_stock_id.text(), item_num.value(),
                             item_price.text(), last_id))
            if self.cur.rowcount != 1:
                QMessageBox.critical(
                    self, 'ERROR', 'order detail add failed')
                exit()

            sql = "UPDATE mwstock SET num=num-%s WHERE id=%s"
            self.cur.execute(sql, (item_num.value(), item_stock_id.text()))
            if self.cur.rowcount != 1:
                QMessageBox.critical(self, 'ERROR', 'stock update failed')
                exit()

        self.db.commit()
        self.clearTbl()
        QMessageBox.information(self, 'WELL', 'OK!')

    def clearTbl(self):
        self.tbl.setRowCount(0)
        self.updateTotal()


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.installEventFilter(self)
        self.initUI()

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:
            DoKeyPressEvent(e, self.tab.currentWidget().handleBarcode)
            return True
        return False

    def initUI(self):
        self.tab = QTabWidget()
        settle_page = SettleWidget(self)
        stock_page = StockWidget(self)
        settle_page.installEventFilter(self)
        stock_page.installEventFilter(self)
        self.tab.addTab(settle_page, 'SETTLE')
        self.tab.addTab(stock_page, 'STOCK')

        layout = QGridLayout()
        layout.addWidget(self.tab, 0, 0, 1, 1)
        self.setLayout(layout)

        self.setWindowTitle('TEST')
        self.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    DB_INST = InitDB()
    main = MainWidget()
    sys.exit(app.exec_())
