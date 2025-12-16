import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vistas.ventana_login import VentanaLogin
from vistas.ventana_principal import VentanaPrincipal
from vistas.ventana_admin_panel import VentanaAdmin

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Bufete Legal Seguro - Sistema de Documentos")
        self.root.state('zoomed') # Maximizar ventana para que quepa la consola
        
        self.colores = {
            'primary': '#1a365d',
            'secondary': '#c9a96e',
            'accent': '#2d3748',
            'light': "#e6f0ff",
            'success': '#38a169',
            'warning': '#dd6b20',
            'danger': '#e53e3e',
            'text': '#2d3748',
            'text_light': '#718096',
            'white': '#ffffff',
            'console_bg': '#000000',
            'console_fg': '#00ff00'
        }
        
        self.root.configure(bg=self.colores['primary'])
        self.configurar_estilo()
        
        self.token = None
        self.nombre_usuario = None
        self.uuid_usuario = None
        self.soy_admin = False
        
        self.contactos = []
        self.documentos_en_lista = []

        self.crear_menu_superior()
        
        # --- NUEVO: Frame Principal que divide App y Consola ---
        self.contenedor_global = tk.Frame(self.root, bg=self.colores['primary'])
        self.contenedor_global.pack(fill='both', expand=True)

        self.frame_app = tk.Frame(self.contenedor_global, bg=self.colores['primary'])
        self.frame_app.pack(side='top', fill='both', expand=True)


        # -----------------------------------------------------
        
        self.mostrar_ventana_login()

    def configurar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.colores['primary'])
        style.configure('Card.TFrame', background=self.colores['primary'])
        style.configure('Title.TLabel', font=('Segoe UI', 36, 'bold'), foreground=self.colores['light'], background=self.colores['primary'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 15), foreground=self.colores['light'], background=self.colores['primary'])
        style.configure('Card.TLabel', font=('Segoe UI', 12), foreground=self.colores['text'], background=self.colores['white'])
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), background=self.colores['primary'], foreground=self.colores['white'], borderwidth=0, focuscolor='none')
        style.map('Primary.TButton', background=[('active', '#2d3748')])
        style.configure('Secondary.TButton', font=('Segoe UI', 10), background=self.colores['secondary'], foreground=self.colores['white'], borderwidth=0)
        style.map('Secondary.TButton', background=[('active', '#b8944d')])
        style.configure('Modern.TEntry', fieldbackground=self.colores['white'], foreground=self.colores['text'], borderwidth=1, relief='solid')


    def loguear(self, mensaje, titulo="INFO"):
        print(f"[{titulo}] {mensaje}")

    def crear_menu_superior(self):
        menubar = tk.Menu(self.root, bg=self.colores['primary'], fg=self.colores['white'])
        self.root.config(menu=menubar)
        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Cerrar Sesión", command=self.cerrar_sesion)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        ayuda_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self.mostrar_acerca_de)

    def crear_header(self):
        header_frame = ttk.Frame(self.frame_app, style='TFrame')
        header_frame.pack(fill='x', padx=20, pady=15)
        
        logo_frame = ttk.Frame(header_frame, style='TFrame')
        logo_frame.pack(fill='x')
        
        title_label = ttk.Label(logo_frame, text="Bufete Legal Seguro - Sistema de Documentos", style='Title.TLabel')
        title_label.pack(side='left')
        
        if self.nombre_usuario:
            user_frame = ttk.Frame(header_frame, style='TFrame')
            user_frame.pack(fill='x', pady=10)
            user_info = tk.Frame(user_frame, bg=self.colores['light'])
            user_info.pack(side='right')
            user_label = tk.Label(user_info, text=f"{self.nombre_usuario} | {'Administrador' if self.soy_admin else 'Abogado'}",
                                 font=('Segoe UI', 10, 'bold'), foreground=self.colores['primary'], background=self.colores['light'])
            user_label.pack(side='left', padx=(0, 15))
            logout_btn = ttk.Button(user_info, text="Cerrar Sesión", command=self.cerrar_sesion, style='Secondary.TButton')
            logout_btn.pack(side='left')

    def limpiar_ventana(self):
        for widget in self.frame_app.winfo_children():
            widget.destroy()

    def mostrar_ventana_login(self):
        self.limpiar_ventana()
        self.root.title("Bufete Legal Seguro - Iniciar Sesión")
        main_frame = tk.Frame(self.frame_app, bg=self.colores['primary'])
        main_frame.pack(expand=True, fill='both', padx=50, pady=50)
        content_frame = tk.Frame(main_frame, bg=self.colores['primary'])
        content_frame.place(relx=0.5, rely=0.5, anchor='center')
        login_card = tk.Frame(content_frame, bg=self.colores['primary'])
        login_card.pack(padx=20, pady=20, ipadx=30, ipady=30)
        
        ttk.Label(login_card, text="Acceso Seguro", style='Title.TLabel').pack(pady=(0, 20))
        form_frame = tk.Frame(login_card, bg=self.colores['primary'])
        form_frame.pack(fill='x', pady=20)
        VentanaLogin(form_frame, self)

    def manejar_login_exitoso(self):
        self.limpiar_ventana()
        self.crear_header()
        
        # LOG DEL TOKEN AL ENTRAR
        self.loguear("Autenticación Exitosa.", "AUTH")
        self.loguear(f"Token JWT Recibido (Firmado con HS256):\n{self.token[:50]}...[TRUNCADO]", "JWT")
        
        if self.soy_admin:
            self.mostrar_ventana_admin()
        else:
            self.mostrar_ventana_principal()

    def mostrar_ventana_principal(self):
        self.limpiar_ventana()
        self.crear_header()
        self.root.title(f"Bandeja de {self.nombre_usuario}")
        main_frame = ttk.Frame(self.frame_app, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        VentanaPrincipal(main_frame, self)

    def mostrar_ventana_admin(self):
        self.limpiar_ventana()
        self.crear_header()
        self.root.title("Panel de Administración")
        main_frame = ttk.Frame(self.frame_app, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        VentanaAdmin(main_frame, self, es_frame_principal=True)

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Salir?"):
            self.token = None
            self.nombre_usuario = None
            self.soy_admin = False
            self.limpiar_ventana()
            self.mostrar_ventana_login()
            self.loguear("Sesión finalizada. Claves borradas de memoria.", "SYS")

    def mostrar_error(self, mensaje):
        messagebox.showerror("Error", mensaje)
        self.loguear(f"ERROR: {mensaje}", "ERR")

    def mostrar_exito(self, mensaje):
        messagebox.showinfo("Éxito", mensaje)
        self.loguear(f"OPERACIÓN EXITOSA: {mensaje}", "OK")

    def mostrar_acerca_de(self):
        messagebox.showinfo("Acerca de", "Sistema de Cifrado Híbrido v1.0")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()