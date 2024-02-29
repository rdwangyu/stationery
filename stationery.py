import sys
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSql import *
from PyQt5.QtGui import *
import requests


BARCODE = ""
URL = 'http://127.0.0.1:8000/cli'


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


class CategorySelector(QDialog):
    def __init__(self):
        super().__init__()
        self.category_id = 0
        self.initUI()

    def initUI(self):
        self.category_tree = QTreeView()
        self.buildCategoryTree()
        self.category_tree.clicked.connect(self.onExpand)
        self.category_tree.doubleClicked.connect(self.onConfirm)

        confirm_btn = QPushButton('确认')
        cancel_btn = QPushButton('取消')
        confirm_btn.clicked.connect(self.onConfirm)
        cancel_btn.clicked.connect(self.reject)

        hbox = QHBoxLayout()
        hbox.addWidget(confirm_btn)
        hbox.addWidget(cancel_btn)
        vbox = QVBoxLayout()
        vbox.addWidget(self.category_tree)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.setWindowTitle('分类')
        self.resize(1920, 1080)

    def buildCategoryTree(self):
        self.category_tree.setHeaderHidden(True)
        self.model = QStandardItemModel()
        self.category_tree.setModel(self.model)

        temp = ['', '', '', '', '', '', '']
        root = self.model.invisibleRootItem()
        resp = requests.get(URL + '/categories')
        resp = resp.json()
        for i in range(len(resp)):
            data = resp[i]
            id = data['id']
            if ''.join(temp[0:1]) != data['class_0']:
                class_0 = QStandardItem(data['class_0'])
                class_0.setEditable(False)
                root.appendRow(class_0)
                temp[0] = data['class_0']
                temp[1:] = [''] * 6

            if ''.join(temp[0:2]) != data['class_0'] + data['class_1']:
                class_1 = QStandardItem(data['class_1'])
                class_0.appendRow(class_1)
                temp[1] = data['class_1']
                temp[2:] = [''] * 5

            if len(data['ext_0']) == 0:
                class_1.setFlags(class_1.flags() & ~Qt.ItemFlag.ItemIsEditable)
                class_1.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:3]) != data['class_0'] + data['class_1'] + data['ext_0']:
                ext_0 = QStandardItem(data['ext_0'])
                class_1.appendRow(ext_0)
                temp[2] = data['ext_0']
                temp[3:] = [''] * 4

            if len(data['ext_1']) == 0:
                ext_0.setFlags(ext_0.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext_0.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:4]) != data['class_0'] + data['class_1'] + data['ext_0'] + data['ext_1']:
                ext_1 = QStandardItem(data['ext_1'])
                ext_0.appendRow(ext_1)
                temp[3] = data['ext_1']
                temp[4:] = [''] * 3

            if len(data['ext_2']) == 0:
                ext_1.setFlags(ext_1.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext_1.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:5]) != data['class_0'] + data['class_1'] + data['ext_0'] + data['ext_1'] + data['ext_2']:
                ext_2 = QStandardItem(data['ext_2'])
                ext_1.appendRow(ext_2)
                temp[4] = data['ext_2']
                temp[5:] = [''] * 2

            if len(data['ext_3']) == 0:
                ext_2.setFlags(ext_2.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext_2.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:6]) != data['class_0'] + data['class_1'] + data['ext_0'] + data['ext_1'] + data['ext_2'] + data['ext_3']:
                ext_3 = QStandardItem(data['ext_3'])
                ext_2.appendRow(ext_3)
                temp[5] = data['ext_3']
                temp[6] = ''

            if len(data['ext_4']) == 0:
                ext_3.setFlags(ext_3.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext_3.setData(id, Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:7]) != data['class_0'] + data['class_1'] + data['ext_0'] + data['ext_1'] + data['ext_2'] + data['ext_3'] + data['ext_4']:
                ext_4 = QStandardItem(data['ext_4'])
                ext_3.appendRow(ext_4)
                temp[6] = data['ext_4']
                ext_4.setFlags(ext_4.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ext_4.setData(id, Qt.ItemDataRole.UserRole)

    def onConfirm(self, index):
        item = self.model.itemFromIndex(index)
        if item.hasChildren():
            return
        self.category_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def onExpand(self, index):
        self.category_tree.collapse(index) if self.category_tree.isExpanded(
            index) else self.category_tree.expand(index)


class StockWidget(QWidget):
    col_id = 0
    col_barcode = 1
    col_name = 2
    col_category_id = 3
    col_num = 4
    col_purchase_price = 5
    col_retail_price = 6
    col_remark = 7
    col_brand = 8
    col_op = 9

    title = ["ID", "条码", "商品名", "分类", "库存",
             "成本", "售价", "备注", "品牌", "操作"]

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def eventFilter(self, obj, e):
        if e.type() == QEvent.MouseButtonPress:
            if obj.objectName() == 'category_selector':
                self.category_selector.open()
                return True
        if e.type() == QEvent.FocusIn:
            if obj.objectName() == 'my_line_edit':
                QTimer.singleShot(0, obj.selectAll)
                return False
        return self.parent.eventFilter(obj, e)

    def initUI(self):
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(self.title))
        self.tbl.setHorizontalHeaderLabels(self.title)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.installEventFilter(self)

        self.category_selector = CategorySelector()
        self.category_selector.finished.connect(self.updateCategory)

        btn_clear = QPushButton('清理')
        btn_import = QPushButton('入库')
        vbox = QVBoxLayout()
        vbox.addWidget(btn_clear)
        vbox.addStretch(1)
        vbox.addWidget(btn_import)
        btn_clear.clicked.connect(self.onClear)
        btn_import.clicked.connect(self.onImport)

        hbox = QHBoxLayout()
        hbox.addWidget(self.tbl)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

    def addRow(self, data, barcode):
        print(data)

        row = FindRow(barcode, self.tbl, self.col_barcode)
        if row != -1:
            item = self.tbl.cellWidget(row, self.col_num)
            item.setValue(item.value() + 1)
            return

        row = self.tbl.rowCount()
        self.tbl.setRowCount(row + 1)

        id = data.get('id', 0)
        category = data.get('category', {'id': 1})
        num = data.get('num', 1)
        name = data.get('name', '')
        remark = data.get('remark', '')
        brand = data.get('brand', '')
        cost_price = data.get('cost_price', 0)
        retail_price = data.get('retail_price', 0)

        item_id = QTableWidgetItem(str(id))
        item_id.setFlags(item_id.flags() & ~
                         Qt.ItemFlag.ItemIsEditable)

        item_barcode = QTableWidgetItem(barcode)
        item_barcode.setFlags(item_barcode.flags() & ~
                              Qt.ItemFlag.ItemIsEditable)

        item_name = QLineEdit(name)

        item_num = QSpinBox(objectName='my_line_edit')
        item_num.setValue(num)
        item_num.setMaximum(10000)
        item_num.installEventFilter(self)

        item_category_id = QLineEdit(objectName='category_selector')
        item_category_id.setText(str(category['id']))
        item_category_id.setProperty('index', item_name)
        item_category_id.installEventFilter(self)

        item_cost_price = QDoubleSpinBox(objectName='my_line_edit')
        item_cost_price.setSingleStep(0.5)
        item_cost_price.setMaximum(9999.99)
        item_cost_price.setValue(float(cost_price))
        item_cost_price.installEventFilter(self)

        item_retail_price = QDoubleSpinBox(objectName='my_line_edit')
        item_retail_price.setSingleStep(0.5)
        item_retail_price.setMaximum(9999.99)
        item_retail_price.setValue(float(retail_price))
        item_retail_price.installEventFilter(self)

        item_remark = QLineEdit(remark)
        item_brand = QLineEdit(brand)

        btn_remove = QPushButton('移除')
        btn_remove.clicked.connect(self.removeRow)

        self.tbl.setItem(row, self.col_id, item_id)
        self.tbl.setItem(row, self.col_barcode, item_barcode)
        self.tbl.setCellWidget(row, self.col_name, item_name)
        self.tbl.setCellWidget(row, self.col_num, item_num)
        self.tbl.setCellWidget(row, self.col_category_id, item_category_id)
        self.tbl.setCellWidget(row, self.col_purchase_price, item_cost_price)
        self.tbl.setCellWidget(row, self.col_retail_price, item_retail_price)
        self.tbl.setCellWidget(row, self.col_remark, item_remark)
        self.tbl.setCellWidget(row, self.col_brand, item_brand)
        self.tbl.setCellWidget(row, self.col_op, btn_remove)

    def onClear(self):
        self.tbl.setRowCount(0)

    def updateCategory(self, code):
        item = self.focusWidget()
        if code == QDialog.DialogCode.Accepted:
            item.setText(str(self.category_selector.category_id))

    def onImport(self):
        if self.tbl.rowCount() == 0:
            return

        for row in range(self.tbl.rowCount()):
            id = int(self.tbl.item(row, self.col_id).text())
            barcode = self.tbl.item(row, self.col_barcode).text()
            category_id = int(self.tbl.cellWidget(
                row, self.col_category_id).text())
            num = self.tbl.cellWidget(row, self.col_num).value()
            cost_price = self.tbl.cellWidget(
                row, self.col_purchase_price).value()
            retail_price = self.tbl.cellWidget(
                row, self.col_retail_price).value()
            name = self.tbl.cellWidget(row, self.col_name).text()
            remark = self.tbl.cellWidget(row, self.col_remark).text()
            brand = self.tbl.cellWidget(row, self.col_brand).text()

            data = {
                'name': name,
                'category_id': category_id,
                'num': num,
                'cost_price': cost_price,
                'retail_price': retail_price,
                'brand': brand,
                'remark': remark
            }
            url = URL + '/goods/' + barcode
            req_fn = requests.post if id == 0 else requests.put
            resp = req_fn(url, data=data)
            if resp.status_code != 200:
                QMessageBox.critical(self, '严重', '入库失败')
                return

        self.onClear()

    def handleBarcode(self, barcode):
        if barcode == "":
            QMessageBox.warning(self, '警告', '未识别到条码')
            return

        resp = requests.get(URL + "/goods/" + barcode)
        if resp.status_code != 200:
            QMessageBox.critical(self, '严重', '服务器异常')
            return
        self.addRow(resp.json(), barcode)

    def removeRow(self):
        btn = self.sender()
        if btn:
            row = self.tbl.indexAt(btn.pos()).row()
            self.tbl.removeRow(row)


