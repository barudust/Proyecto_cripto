import tkinter as tk
from tkinter import messagebox
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vistas.ventana_login import VentanaLogin
from vistas.ventana_principal import VentanaPrincipal
from vistas.ventana_admin_panel import VentanaAdmin # Importamos la vista admin

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Seguro")
        self.root.geometry("800x600")

        self.token = None
        self.nombre_usuario = None
        self.uuid_usuario = None
        self.soy_admin = False
        
        self.contactos = []
        self.documentos_en_lista = []

        self.mostrar_ventana_login()

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def mostrar_ventana_login(self):
        self.limpiar_ventana()
        self.root.title("Iniciar Sesión")
        VentanaLogin(self.root, self)

    def manejar_login_exitoso(self):
        """Decide a qué pantalla ir según el rol"""
        if self.soy_admin:
            self.mostrar_ventana_admin()
        else:
            self.mostrar_ventana_principal()

    def mostrar_ventana_principal(self):
        self.limpiar_ventana()
        self.root.title(f"Bandeja Usuario - {self.nombre_usuario}")
        VentanaPrincipal(self.root, self)

    def mostrar_ventana_admin(self):
        self.limpiar_ventana()
        self.root.title(f"PANEL DE CONTROL - ADMIN: {self.nombre_usuario}")
        # Usamos VentanaAdmin pero adaptada para ser frame principal o gestionada aquí
        # Para simplificar, instanciamos la clase y dejamos que pinte sobre self.root
        # Nota: Modificaremos VentanaAdmin para que no sea Toplevel sino un Frame si se prefiere,
        # o simplemente ocultamos root y mostramos la ventana.
        # ESTRATEGIA: Limpiar root e incrustar el contenido del admin.
        VentanaAdmin(self.root, self, es_frame_principal=True)

    def cerrar_sesion(self):
        if messagebox.askyesno("Salir", "¿Desea cerrar sesión?"):
            self.token = None
            self.nombre_usuario = None
            self.uuid_usuario = None
            self.soy_admin = False
            self.mostrar_ventana_login()

    def mostrar_error(self, mensaje):
        messagebox.showerror("Error", mensaje)

    def mostrar_exito(self, mensaje):
        messagebox.showinfo("Éxito", mensaje)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()