import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_cliente

class VentanaAdmin:
    def __init__(self, master, app_instance, es_frame_principal=False):
        self.app = app_instance
        self.master = master
        
        if es_frame_principal:
            self.window = master
        else:
            self.window = tk.Toplevel(master)
            self.window.title("Panel Admin")
            self.window.geometry("500x500")

        # Frame Contenedor
        main_frame = tk.Frame(self.window, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Encabezado
        header = tk.Frame(main_frame)
        header.pack(fill="x", pady=10)
        
        tk.Label(header, text="PANEL DE ADMINISTRADOR", font=("Arial", 16, "bold"), fg="red").pack(side="left")
        tk.Button(header, text="🚪 Cerrar Sesión", command=self.app.cerrar_sesion, bg="#ffcdd2").pack(side="right")

        tk.Label(main_frame, text="Gestión de Usuarios del Sistema", font=("Arial", 12)).pack(anchor="w")
        tk.Label(main_frame, text="Nota: Al eliminar un usuario, se borrarán sus documentos.", font=("Arial", 9), fg="grey").pack(anchor="w")

        # Lista
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)

        scrollbar = Scrollbar(list_frame, orient="vertical")
        self.lista_usuarios = Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 11))
        scrollbar.config(command=self.lista_usuarios.yview)
        
        scrollbar.pack(side="right", fill="y")
        self.lista_usuarios.pack(side="left", fill="both", expand=True)

        # Botones
        btn_eliminar = tk.Button(main_frame, text="🗑️ ELIMINAR USUARIO SELECCIONADO", bg="red", fg="white", font=("Arial", 11, "bold"), command=self.eliminar_seleccionado)
        btn_eliminar.pack(fill="x", pady=5)
        
        btn_refresh = tk.Button(main_frame, text="🔄 Actualizar Lista", command=self.cargar_usuarios)
        btn_refresh.pack(fill="x", pady=5)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        try:
            self.app.contactos = api_cliente.obtener_contactos(self.app.token)
            self.lista_usuarios.delete(0, "end")
            self.mapa_usuarios = []
            
            for u in self.app.contactos:
                # --- FILTRO DE SEGURIDAD ---
                # Si el UUID del usuario en la lista es IGUAL al mío (Admin conectado),
                # NO lo agrego a la lista visual.
                if u["uuid"] == self.app.uuid_usuario:
                    continue

                rol = "[ADMIN]" if u.get("es_admin") else "[USUARIO]"
                texto = f"{u['nombre']:<20} {rol}"
                self.lista_usuarios.insert("end", texto)
                self.mapa_usuarios.append(u)
            
            # Mensaje si no hay nadie más
            if not self.mapa_usuarios:
                self.lista_usuarios.insert("end", "(No hay otros usuarios registrados)")

        except Exception as e:
            self.app.mostrar_error(f"Error cargando usuarios: {e}")

    def eliminar_seleccionado(self):
        seleccion = self.lista_usuarios.curselection()
        if not seleccion:
            # Validación extra por si selecciona el mensaje de "(No hay otros usuarios)"
            if not self.mapa_usuarios:
                return
            messagebox.showerror("Error", "Selecciona un usuario.")
            return

        usuario_a_borrar = self.mapa_usuarios[seleccion[0]]
        
        # Doble verificación de seguridad (aunque ya no debería aparecer en la lista)
        if usuario_a_borrar["uuid"] == self.app.uuid_usuario:
            messagebox.showwarning("Error", "No puedes eliminarte a ti mismo.")
            return

        confirmacion = messagebox.askyesno(
            "PELIGRO - Borrado Permanente", 
            f"¿Estás seguro de eliminar a '{usuario_a_borrar['nombre']}'?\n\n"
            "ESTO BORRARÁ TODOS SUS DOCUMENTOS Y CLAVES.\n"
            "Esta acción es irreversible."
        )

        if confirmacion:
            try:
                api_cliente.eliminar_usuario_admin(self.app.token, usuario_a_borrar["uuid"])
                messagebox.showinfo("Éxito", f"Usuario '{usuario_a_borrar['nombre']}' eliminado.")
                self.cargar_usuarios()
            except Exception as e:
                messagebox.showerror("Error", str(e))