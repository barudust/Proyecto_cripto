import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ajuste para que encuentre la carpeta 'vistas' y los módulos raíz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vistas.ventana_login import VentanaLogin
from vistas.ventana_principal import VentanaPrincipal

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente Cripto Seguro")
        self.root.geometry("800x600")

        # Estado Global de la Sesión
        self.token = None
        self.nombre_usuario = None
        self.uuid_usuario = None
        self.soy_admin = False
        
        # Datos en memoria
        self.contactos = []
        self.documentos_en_lista = []

        # Iniciar en el Login
        self.mostrar_ventana_login()

    def limpiar_ventana(self):
        """Elimina todos los widgets de la ventana actual"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def mostrar_ventana_login(self):
        self.limpiar_ventana()
        self.root.title("Iniciar Sesión - CriptoApp")
        # Instanciamos la vista de Login pasándole el controlador (self)
        VentanaLogin(self.root, self)

    def mostrar_ventana_principal(self):
        self.limpiar_ventana()
        self.root.title(f"Bandeja Principal - {self.nombre_usuario}")
        # Instanciamos la vista Principal
        VentanaPrincipal(self.root, self)

    def cerrar_sesion(self):
        if messagebox.askyesno("Salir", "¿Desea cerrar sesión?"):
            self.token = None
            self.nombre_usuario = None
            self.uuid_usuario = None
            self.soy_admin = False
            self.mostrar_ventana_login()

    # --- Métodos Globales de Ayuda ---
    def mostrar_error(self, mensaje):
        messagebox.showerror("Error", mensaje)

    def mostrar_exito(self, mensaje):
        messagebox.showinfo("Éxito", mensaje)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()