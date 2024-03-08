import sys
from PyQt5.QtCore import QEvent
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSql import *
from PyQt5.QtGui import *
import requests
from datetime import datetime
import xlrd
import math

Barcode = ""
BaseUrl = 'https://moreway.shop'
# BaseUrl = 'http://127.0.0.1:8000'
Beep = None
Resolution = QSize(1920, 1080)


def RequestData(url, method='GET', data=None, err_msg='服务器异常'):
    print('request...')
    start_time = datetime.now()
    resp = requests.request(url=url, json=data, method=method)
    end_time = datetime.now()
    duration = end_time - start_time
    print('request...', url, method, duration, data)
    if resp.status_code != 200:
        QMessageBox.critical(None, '严重', err_msg)
        return None, False
    return resp, True


def DoKeyPressEvent(e, handle_barcode_cb):
    global Barcode

    keycode = e.key()
    if keycode == Qt.Key_Enter or keycode == Qt.Key_Return:
        print("barcode:", Barcode)
        handle_barcode_cb(Barcode)
        Barcode = ""
    elif keycode not in [*range(48, 58), *range(65, 91), *range(97, 123)]:
        print('out of range:', keycode)
        Barcode = ""
    else:
        Barcode += chr(keycode)


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
        self.category_name = ''
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
        self.setFixedSize(Resolution / 2)

    def buildCategoryTree(self):
        self.category_tree.setHeaderHidden(True)
        self.model = QStandardItemModel()
        self.category_tree.setModel(self.model)

        temp = ['', '', '', '', '', '', '']
        root = self.model.invisibleRootItem()

        resp, success = RequestData(BaseUrl + '/cli/categories')
        if not success:
            return
        data = resp.json()
        self.category_id = data[0]['id']
        for i in range(len(data)):
            item = data[i]
            id = item['id']
            if ''.join(temp[0:1]) != item['class_0']:
                class_0 = QStandardItem(item['class_0'])
                class_0.setEditable(False)
                root.appendRow(class_0)
                temp[0] = item['class_0']
                temp[1:] = [''] * 6

            if ''.join(temp[0:2]) != item['class_0'] + item['class_1']:
                class_1 = QStandardItem(item['class_1'])
                class_1.setEditable(False)
                class_0.appendRow(class_1)
                temp[1] = item['class_1']
                temp[2:] = [''] * 5

            if len(item['ext_0']) == 0:
                class_1.setData((id, '-'.join(temp)), Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:3]) != item['class_0'] + item['class_1'] + item['ext_0']:
                ext_0 = QStandardItem(item['ext_0'])
                ext_0.setEditable(False)
                class_1.appendRow(ext_0)
                temp[2] = item['ext_0']
                temp[3:] = [''] * 4

            if len(item['ext_1']) == 0:
                ext_0.setData((id, '-'.join(temp)), Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:4]) != item['class_0'] + item['class_1'] + item['ext_0'] + item['ext_1']:
                ext_1 = QStandardItem(item['ext_1'])
                ext_1.setEditable(False)
                ext_0.appendRow(ext_1)
                temp[3] = item['ext_1']
                temp[4:] = [''] * 3

            if len(item['ext_2']) == 0:
                ext_1.setData((id, '-'.join(temp)), Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:5]) != item['class_0'] + item['class_1'] + item['ext_0'] + item['ext_1'] + item['ext_2']:
                ext_2 = QStandardItem(item['ext_2'])
                ext_2.setEditable(False)
                ext_1.appendRow(ext_2)
                temp[4] = item['ext_2']
                temp[5:] = [''] * 2

            if len(item['ext_3']) == 0:
                ext_2.setData((id, '-'.join(temp)), Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:6]) != item['class_0'] + item['class_1'] + item['ext_0'] + item['ext_1'] + item['ext_2'] + item['ext_3']:
                ext_3 = QStandardItem(item['ext_3'])
                ext_3.setEditable(False)
                ext_2.appendRow(ext_3)
                temp[5] = item['ext_3']
                temp[6] = ''

            if len(item['ext_4']) == 0:
                ext_3.setData((id, '-'.join(temp)), Qt.ItemDataRole.UserRole)
                continue
            if ''.join(temp[0:7]) != item['class_0'] + item['class_1'] + item['ext_0'] + item['ext_1'] + item['ext_2'] + item['ext_3'] + item['ext_4']:
                ext_4 = QStandardItem(item['ext_4'])
                ext_4.setEditable(False)
                ext_3.appendRow(ext_4)
                temp[6] = item['ext_4']
                ext_4.setData((id, '-'.join(temp)), Qt.ItemDataRole.UserRole)

    def onConfirm(self, checked):
        index = self.category_tree.selectedIndexes()
        if len(index) == 0:
            return
        item = self.model.itemFromIndex(index[0])
        if item.hasChildren():
            return
        self.category_id = item.data(Qt.ItemDataRole.UserRole)[0]
        self.category_name = item.data(Qt.ItemDataRole.UserRole)[1]
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
    col_add_num = 5
    col_cost_price = 6
    col_retail_price = 7
    col_thumbnail = 8
    col_poster = 9
    col_remark = 10
    col_brand = 11
    col_op = 12

    title = ["ID", "条码", "商品名", "分类", "库存", "新增",
             "成本", "售价", "封面图", "海报图", "备注", "品牌", "操作"]

    brand_keywords = ['小卡尼', '得力', '晨光', '黑龙', '昊霆', '毛毛鱼',
                      '千色坊', '文源', '宏翔', '常吉', '优佰', '掌握', '国誉',
                      '派通', '百乐', '斑马',]

    profit_ratio = 2.0
    doc_col_idx = {'barcode': 0, 'name': 0, 'cost': 0, 'num': 0}

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def eventFilter(self, obj, e):
        if e.type() == QEvent.MouseButtonPress:
            if obj.objectName() == 'category_selector':
                self.category_selector.show()
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
        self.category_selector.setModal(True)
        self.category_selector.finished.connect(self.updateCategory)

        self.total_form = QFormLayout()
        self.total_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.total_form.addRow("新增数量:", QLabel(
            "0", alignment=Qt.AlignmentFlag.AlignRight))
        self.total_form.addRow("新增进价:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))

        btn_clear = QPushButton('清理')
        btn_clear.clicked.connect(self.onClear)
        btn_read = QPushButton('文件批量入库')
        btn_read.clicked.connect(self.onParseExcel)
        btn_import = QPushButton('入库')
        btn_import.clicked.connect(self.onImport)
        vbox = QVBoxLayout()
        vbox.addWidget(btn_clear)
        vbox.addWidget(btn_read)
        vbox.addStretch(1)
        vbox.addWidget(btn_import)
        vbox.addLayout(self.total_form)

        hbox = QHBoxLayout()
        hbox.addWidget(self.tbl)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

    def onParseExcel(self, checked):
        file, filter = QFileDialog.getOpenFileName(
            self, '选择库存单据', './', '*.xls *.xlsx')
        if not file:
            return
        print('excel', file)
        doc = xlrd.open_workbook(file)
        sheet = doc.sheet_by_index(0)
        title_row = 0
        for col in range(sheet.ncols):
            title_name = sheet.cell_value(title_row, col)
            if title_name in self.doc_col_idx.keys():
                self.doc_col_idx[title_name] = col
        if sum(self.doc_col_idx.values()) == 0:
            QMessageBox.warning(self, '警告', '库存单据字段未格式化')
            return

        start_row = 1
        total_row = sheet.nrows - 1
        for row in range(start_row, total_row):
            barcode = sheet.cell_value(row, self.doc_col_idx['barcode'])
            name = sheet.cell_value(row, self.doc_col_idx['name'])
            add_num = int(sheet.cell_value(row, self.doc_col_idx['num']))
            cost = sheet.cell_value(row, self.doc_col_idx['cost'])
            brand = next(
                (k for k in self.brand_keywords if name.find(k) != -1), '')

            data, success = RequestData(BaseUrl + "/goods/" + barcode)
            if not success:
                return
            if data.get('errmsg'):
                data = {
                    'add_num': add_num,
                    'name': name,
                    'cost_price': cost,
                    'brand': brand,
                    'retail_price': math.floor(cost * self.profit_ratio)
                }
            else:
                data['name'] = name
                data['add_num'] = add_num
                data['cost_price'] = cost
                data['brand'] = brand
            self.addRow(data, barcode=barcode)

    def updateTotal(self):
        total_add_num = 0
        total_add_price = 0.00
        for i in range(self.tbl.rowCount()):
            item_add_num = self.tbl.cellWidget(i, self.col_add_num)
            item_cost_price = self.tbl.cellWidget(i, self.col_cost_price)

            price = item_add_num.value() * float(item_cost_price.value())
            total_add_num += item_add_num.value()
            total_add_price += float(price)

        item_total_add_num = self.total_form.itemAt(
            0, QFormLayout.FieldRole).widget()
        item_total_add_price = self.total_form.itemAt(
            1, QFormLayout.FieldRole).widget()

        item_total_add_num.setText(str(total_add_num))
        item_total_add_price.setText(format(total_add_price, ".2f"))

    def addRow(self, data, barcode):
        print(data)

        id = data.get('id', 0)
        category = data.get('category', {'id': -1})
        num = data.get('num', 0)
        add_num = data.get('add_num', 1)
        name = data.get('name', '')
        remark = data.get('remark', '')
        brand = data.get('brand', '')
        thumbnail = data.get('thumbnail', [''])
        poster = data.get('poster', [''])
        cost_price = data.get('cost_price', 0.0)
        retail_price = data.get('retail_price', 0.0)

        row = FindRow(barcode, self.tbl, self.col_barcode)
        if row != -1:
            item = self.tbl.cellWidget(row, self.col_add_num)
            item.setValue(item.value() + add_num)
        else:
            row = self.tbl.rowCount()
            self.tbl.setRowCount(row + 1)

            item_id = QTableWidgetItem(str(id))
            item_id.setFlags(item_id.flags() & ~
                             Qt.ItemFlag.ItemIsEditable)

            item_barcode = QTableWidgetItem(barcode)
            item_barcode.setFlags(item_barcode.flags() & ~
                                  Qt.ItemFlag.ItemIsEditable)

            item_name = QLineEdit(name)

            item_num = QTableWidgetItem(str(num))
            item_num.setFlags(item_barcode.flags() & ~
                              Qt.ItemFlag.ItemIsEditable)

            item_add_num = QSpinBox(objectName='my_line_edit')
            item_add_num.setValue(add_num)
            item_add_num.setMaximum(10000)
            item_add_num.valueChanged.connect(self.updateTotal)
            item_add_num.installEventFilter(self)

            item_category_id = QLineEdit(objectName='category_selector')
            item_category_id.setText(str(category['id']))
            item_category_id.setProperty('index', item_name)
            item_category_id.installEventFilter(self)

            item_cost_price = QDoubleSpinBox(objectName='my_line_edit')
            item_cost_price.setSingleStep(0.5)
            item_cost_price.setMaximum(9999.99)
            item_cost_price.setValue(float(cost_price))
            item_cost_price.valueChanged.connect(self.updateTotal)
            item_cost_price.installEventFilter(self)

            item_retail_price = QDoubleSpinBox(objectName='my_line_edit')
            item_retail_price.setSingleStep(0.5)
            item_retail_price.setMaximum(9999.99)
            item_retail_price.setValue(float(retail_price))
            item_retail_price.installEventFilter(self)

            item_thumbnail = QLineEdit(';'.join(thumbnail))
            item_poster = QLineEdit(';'.join(poster))
            item_remark = QLineEdit(remark)
            item_brand = QLineEdit(brand)

            btn_remove = QPushButton('移除')
            btn_remove.clicked.connect(self.removeRow)

            self.tbl.setItem(row, self.col_id, item_id)
            self.tbl.setItem(row, self.col_barcode, item_barcode)
            self.tbl.setItem(row, self.col_num, item_num)
            self.tbl.setCellWidget(row, self.col_name, item_name)
            self.tbl.setCellWidget(row, self.col_add_num, item_add_num)
            self.tbl.setCellWidget(row, self.col_category_id, item_category_id)
            self.tbl.setCellWidget(row, self.col_cost_price, item_cost_price)
            self.tbl.setCellWidget(
                row, self.col_retail_price, item_retail_price)
            self.tbl.setCellWidget(row, self.col_thumbnail, item_thumbnail)
            self.tbl.setCellWidget(row, self.col_poster, item_poster)
            self.tbl.setCellWidget(row, self.col_remark, item_remark)
            self.tbl.setCellWidget(row, self.col_brand, item_brand)
            self.tbl.setCellWidget(row, self.col_op, btn_remove)

        self.updateTotal()
        Beep.play()

    def onClear(self):
        self.tbl.setRowCount(0)
        self.updateTotal()

    def updateCategory(self, code):
        item = self.focusWidget()
        if code == QDialog.DialogCode.Accepted:
            item.setText(str(self.category_selector.category_id))

            row = self.tbl.currentRow()
            name = self.tbl.cellWidget(row, self.col_name).text()
            if name.strip() == '':
                prefix = self.tbl.cellWidget(row, self.col_brand).text()
                name = prefix + '-' + self.category_selector.category_name
                self.tbl.cellWidget(row, self.col_name).setText(name)

    def onImport(self):
        if self.tbl.rowCount() == 0:
            return

        for row in range(self.tbl.rowCount()):
            id = int(self.tbl.item(row, self.col_id).text())
            barcode = self.tbl.item(row, self.col_barcode).text()
            num = int(self.tbl.item(row, self.col_num).text())
            category_id = int(self.tbl.cellWidget(
                row, self.col_category_id).text())
            add_num = self.tbl.cellWidget(row, self.col_add_num).value()
            cost_price = self.tbl.cellWidget(
                row, self.col_cost_price).value()
            retail_price = self.tbl.cellWidget(
                row, self.col_retail_price).value()
            thumbnail = self.tbl.cellWidget(row, self.col_thumbnail).text()
            poster = self.tbl.cellWidget(row, self.col_poster).text()
            name = self.tbl.cellWidget(row, self.col_name).text()
            remark = self.tbl.cellWidget(row, self.col_remark).text()
            brand = self.tbl.cellWidget(row, self.col_brand).text()

            data = {
                'name': name,
                'category_id': category_id,
                'num': num + add_num,
                'cost_price': cost_price,
                'retail_price': retail_price,
                'brand': brand,
                'remark': remark,
                'thumbnail': thumbnail,
                'poster': poster
            }
            resp, success = RequestData(
                BaseUrl + '/cli/goods/' + barcode,
                'POST' if id == 0 else 'PUT',
                data,
                '入库失败, 系统异常'
            )
            if not success:
                return
            data = resp.json()
            if resp.get('errmsg'):
                QMessageBox.warning(self, '警告', resp['errmsg'])
                return

        Beep.play()
        self.onClear()

    def handleInput(self, text):
        if text == "":
            QMessageBox.warning(self, '警告', '未识别到条码')
            return

        resp, success = RequestData(BaseUrl + "/cli/goods/" + text)
        if not success:
            return
        self.addRow(resp.json(), text)

    def removeRow(self):
        btn = self.sender()
        if btn:
            row = self.tbl.indexAt(btn.pos()).row()
            self.tbl.removeRow(row)
        self.updateTotal()


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
        self.tbl.setAlternatingRowColors(True)
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
        Beep.play()

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

        item_total_num = self.total_form.itemAt(
            0, QFormLayout.FieldRole).widget()
        item_total_price = self.total_form.itemAt(
            1, QFormLayout.FieldRole).widget()

        item_total_num.setText(str(total_num))
        item_total_price.setText(format(total_price, ".2f"))

    def handleInput(self, text):
        if text == "":
            QMessageBox.warning(self, '警告', '未识别到条码')
            return

        resp, success = RequestData(BaseUrl + "/cli/goods/" + text)
        if not success:
            return
        data = resp.json()
        if data.get('errmsg'):
            QMessageBox.warning(self, '警告', resp.get('errmsg'))
            return
        self.addRow(data, text)

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
        resp, success = RequestData(
            BaseUrl + "/cli/settle",
            'POST',
            post_data,
            '后台结算异常'
        )
        if not success:
            return
        data = resp.json()
        if data.get('errmsg'):
            QMessageBox.warning(self, '警告', data['errmsg'])
            return

        self.onClear()
        Beep.play()

    def onClear(self):
        self.tbl.setRowCount(0)
        self.updateTotal()


class BillDetailWidget(QDialog):
    goods_fields = ['图片', '条码', '商品名', '数量']

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.field_id = QLabel("")
        self.field_sn = QLabel("")
        self.field_num = QLabel("")
        self.field_discount = QLabel("")
        self.field_payable = QLabel("")
        self.field_pay_platform = QLabel("")
        self.field_created_time = QLabel("")

        self.field_status = QComboBox()
        self.field_status.addItems(['0', '1', '2', '3'])

        formLayout = QFormLayout()
        formLayout.addRow("ID", self.field_id)
        formLayout.addRow("SN", self.field_sn)
        formLayout.addRow("商品数", self.field_num)
        formLayout.addRow("折扣", self.field_discount)
        formLayout.addRow("应收", self.field_payable)
        formLayout.addRow("支付平台", self.field_pay_platform)
        formLayout.addRow("账单状态", self.field_status)
        formLayout.addRow("创建日期", self.field_created_time)

        self.tbl = QTableView()
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setDefaultSectionSize(300)
        self.tbl.setAlternatingRowColors(True)

        btn_confirm = QPushButton('确定')
        btn_confirm.clicked.connect(self.onConfirm)
        vbox = QVBoxLayout()
        vbox.addLayout(formLayout)
        vbox.addWidget(self.tbl)
        vbox.addWidget(btn_confirm)
        self.setLayout(vbox)

        self.setWindowTitle('账单详情')
        self.setFixedSize(Resolution * 0.8)

    def onConfirm(self, checked):
        url = BaseUrl + '/cli/bills/' + self.field_id.text()
        status = int(self.field_status.currentText())
        resp, success = RequestData(
            url, 'PUT', {'status': status}, '状态更新异常')
        if not success:
            return
        self.accept()

    def loadData(self, id):
        resp, success = RequestData(BaseUrl + '/cli/bills/' + str(id))
        if not success:
            return
        data = resp.json()
        if isinstance(data, dict):
            QMessageBox.critical(self, '严重', data['errmsg'])
            return

        bill = data[0]['bill']
        self.field_id.setText(str(bill['id']))
        self.field_sn.setText(str(bill['sn']))
        self.field_num.setText(str(bill['num']))
        self.field_discount.setText(str(bill['discount']))
        self.field_payable.setText(str(bill['payable']))
        self.field_pay_platform.setText(str(bill['pay_platform']))
        self.field_status.setCurrentText(str(bill['status']))
        self.field_created_time.setText(str(bill['created_time']))

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(self.goods_fields)
        for i in range(len(data)):
            item = data[i]
            goods_detail = item['goods']

            item_name = QStandardItem(goods_detail['name'])
            item_barcode = QStandardItem(goods_detail['barcode'])
            item_num = QStandardItem(str(item['num']))
            item_img = QStandardItem()

            img_url = goods_detail['thumbnail'][0]
            if len(img_url):
                resp, success = RequestData(
                    img_url, err_msg='商品图片加载异常' + img_url)
                if not success:
                    return
                img = QPixmap()
                img.loadFromData(resp.content)
                img = img.scaled(300, 300)
                item_img.setData(img, Qt.ItemDataRole.DecorationRole)

            model.setItem(i, 0, item_img)
            model.setItem(i, 1, item_barcode)
            model.setItem(i, 2, item_name)
            model.setItem(i, 3, item_num)

        self.tbl.setModel(model)


class BillWidget(QWidget):
    col_id = 0
    col_sn = 1
    col_num = 2
    col_discount = 3
    col_payable = 4
    col_platform = 5
    col_status = 6
    col_created_time = 7
    title = ["ID", "SN", "商品数", "折扣", "应收", "支付平台", "账单状态", "创建日期"]

    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadData()

    def handleInput(self, text):
        return

    def initUI(self):
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(self.title))
        self.tbl.setHorizontalHeaderLabels(self.title)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.itemClicked.connect(self.onItemClicked)

        self.detail_page = BillDetailWidget()
        self.detail_page.setModal(True)
        self.detail_page.finished.connect(self.loadData)

        self.stat_form = QFormLayout()
        self.stat_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.stat_form.addRow("季收益:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))
        self.stat_form.addRow("月收益:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))
        self.stat_form.addRow("上周收益:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))
        self.stat_form.addRow("本周收益:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))
        self.stat_form.addRow("日收益:", QLabel(
            "0.00", alignment=Qt.AlignmentFlag.AlignRight))

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.loadData)

        vbox = QVBoxLayout()
        vbox.addWidget(btn_refresh)
        vbox.addStretch(1)
        vbox.addLayout(self.stat_form)

        layout_grid = QGridLayout()
        layout_grid.addWidget(self.tbl, 0, 0, 1, 1)
        layout_grid.addLayout(vbox, 0, 1, 1, 1)

        self.setLayout(layout_grid)

    def onItemClicked(self, item):
        if item.column() == self.col_id:
            self.detail_page.loadData(int(item.text()))
            self.detail_page.show()

    def loadData(self):
        self.tbl.setRowCount(0)

        resp, success = RequestData(
            BaseUrl + '/cli/bills', err_msg='后台异常, 账单列表加载失败')
        if not success:
            return
        data = resp.json()
        rowCount = len(data)

        self.tbl.setRowCount(rowCount)
        for row in range(rowCount):
            item_id = QTableWidgetItem(str(data[row]['id']))
            item_id.setFlags(item_id.flags() & ~
                             Qt.ItemFlag.ItemIsEditable)

            item_sn = QTableWidgetItem(data[row]['sn'])
            item_sn.setFlags(item_id.flags() & ~
                             Qt.ItemFlag.ItemIsEditable)

            item_num = QTableWidgetItem(str(data[row]['num']))
            item_num.setFlags(item_id.flags() & ~
                              Qt.ItemFlag.ItemIsEditable)

            item_discount = QTableWidgetItem(str(data[row]['discount']))
            item_discount.setFlags(item_id.flags() & ~
                                   Qt.ItemFlag.ItemIsEditable)

            item_payable = QTableWidgetItem(str(data[row]['payable']))
            item_payable.setFlags(item_id.flags() & ~
                                  Qt.ItemFlag.ItemIsEditable)

            item_pay_platform = QTableWidgetItem(
                str(data[row]['pay_platform']))
            item_pay_platform.setFlags(item_id.flags() & ~
                                       Qt.ItemFlag.ItemIsEditable)

            item_status = QTableWidgetItem(str(data[row]['status']))
            item_status.setFlags(item_id.flags() & ~
                                 Qt.ItemFlag.ItemIsEditable)

            item_created_time = QTableWidgetItem(data[row]['created_time'])
            item_created_time.setFlags(item_id.flags() & ~
                                       Qt.ItemFlag.ItemIsEditable)

            self.tbl.setItem(row, self.col_id, item_id)
            self.tbl.setItem(row, self.col_sn, item_sn)
            self.tbl.setItem(row, self.col_num, item_num)
            self.tbl.setItem(row, self.col_discount, item_discount)
            self.tbl.setItem(row, self.col_payable, item_payable)
            self.tbl.setItem(row, self.col_platform, item_pay_platform)
            self.tbl.setItem(row, self.col_status, item_status)
            self.tbl.setItem(row, self.col_created_time, item_created_time)

        resp, success = RequestData(
            BaseUrl + '/cli/bills/stat', err_msg='获取统计信息失败, 后台异常')
        if not success:
            return
        data = resp.json()
        item_total_this_quarter = self.stat_form.itemAt(
            0, QFormLayout.FieldRole).widget()
        item_total_this_month = self.stat_form.itemAt(
            1, QFormLayout.FieldRole).widget()
        item_total_last_week = self.stat_form.itemAt(
            2, QFormLayout.FieldRole).widget()
        item_total_this_week = self.stat_form.itemAt(
            3, QFormLayout.FieldRole).widget()
        item_total_today = self.stat_form.itemAt(
            4, QFormLayout.FieldRole).widget()
        item_total_today.setText(str(data['today']))
        item_total_this_week.setText(str(data['this_week']))
        item_total_last_week.setText(str(data['last_week']))
        item_total_this_month.setText(str(data['this_month']))
        item_total_this_quarter.setText(str(data['this_quarter']))


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.installEventFilter(self)
        self.initUI()

        shortcut_quit = QShortcut(QKeySequence('Alt+Q'), self)
        shortcut_quit.activated.connect(self.onQuit)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:
            if not isinstance(obj, (QSpinBox, QDoubleSpinBox)):
                DoKeyPressEvent(e, self.tab.currentWidget().handleInput)
                return True
            else:
                if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
                    obj.clearFocus()
                    return True
        return False

    def initUI(self):
        settle_page = SettleWidget(self)
        settle_page.installEventFilter(self)
        stock_page = StockWidget(self)
        stock_page.installEventFilter(self)
        bill_page = BillWidget()

        self.tab = QTabWidget()
        self.tab.setStyleSheet("QTabBar::tab { height: 50px; width: 300px; }")
        self.tab.addTab(bill_page, '订单')
        self.tab.addTab(stock_page, '库存')
        self.tab.addTab(settle_page, '结算')

        layout = QGridLayout()
        layout.addWidget(self.tab, 0, 0, 1, 1)
        self.setLayout(layout)

        self.setWindowTitle('收银系统 - 墨为文体用品店 V2.0')
        self.showFullScreen()

    def onQuit(self):
        qApp.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    Resolution = QSize(app.desktop().width(), app.desktop().height())
    print('Screen Resolution: ', Resolution)

    Beep = QSound('./dong.wav', app)
    main = MainWidget()

    sys.exit(app.exec_())
