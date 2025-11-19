import tkinter as tk
from tkinter import messagebox, simpledialog
import api_cliente

class VentanaLogin:
    def __init__(self, master, app_instance):
        self.master = master
        self.app = app_instance # Instancia de la clase App (el controlador)
        
        # Frame principal de la vista
        self.frame = tk.Frame(master, pady=20)
        self.frame.pack(expand=True)

        tk.Label(self.frame, text="Usuario:", font=("Arial", 12)).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.entry_usuario = tk.Entry(self.frame, font=("Arial", 12), width=20)
        self.entry_usuario.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(self.frame, text="Contraseña:", font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.entry_pass = tk.Entry(self.frame, font=("Arial", 12), width=20, show="*")
        self.entry_pass.grid(row=1, column=1, pady=5, padx=5)

        btn_login = tk.Button(self.frame, text="Iniciar Sesión", command=self.ejecutar_login, font=("Arial", 12), bg="#4CAF50", fg="white")
        btn_login.grid(row=2, column=0, columnspan=2, pady=10)
        
        btn_registrar = tk.Button(self.frame, text="Registrarse", command=self.ejecutar_registro, font=("Arial", 10))
        btn_registrar.grid(row=3, column=0, columnspan=2, pady=5)
        
        tk.Label(master, text="Cód. Usuario: Abogado2025 | Cód. Admin: SocioFundadorVIP", fg="grey").pack(side="bottom", pady=5)

    def ejecutar_login(self):
        usuario = self.entry_usuario.get()
        password = self.entry_pass.get()
        if not usuario or not password:
            self.app.mostrar_error("Usuario y contraseña son requeridos.")
            return
        try:
            token = api_cliente.login(usuario, password)
            self.app.token = token
            self.app.nombre_usuario = usuario
            
            # Obtener contactos y detectar rol
            contactos = api_cliente.obtener_contactos(token)
            mi_info_encontrada = False
            for c in contactos:
                if c["nombre"] == self.app.nombre_usuario:
                    self.app.uuid_usuario = c["uuid"]
                    self.app.soy_admin = c.get("es_admin", False)
                    mi_info_encontrada = True
                    break
            self.app.contactos = contactos
            
            if not mi_info_encontrada:
                print("Advertencia: Usuario sin clave pública.")
            
            self.app.manejar_login_exitoso()

        except Exception as e:
            self.app.mostrar_error(str(e))
            
    def ejecutar_registro(self):
        usuario = self.entry_usuario.get()
        password = self.entry_pass.get()
        if not usuario or not password:
            self.app.mostrar_error("Ingrese usuario y contraseña.")
            return
        
        codigo = simpledialog.askstring("Código de Acceso", "Ingrese Código (Usuario o Admin):", show="*")
        if not codigo: return

        try:
            nuevo_usuario = api_cliente.registrar_usuario(usuario, password, codigo)
            
            # El servidor devuelve el estado del rol
            tipo = "ADMINISTRADOR" if nuevo_usuario.get("es_admin") else "Usuario"
            
            self.app.mostrar_exito(f"¡{tipo} '{usuario}' registrado!\nAhora inicia sesión.")
        except Exception as e:
            self.app.mostrar_error(str(e))