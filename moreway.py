import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSql import *
from PyQt5.QtGui import *
import psycopg2


BARCODE = ""
DB_INST = None


def initDB():
    inst = psycopg2.connect(
        "dbname=postgres user=postgres password=123456")
    cursor = inst.cursor()
    cursor.execute("SELECT version()")
    if cursor.fetchone() is None:
        QMessageBox.critical('ERROR', 'database connected failed')
        exit()
    return inst


def doKeyPressEvent(e, handle_barcode_cb):
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


def findRow(kw, tbl, col):
    for row in range(tbl.rowCount()):
        item = tbl.item(row, col)
        if kw == item.text():
            return row
    return -1


class MWTableWidget(QTableWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def focusInEvent(self, e):
        self.parent.setFocus(True)
        return super().focusInEvent(e)


class MWSpinBox(QSpinBox):
    def __init__(self):
        super().__init__()

    def focusInEvent(self, e):
        QTimer.singleShot(0, self.selectAll)
        return super().focusInEvent(e)


class MWDoubleSpinBox(QDoubleSpinBox):
    def __init__(self):
        super().__init__()

    def focusInEvent(self, e):
        QTimer.singleShot(0, self.selectAll)
        return super().focusInEvent(e)


class SelectClassIDDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.class_id = 0
        self.cur = DB_INST.cursor()
        self.initUI()


    def hahaha(self, e):
        index = self.class_tree.selectedIndexes()
        if len(index) == 0:
            return
        item = self.m.itemFromIndex(index[0])
        if item.hasChildren():
            return
        self.class_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def initUI(self):
        self.class_tree = QTreeView(self)
        self.class_tree.clicked.connect(self.class_tree.expand)
        self.class_tree.doubleClicked.connect(self.hahaha)
        self.abc()
        confirm_btn = QPushButton('Confirm')
        cancel_btn = QPushButton('Cancel')
        confirm_btn.clicked.connect(self.hahaha)
        cancel_btn.clicked.connect(self.reject)

        hbox = QHBoxLayout()
        hbox.addWidget(confirm_btn)
        hbox.addWidget(cancel_btn)
        vbox = QVBoxLayout()
        vbox.addWidget(self.class_tree)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.resize(1920, 1080)

    def abc(self):
        self.cur.execute(
            "SELECT class0,class1,ext0,ext1,ext2,ext3,ext4,id FROM mwclass ORDER BY class0,class1,ext0,ext1,ext2,ext3,ext4")
        self.m = QStandardItemModel()
        self.m.setHorizontalHeaderLabels(['class id'])
        self.class_tree.setModel(self.m)

        haha = ['', '', '', '', '', '', '']
        root = self.m.invisibleRootItem()
        while True:
            data = self.cur.fetchone()
            if data is None:
                break
            id = data[7]
            if ''.join(haha[0:1]) != ''.join(data[0:1]):
                class0 = QStandardItem(data[0])
                class0.setEditable(False)
                root.appendRow(class0)
                haha[0] = data[0]

            if ''.join(haha[0:2]) != ''.join(data[0:2]):
                class1 = QStandardItem(data[1])
                class0.appendRow(class1)
                haha[1] = data[1]

            if len(data[2]) == 0:
                class1.setFlags(class1.flags() & ~Qt.ItemFlag.ItemIsEditable)
                class1.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(haha[0:3]) != ''.join(data[0:3]):
                ext0 = QStandardItem(data[2])
                class1.appendRow(ext0)
                haha[2] = data[2]

            if len(data[3]) == 0:
                ext0.setFlags(ext0.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext0.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(haha[0:4]) != ''.join(data[0:4]):
                ext1 = QStandardItem(data[3])
                ext0.appendRow(ext1)
                haha[3] = data[3]

            if len(data[4]) == 0:
                ext1.setFlags(ext1.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext1.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(haha[0:5]) != ''.join(data[0:5]):
                ext2 = QStandardItem(data[4])
                ext1.appendRow(ext2)
                haha[4] = data[4]

            if len(data[5]) == 0:
                ext2.setFlags(ext2.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext2.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(haha[0:6]) != ''.join(data[0:6]):
                ext3 = QStandardItem(data[5])
                ext2.appendRow(ext3)
                haha[5] = data[5]

            if len(data[6]) == 0:
                ext3.setFlags(ext3.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext3.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(haha[0:7]) != ''.join(data[0:7]):
                ext4 = QStandardItem(data[6])
                ext3.appendRow(ext4)
                haha[6] = data[6]
                ext4.setFlags(ext4.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext4.setData(id, Qt.ItemDataRole.UserRole)


class MWQLineEdit(QLineEdit):
    def __init__(self, selector):
        super().__init__()
        self.selector = selector
        self.is_ready = True

    def focusInEvent(self, e):
        if self.is_ready:
            self.selector.open()
            self.is_ready = False


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
             "Input Price", "Sale Price", "Remark", "Brand", "Op."]

    def __init__(self):
        super().__init__()
        self.db = DB_INST
        self.cur = DB_INST.cursor()
        self.initUI()
        self.installEventFilter(self)

    def eventFilter(self, obj, e):
        if obj.objectName() == 'item_class_id' and e.type() == QEvent.FocusIn:
            print('hahaha')
            return True
        return False


# class MWQLineEdit(QLineEdit):
#     def __init__(self, selector):
#         super().__init__()
#         self.selector = selector
#         self.is_ready = True

#     def focusInEvent(self, e):
#         print(9999, self.is_ready)
#         if self.is_ready:
#             self.selector.open()
#             self.is_ready = False
    def keyPressEvent(self, e):
        doKeyPressEvent(e, self.handleBarcode)
        return super().keyPressEvent(e)

    def ddd(self, code):
        item = self.focusWidget()
        if code == QDialog.DialogCode.Accepted:
            item.setText(str(self.class_selector.class_id))

        item.is_ready = True
        self.setFocus(True)

    def initUI(self):
        self.tbl = MWTableWidget(self)
        self.tbl.setColumnCount(len(self.title))
        self.tbl.setHorizontalHeaderLabels(self.title)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.class_selector = SelectClassIDDialog(self)
        self.class_selector.finished.connect(self.ddd)

        clear_btn = QPushButton('Clear')
        import_btn = QPushButton('Import')
        vbox = QVBoxLayout()
        vbox.addWidget(clear_btn)
        vbox.addStretch(1)
        vbox.addWidget(import_btn)
        clear_btn.clicked.connect(self.clearTbl)
        import_btn.clicked.connect(self.doImport)

        hbox = QHBoxLayout()
        hbox.addWidget(self.tbl)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

    def clearTbl(self):
        self.tbl.setRowCount(0)

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
                    SET num=%s,
                        saleprice=%s,
                        inputprice=%s,
                        classid=%s,
                        brand=%s,
                        remark=%s
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

    def addRow(self, data, barcode):
        print('data:', data, barcode)

        row = findRow(barcode, self.tbl, self.col_barcode)
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
        item_barcode = QTableWidgetItem(barcode)
        item_goods_name = QTableWidgetItem(goods_name)
        item_stock_num = MWSpinBox()
        # class_id_item = MWQLineEdit(self.class_selector)
        item_class_id = QLineEdit(objectName='item_class_id')
        item_class_id.installEventFilter(self)
        
        item_input_price = MWDoubleSpinBox()
        item_sale_price = MWDoubleSpinBox()
        item_remark = QLineEdit(remark)
        item_brand = QLineEdit(brand)
        btn_remove = QPushButton('Remove')

        item_sys_id.setFlags(item_sys_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_sys_id.setFlags(item_sys_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_goods_name.setFlags(
            item_goods_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_stock_num.setValue(stock_num)
        item_class_id.setText(str(class_id))
        item_class_id.setProperty('index', item_goods_name)
        item_class_id.textChanged.connect(self.updateGoodsName)
        item_input_price.setSingleStep(0.5)
        item_input_price.setValue(input_price)
        item_sale_price.setSingleStep(0.5)
        item_sale_price.setValue(sale_price)
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

    def updateGoodsName(self, class_id):
        self.cur.execute(
            "SELECT CONCAT(class0, class1, ext0, ext1, ext2, ext3, ext4) AS goodsname FROM mwclass WHERE id=%s", (class_id,))
        data = self.cur.fetchone()
        item = self.sender().property('index')
        item.setText(data[0])
        self.setFocus(True)

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
        self.setFocus(True)


class SettleWidget(QWidget):
    col_sys_id = 0
    col_barcode = 1
    col_goods_name = 2
    col_sale_price = 3
    col_num = 4
    col_price = 5
    col_op = 6
    title = ["SYSID", "Barcode", "Goods Name",
             "Sale Price", "Num", "Price", "Op."]

    def __init__(self):
        super().__init__()
        self.db = DB_INST
        self.cur = DB_INST.cursor()
        self.initUI()

    def initUI(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.tbl = MWTableWidget(self)
        self.tbl.setColumnCount(len(self.title))
        self.tbl.setHorizontalHeaderLabels(self.title)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.total_form = QFormLayout()
        self.total_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.total_form.addRow("Total Num:", QLabel(
            "0", alignment=Qt.AlignmentFlag.AlignRight))
        self.total_form.addRow("Total Price:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))

        clear_btn = QPushButton("Clear")
        settle_btn = QPushButton("Settle")
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(settle_btn)

        self.grid.addWidget(self.tbl, 0, 0, 2, 1)
        self.grid.addLayout(btn_layout, 0, 1, 1, 1)
        self.grid.addLayout(self.total_form, 1, 1, 1, 1)

        clear_btn.clicked.connect(self.clearTbl)
        settle_btn.clicked.connect(self.doSettle)

    def updateTotal(self):
        total_num = 0
        total_price = 0.00
        for i in range(self.tbl.rowCount()):
            num_item = self.tbl.cellWidget(i, self.col_num)
            sale_price_item = self.tbl.item(i, self.col_sale_price)
            price_item = self.tbl.item(i, self.col_price)

            price = num_item.value() * float(sale_price_item.text())
            price_item.setText(format(price, ".2f"))
            total_num += num_item.value()
            total_price += float(price)

        total_num_item = self.total_form.itemAt(
            0, QFormLayout.FieldRole).widget()
        total_price_item = self.total_form.itemAt(
            1, QFormLayout.FieldRole).widget()

        total_num_item.setText(str(total_num))
        total_price_item.setText(format(total_price, ".2f"))

    def keyPressEvent(self, e):
        doKeyPressEvent(e, self.handleBarcode)
        return super().keyPressEvent(e)

    def addRow(self, data, barcode):
        print('data:', data, barcode)

        row = findRow(barcode, self.tbl, self.col_barcode)
        if row != -1:
            sale_price_item = self.tbl.item(row, self.col_sale_price)
            price_item = self.tbl.item(row, self.col_price)
            num_item = self.tbl.cellWidget(row, self.col_num)

            num_item.setValue(num_item.value() + 1)
            price_item.setText(
                format(float(price_item.text()) + float(sale_price_item.text()), ".2f"))
        else:
            row = self.tbl.rowCount()
            self.tbl.setRowCount(row + 1)

            sys_id_item = QTableWidgetItem(str(data[0]))
            barcode_item = QTableWidgetItem(data[1])
            goods_name_item = QTableWidgetItem(data[2])
            sale_price_item = QTableWidgetItem(str(data[3]))
            price_item = QTableWidgetItem(sale_price_item.text())
            num_item = MWSpinBox()
            remove_btn = QPushButton('Remove')

            sys_id_item.setFlags(sys_id_item.flags() & ~
                                 Qt.ItemFlag.ItemIsEditable)
            barcode_item.setFlags(barcode_item.flags() &
                                  ~Qt.ItemFlag.ItemIsEditable)
            goods_name_item.setFlags(
                goods_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sale_price_item.setFlags(
                sale_price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setFlags(price_item.flags() & ~
                                Qt.ItemFlag.ItemIsEditable)
            num_item.setValue(1)
            num_item.valueChanged.connect(self.updateTotal)
            remove_btn.clicked.connect(self.removeRow)

            self.tbl.setItem(row, self.col_sys_id, sys_id_item)
            self.tbl.setItem(row, self.col_barcode, barcode_item)
            self.tbl.setItem(row, self.col_goods_name, goods_name_item)
            self.tbl.setItem(row, self.col_sale_price, sale_price_item)
            self.tbl.setItem(row, self.col_price, price_item)
            self.tbl.setCellWidget(row, self.col_num, num_item)
            self.tbl.setCellWidget(row, self.col_op, remove_btn)

        self.updateTotal()

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
        self.setFocus(True)

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
            stockid_item = self.tbl.item(row, self.col_sys_id)
            price_item = self.tbl.item(row, self.col_price)
            num_item = self.tbl.cellWidget(row, self.col_num)

            sql = """
                INSERT INTO mworderdetail(stockid,num,price,orderid)
                VALUES(%s,%s,%s,%s)
                """
            self.cur.execute(sql, (stockid_item.text(), num_item.value(),
                             price_item.text(), last_id))
            if self.cur.rowcount != 1:
                QMessageBox.critical(
                    self, 'ERROR', 'order detail add failed')
                exit()

            sql = "UPDATE mwstock SET num=num-%s WHERE id=%s"
            self.cur.execute(sql, (num_item.value(), stockid_item.text()))
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
        self.initUI()

    def initUI(self):
        layout = QGridLayout(self)
        self.setLayout(layout)

        settle_page = SettleWidget()
        stock_page = StockWidget()
        self.tab = QTabWidget(self)
        self.tab.addTab(settle_page, 'SETTLE')
        self.tab.addTab(stock_page, 'STOCK')

        self.tab.currentWidget().setFocus(True)

        layout.addWidget(self.tab, 0, 0, 1, 1)

        self.setWindowTitle('TEST')
        self.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    DB_INST = initDB()
    main = MainWidget()
    sys.exit(app.exec_())