class SettleWidget(QWidget):
    col_id = 0
    col_barcode = 1
    col_name = 2
    col_retail_price = 3
    col_num = 4
    col_price = 5
    col_op = 6
    title = ["ID", "条码", "商品名",
             "零售价", "数量", "金额", "操作"]

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
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
        self.total_form.addRow("总数量:", QLabel(
            "0", alignment=Qt.AlignmentFlag.AlignRight))
        self.total_form.addRow("总价格:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))
        btn_clear = QPushButton("清空")
        btn_settle = QPushButton("结算")
        btn_clear.clicked.connect(self.onClear)
        btn_settle.clicked.connect(self.onSettle)
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
        print(data)

        row = FindRow(barcode, self.tbl, self.col_barcode)
        if row != -1:
            item_retail_price = self.tbl.item(row, self.col_retail_price)
            item_price = self.tbl.item(row, self.col_price)
            item_num = self.tbl.cellWidget(row, self.col_num)

            item_num.setValue(item_num.value() + 1)
            item_price.setText(
                format(float(item_price.text()) + float(item_retail_price.text()), ".2f"))
        else:
            row = self.tbl.rowCount()
            self.tbl.setRowCount(row + 1)
            item_id = QTableWidgetItem(str(data['id']))
            item_id.setFlags(item_id.flags() & ~
                             Qt.ItemFlag.ItemIsEditable)

            item_barcode = QTableWidgetItem(data['barcode'])
            item_barcode.setFlags(item_barcode.flags() &
                                  ~Qt.ItemFlag.ItemIsEditable)

            item_name = QTableWidgetItem(data['name'])
            item_name.setFlags(
                item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_retail_price = QTableWidgetItem(str(data['retail_price']))
            item_retail_price.setFlags(
                item_retail_price.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_price = QTableWidgetItem(item_retail_price.text())
            item_price.setFlags(item_price.flags() & ~
                                Qt.ItemFlag.ItemIsEditable)

            item_num = QSpinBox()
            item_num.setValue(1)
            item_num.valueChanged.connect(self.updateTotal)

            btn_remove = QPushButton('Remove')
            btn_remove.clicked.connect(self.removeRow)

            self.tbl.setItem(row, self.col_id, item_id)
            self.tbl.setItem(row, self.col_barcode, item_barcode)
            self.tbl.setItem(row, self.col_name, item_name)
            self.tbl.setItem(row, self.col_retail_price, item_retail_price)
            self.tbl.setItem(row, self.col_price, item_price)
            self.tbl.setCellWidget(row, self.col_num, item_num)
            self.tbl.setCellWidget(row, self.col_op, btn_remove)

        self.updateTotal()

    def updateTotal(self):
        total_num = 0
        total_price = 0.00
        for i in range(self.tbl.rowCount()):
            item_num = self.tbl.cellWidget(i, self.col_num)
            item_sale_price = self.tbl.item(i, self.col_retail_price)
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
            QMessageBox.warning(self, '警告', '未识别到条码')
            return

        resp = requests.get(URL + "/goods/" + barcode)
        if resp.status_code != 200:
            QMessageBox.critical(self, '严重', '服务器异常')
            return
        resp = resp.json()
        if resp.get('errmsg'):
            QMessageBox.warning(self, '警告', resp.get('errmsg'))
            return
        self.addRow(resp, barcode)

    def removeRow(self):
        btn = self.sender()
        if btn:
            row = self.tbl.indexAt(btn.pos()).row()
            self.tbl.removeRow(row)
        self.updateTotal()

    def onSettle(self):
        if self.tbl.rowCount() == 0:
            return

        post_data = []
        for row in range(self.tbl.rowCount()):
            item_id = self.tbl.item(row, self.col_id)
            item_retail_price = self.tbl.item(row, self.col_retail_price)
            item_num = self.tbl.cellWidget(row, self.col_num)

            post_data.append({
                'id': item_id.text(),
                'num': item_num.value(),
                'retail_price': item_retail_price.text()
            })
        resp = requests.post(URL + "/settle", json=post_data)
        if resp.status_code != 200:
            QMessageBox.critical(self, '严重', '结算后台异常')
            return
        self.onClear()

    def onClear(self):
        self.tbl.setRowCount(0)
        self.updateTotal()


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.installEventFilter(self)
        self.initUI()

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:
            if not isinstance(obj, (QSpinBox, QDoubleSpinBox)):
                DoKeyPressEvent(e, self.tab.currentWidget().handleBarcode)
                return True
            else:
                if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
                    obj.clearFocus()
                    return True
        return False

    def initUI(self):
        settle_page = SettleWidget(self)
        stock_page = StockWidget(self)
        settle_page.installEventFilter(self)
        stock_page.installEventFilter(self)

        self.tab = QTabWidget()
        self.tab.setStyleSheet("QTabBar::tab { height: 50px; width: 300px; }")
        self.tab.addTab(settle_page, '结算')
        self.tab.addTab(stock_page, '库存')

        layout = QGridLayout()
        layout.addWidget(self.tab, 0, 0, 1, 1)
        self.setLayout(layout)

        self.setWindowTitle('收银系统 - 墨为文体用品店 V2.0')
        self.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = MainWidget()
    sys.exit(app.exec_())
