# Form implementation generated from reading ui file 'designer/form.ui'
#
# Created by: PyQt6 UI code generator 6.3.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(512, 327)
        self.formLayout_2 = QtWidgets.QFormLayout(Dialog)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)
        self.deckChooser = QtWidgets.QWidget(Dialog)
        self.deckChooser.setObjectName("deckChooser")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.deckChooser)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label)
        self.parentDeckLineEdit = QtWidgets.QLineEdit(Dialog)
        self.parentDeckLineEdit.setObjectName("parentDeckLineEdit")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.parentDeckLineEdit)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.separatorFieldRadioButton = QtWidgets.QRadioButton(self.groupBox)
        self.separatorFieldRadioButton.setObjectName("separatorFieldRadioButton")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.separatorFieldRadioButton)
        self.separatorFieldComboBox = QtWidgets.QComboBox(self.groupBox)
        self.separatorFieldComboBox.setObjectName("separatorFieldComboBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.separatorFieldComboBox)
        self.numberOfCardsRadioButton = QtWidgets.QRadioButton(self.groupBox)
        self.numberOfCardsRadioButton.setObjectName("numberOfCardsRadioButton")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.numberOfCardsRadioButton)
        self.numberOfCardsSpinBox = QtWidgets.QSpinBox(self.groupBox)
        self.numberOfCardsSpinBox.setMinimum(1)
        self.numberOfCardsSpinBox.setMaximum(1000000)
        self.numberOfCardsSpinBox.setObjectName("numberOfCardsSpinBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.numberOfCardsSpinBox)
        self.duplicateDeckRadioButton = QtWidgets.QRadioButton(self.groupBox)
        self.duplicateDeckRadioButton.setObjectName("duplicateDeckRadioButton")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.duplicateDeckRadioButton)
        self.duplicateDeckNameLineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.duplicateDeckNameLineEdit.setObjectName("duplicateDeckNameLineEdit")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.duplicateDeckNameLineEdit)
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.groupBox)
        self.processButton = QtWidgets.QPushButton(Dialog)
        self.processButton.setObjectName("processButton")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.processButton)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_2.setText(_translate("Dialog", "Deck"))
        self.label.setText(_translate("Dialog", "Parent deck"))
        self.separatorFieldRadioButton.setText(_translate("Dialog", "Separate by field contents"))
        self.numberOfCardsRadioButton.setText(_translate("Dialog", "Separate by number of cards"))
        self.duplicateDeckRadioButton.setText(_translate("Dialog", "Duplicate deck as"))
        self.processButton.setText(_translate("Dialog", "Process"))
