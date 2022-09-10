import re
from PySide6 import QtCore
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox,QTableWidgetItem)
from ui_main import Ui_MainWindow
import sys
from ui_functions import consulta_cnpj
import pandas as pd
from database import Data_base
import pandas as pd

class MainWindow(QMainWindow, Ui_MainWindow): #Aqui a classe MainWindow herda propriedades da QMainWindow e Ui_MainWindow
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Pytax - Sistema de cadastro de empresas") #Titulo da janela
        appIcon = QIcon(u"") #Seleciona o ícone do programa
        self.setWindowIcon(appIcon)

        # Botão para abrir o menu esquerdo
        self.btn_toggle.clicked.connect(self.leftMenu)

        # Paginas do sistema
        self.btn_home.clicked.connect(lambda:self.Pages.setCurrentWidget(self.pg_home))
        self.btn_cadastrar.clicked.connect(lambda:self.Pages.setCurrentWidget(self.pg_cadastrar))
        self.btn_sobre.clicked.connect(lambda:self.Pages.setCurrentWidget(self.pg_sobre))
        self.btn_contatos.clicked.connect(lambda:self.Pages.setCurrentWidget(self.pg_contatos))

        # Metodos 
        self.txt_cnpj.editingFinished.connect(self.consult_api)
        self.pushButton_5.clicked.connect(self.cadastrar_empresas)
        self.btn_alterar.clicked.connect(self.updata_company)
        self.btn_excluir.clicked.connect(self.deletar_empresa)
        self.btn_excel.clicked.connect(self.gerar_excel)

        self.buscar_empresas()


    # Menu Lateral
    def leftMenu(self):
        width = self.left_container.width()
        if width == 9:
            newWidth = 200
        else:
            newWidth = 9

        self.animation = QtCore.QPropertyAnimation(self.left_container, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(width)
        self.animation.setEndValue(newWidth)
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()
    
    # Chama a API
    def consult_api(self):
        campos = consulta_cnpj(self.txt_cnpj.text())

        self.txt_nome.setText(campos[0])
        self.txt_logradouro.setText(campos[1])
        self.txt_numero.setText(campos[2])
        self.txt_complemento.setText(campos[3])
        self.txt_bairro.setText(campos[4])
        self.txt_municipio.setText(campos[5])
        self.txt_uf.setText(campos[6])
        self.txt_cep.setText(campos[7].replace('.','').replace('-',''))
        self.txt_telefone.setText(campos[8].replace('(','').replace('-','').replace(')',''))
        self.txt_email.setText(campos[9])


    def cadastrar_empresas(self):
        db = Data_base()
        db.connect()

        fullDataSet = (
            self.txt_cnpj.text(), self.txt_nome.text(),self.txt_logradouro.text(), self.txt_numero.text(), 
            self.txt_complemento.text(), self.txt_bairro.text(), self.txt_municipio.text(), self.txt_uf.text(), self.txt_cep.text(), 
            self.txt_telefone.text().strip(),self.txt_email.text() # o ".strip()" elimina os espaços em branco da esquerda e direita
            )
        #CADSATRAR NO BANCO DE DADOS 
        resp = db.register_company(fullDataSet)        

        if resp == "OK":
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Cadastro Realizado")
            msg.setText("Cadastro Realizado com Sucesso")
            msg.exec()
            self.buscar_empresas()
            db.close_connection()
            return 
        
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Erro")
            msg.setText("Erro ao cadastrar ! verifique se as informações estão corretas ou se o CNPJ já consta cadastrado!")
            msg.exec()
            db.close_connection()
            return


    def buscar_empresas(self):
        db = Data_base()
        db.connect()
        result = db.select_all_companies() #tras todas as empresas pra essa variavel
        
        self.tableWidget.clearContents() #Limpa os dados da tabela toda vez que eu chamar essa função, ou seja, vai zerar e recriar
        self.tableWidget.setRowCount(len(result)) #mostra o numero de dados, ou seja, se tiver 10 empresas ele retornas as 10

        for row,text in enumerate(result):
            for column, data in enumerate(text):
                self.tableWidget.setItem(row,column, QTableWidgetItem(str(data)))
        db.close_connection()


    def updata_company(self):
        dados = []
        update_dados = []
        
        for row in range(self.tableWidget.rowCount()):
            for column in range(self.tableWidget.columnCount()):
                dados.append(self.tableWidget.item(row, column).text())

            update_dados.append(dados)
            dados = []
        #Atualizar dados no banco
        db = Data_base()
        db.connect()

        for emp in update_dados:
            db.update_company(tuple(emp))
        
        db.close_connection()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Atualização de Dados")
        msg.setText("Dados atualizados com sucesso")
        msg.exec()

        self.tableWidget.reset()
        self.buscar_empresas()


    def deletar_empresa(self):
        db = Data_base()
        db.connect()

        msg = QMessageBox()
        msg.setWindowTitle("Excluir")
        msg.setText("Este registro sera excluido")
        msg.setInformativeText("Voce tem certeza que deseja excluir?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        resp = msg.exec()

        if resp == QMessageBox.Yes:
            cnpj = self.tableWidget.selectionModel().currentIndex().siblingAtColumn(0).data()
            result = db.delete_companies(cnpj)
            self.buscar_empresas()
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("EMPRESAS")
            msg.setText(result)
            msg.exec()

        db.close_connection()


    def gerar_excel(self):
        dados = []
        all_dados = []
        for row in range(self.tableWidget.rowCount()):
            for column in range(self.tableWidget.columnCount()):
                dados.append(self.tableWidget.item(row, column).text())
            all_dados.append(dados)
            dados = [0]
        columns = ['CNPJ','CNPJ','NOME', 'LOGRADOURO', 'NUMERO','COMPLEMENTO','BAIRRO','MUNICIPIO','UF', 'CEP','TELEFONE','EMAIL']
        empresas = pd.DataFrame(all_dados, columns=columns)
        empresas.to_excel("arquivos_excel/Empresas.xlsx", sheet_name='empresas',index=False)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Excel")
        msg.setText("Relatório Excel gerado com sucesso!")
        msg.exec()



# O código abaixo executa a janela
if __name__ == "__main__": #Se for a janela principal que esta sendo executada, executa a aplicação abaixo
    db = Data_base()
    db.connect()
    db.create_table_company()
    db.close_connection()
    

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
    
    