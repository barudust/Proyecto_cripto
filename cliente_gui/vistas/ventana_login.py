import tkinter as tk
from tkinter import messagebox, simpledialog
import api_cliente

class VentanaLogin:
    def __init__(self, master, app_instance):
        self.master = master
        self.app = app_instance
        
        # Acceder a la paleta de colores de la app principal
        self.colores = app_instance.colores
        
        # Frame principal con el mismo fondo que la app
        self.frame = tk.Frame(master, pady=30, bg=self.colores['light'])
        self.frame.pack(expand=True, fill='both')
        
        # Título del formulario
        titulo = tk.Label(self.frame, 
                         text="Iniciar Sesión", 
                         font=("Segoe UI", 16, "bold"),
                         fg=self.colores['primary'],
                         bg=self.colores['light'])
        titulo.pack(pady=(0, 20))

        # Frame para los campos del formulario
        form_frame = tk.Frame(self.frame, bg=self.colores['light'])
        form_frame.pack(pady=10)

        # Campo Usuario
        lbl_usuario = tk.Label(form_frame, 
                              text="Usuario:", 
                              font=("Segoe UI", 11),
                              fg=self.colores['text'],
                              bg=self.colores['light'])
        lbl_usuario.grid(row=0, column=0, sticky="e", pady=8, padx=5)
        
        self.entry_usuario = tk.Entry(form_frame, 
                                     font=("Segoe UI", 11),
                                     width=25,
                                     bg='white',
                                     fg=self.colores['text'],
                                     insertbackground=self.colores['primary'],
                                     relief='solid',
                                     borderwidth=1)
        self.entry_usuario.grid(row=0, column=1, pady=8, padx=5, ipady=4)

        # Campo Contraseña
        lbl_pass = tk.Label(form_frame, 
                           text="Contraseña:", 
                           font=("Segoe UI", 11),
                           fg=self.colores['text'],
                           bg=self.colores['light'])
        lbl_pass.grid(row=1, column=0, sticky="e", pady=8, padx=5)
        
        self.entry_pass = tk.Entry(form_frame, 
                                  font=("Segoe UI", 11),
                                  width=25,
                                  show="•",
                                  bg='white',
                                  fg=self.colores['text'],
                                  insertbackground=self.colores['primary'],
                                  relief='solid',
                                  borderwidth=1)
        self.entry_pass.grid(row=1, column=1, pady=8, padx=5, ipady=4)

        # Frame para botones
        button_frame = tk.Frame(self.frame, bg=self.colores['light'])
        button_frame.pack(pady=20)

        # Botón Iniciar Sesión
        btn_login = tk.Button(button_frame, 
                             text="Iniciar Sesión", 
                             command=self.ejecutar_login, 
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colores['primary'],
                             fg='white',
                             relief='flat',
                             borderwidth=0,
                             width=15,
                             cursor='hand2')
        btn_login.pack(pady=8, ipady=8)

        # Botón Registrarse
        btn_registrar = tk.Button(button_frame, 
                                 text="Registrarse", 
                                 command=self.ejecutar_registro, 
                                 font=("Segoe UI", 10),
                                 bg=self.colores['secondary'],
                                 fg='white',
                                 relief='flat',
                                 borderwidth=0,
                                 width=12,
                                 cursor='hand2')
        btn_registrar.pack(pady=5, ipady=6)

        # Información de códigos
        info_codigos = tk.Label(self.frame, 
                               font=("Segoe UI", 9),
                               fg=self.colores['text_light'],
                               bg=self.colores['light'])
        info_codigos.pack(side="bottom", pady=10)
        
        # Bind Enter key para facilitar el login
        self.entry_usuario.bind('<Return>', lambda e: self.entry_pass.focus())
        self.entry_pass.bind('<Return>', lambda e: self.ejecutar_login())
        
        # Focus inicial en el campo de usuario
        self.entry_usuario.focus_set()

    def ejecutar_login(self):
        usuario = self.entry_usuario.get().strip()
        password = self.entry_pass.get().strip()
        
        if not usuario or not password:
            self.app.mostrar_error("Usuario y contraseña son requeridos.")
            return
        
        try:
            # Deshabilitar botones durante el login
            self.master.update_idletasks()
            
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
        usuario = self.entry_usuario.get().strip()
        password = self.entry_pass.get().strip()
        
        if not usuario or not password:
            self.app.mostrar_error("Ingrese usuario y contraseña.")
            return
        
        codigo = simpledialog.askstring("Código de Acceso", "Ingrese Código:", show="*")
        if not codigo: 
            return

        try:
            nuevo_usuario = api_cliente.registrar_usuario(usuario, password, codigo)
            
            # El servidor devuelve el estado del rol
            tipo = "ADMINISTRADOR" if nuevo_usuario.get("es_admin") else "Usuario"
            
            self.app.mostrar_exito(f"¡{tipo} '{usuario}' registrado!\nAhora inicia sesión.")
            
            # Limpiar solo la contraseña después del registro
            self.entry_pass.delete(0, tk.END)
            
        except Exception as e:
            self.app.mostrar_error(str(e))