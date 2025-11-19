import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
import sys
import os

# Ajuste de path para encontrar api_cliente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_cliente

class VentanaAdmin(tk.Toplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.title("Panel de Administración")
        self.geometry("400x400")
        self.app = app_instance
        
        tk.Label(self, text="Gestión de Usuarios", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self, text="Selecciona un usuario para eliminarlo del sistema:", fg="grey").pack()

        # Lista de usuarios
        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        scrollbar = Scrollbar(list_frame, orient="vertical")
        self.lista_usuarios = Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 12))
        scrollbar.config(command=self.lista_usuarios.yview)
        
        scrollbar.pack(side="right", fill="y")
        self.lista_usuarios.pack(side="left", fill="both", expand=True)

        # Botón Eliminar
        btn_eliminar = tk.Button(self, text="🗑️ ELIMINAR USUARIO", bg="#ffcdd2", fg="red", font=("Arial", 10, "bold"), command=self.eliminar_seleccionado)
        btn_eliminar.pack(pady=10, fill="x", padx=20)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        self.lista_usuarios.delete(0, "end")
        self.mapa_usuarios = []
        
        # Filtramos para que no se muestre a sí mismo (el admin)
        for u in self.app.contactos:
            if u["nombre"] != self.app.nombre_usuario:
                rol = "[ADMIN]" if u.get("es_admin") else "[USER]"
                self.lista_usuarios.insert("end", f"{u['nombre']} {rol}")
                self.mapa_usuarios.append(u)
        
        if not self.mapa_usuarios:
            self.lista_usuarios.insert("end", "(No hay otros usuarios)")

    def eliminar_seleccionado(self):
        seleccion = self.lista_usuarios.curselection()
        if not seleccion:
            messagebox.showerror("Error", "Selecciona un usuario de la lista.")
            return

        usuario_a_borrar = self.mapa_usuarios[seleccion[0]]
        nombre = usuario_a_borrar["nombre"]
        uuid_borrar = usuario_a_borrar["uuid"]

        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación", 
            f"¿Estás SEGURO de que quieres eliminar a '{nombre}'?\n\n"
            "⚠️ Esta acción borrará sus claves y acceso a documentos permanentemente.\n"
            "No se puede deshacer."
        )

        if confirmacion:
            try:
                api_cliente.eliminar_usuario_admin(self.app.token, uuid_borrar)
                messagebox.showinfo("Éxito", f"Usuario '{nombre}' eliminado correctamente.")
                
                # Recargar la lista local y en la app principal
                self.app.contactos = api_cliente.obtener_contactos(self.app.token)
                self.cargar_usuarios()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")