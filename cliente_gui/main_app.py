import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vistas.ventana_login import VentanaLogin
from vistas.ventana_principal import VentanaPrincipal
from vistas.ventana_admin_panel import VentanaAdmin

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Bufete Legal Seguro - Sistema de Documentos")
        self.root.geometry("1280x860")
        
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
            'white': '#ffffff'
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
        
        self.mostrar_ventana_login()

    def configurar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=self.colores['primary'])
        style.configure('Card.TFrame', background=self.colores['primary'])
        
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 22, 'bold'),
                       foreground=self.colores['light'],
                       background=self.colores['primary'])
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 15),
                       foreground=self.colores['light'],
                       background=self.colores['primary'])
        style.configure('Card.TLabel',
                       font=('Segoe UI', 12),
                       foreground=self.colores['text'],
                       background=self.colores['white'])
        
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background=self.colores['primary'],
                       foreground=self.colores['white'],
                       borderwidth=0,
                       focuscolor='none')
        style.map('Primary.TButton',
                 background=[('active', '#2d3748')])
        
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 10),
                       background=self.colores['secondary'],
                       foreground=self.colores['white'],
                       borderwidth=0)
        style.map('Secondary.TButton',
                 background=[('active', '#b8944d')])
        
        style.configure('Modern.TEntry',
                       fieldbackground=self.colores['white'],
                       foreground=self.colores['text'],
                       borderwidth=1,
                       relief='solid')

    def crear_menu_superior(self):
        menubar = tk.Menu(self.root, 
                         bg=self.colores['primary'], 
                         fg=self.colores['white'],
                         activebackground=self.colores['secondary'],
                         activeforeground=self.colores['primary'])
        self.root.config(menu=menubar)
        
        archivo_menu = tk.Menu(menubar, 
                              tearoff=0, 
                              bg=self.colores['white'], 
                              fg=self.colores['text'],
                              activebackground=self.colores['light'])
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Cerrar Sesión", command=self.cerrar_sesion)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        
        ayuda_menu = tk.Menu(menubar, 
                            tearoff=0, 
                            bg=self.colores['white'], 
                            fg=self.colores['text'],
                            activebackground=self.colores['light'])
        menubar.add_cascade(label="Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self.mostrar_acerca_de)

    def crear_header(self):
        header_frame = ttk.Frame(self.root, style='TFrame')
        header_frame.pack(fill='x', padx=20, pady=15)
        
        logo_frame = ttk.Frame(header_frame, style='TFrame')
        logo_frame.pack(fill='x')
        
        title_label = ttk.Label(logo_frame, 
                               text="Bufete Legal Seguro - Sistema de Gestión Documental Cifrada", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        subtitle_label = ttk.Label(logo_frame,
                                  text="",
                                  style='Subtitle.TLabel')
        subtitle_label.pack(side='left', padx=(15, 0))
        
        if self.nombre_usuario:
            user_frame = ttk.Frame(header_frame, style='TFrame')
            user_frame.pack(fill='x', pady=10)
            
            user_info = tk.Frame(user_frame, bg=self.colores['light'])
            user_info.pack(side='right')
            
            user_label = tk.Label(user_info,
                                 text=f"{self.nombre_usuario} | {'Administrador' if self.soy_admin else 'Abogado'}",
                                 font=('Segoe UI', 10, 'bold'),
                                 foreground=self.colores['primary'],
                                 background=self.colores['light'])
            user_label.pack(side='left', padx=(0, 15))
            
            logout_btn = ttk.Button(user_info,
                                   text="Cerrar Sesión",
                                   command=self.cerrar_sesion,
                                   style='Secondary.TButton')
            logout_btn.pack(side='left')

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()

    def mostrar_ventana_login(self):
        self.limpiar_ventana()
        self.root.title("Bufete Legal Seguro - Iniciar Sesión")
        
        main_frame = tk.Frame(self.root, bg=self.colores['primary'])
        main_frame.pack(expand=True, fill='both', padx=50, pady=50)
        
        content_frame = tk.Frame(main_frame, bg=self.colores['primary'])
        content_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        login_card = tk.Frame(content_frame, bg=self.colores['primary'])
        login_card.pack(padx=20, pady=20, ipadx=30, ipady=30)
        
        welcome_frame = tk.Frame(login_card, bg=self.colores['primary'])
        welcome_frame.pack(pady=(0, 30))
        
        ttk.Label(welcome_frame, 
                text="Bufete Legal Seguro",
                foreground=self.colores['secondary'],
                background=self.colores['primary'],
                font=('Segoe UI', 16, 'bold')).pack(pady=(10, 5))
        
        ttk.Label(welcome_frame,
                text="Sistema de Gestión Documental Cifrada",
                foreground=self.colores['text_light'],
                background=self.colores['primary'],
                font=('Segoe UI', 12)).pack()
        
        form_frame = tk.Frame(login_card, bg=self.colores['primary'])
        form_frame.pack(fill='x', pady=20)
        
        VentanaLogin(form_frame, self)

    def manejar_login_exitoso(self):
        self.limpiar_ventana()
        self.crear_header()
        
        if self.soy_admin:
            self.mostrar_ventana_admin()
        else:
            self.mostrar_ventana_principal()

    def mostrar_ventana_principal(self):
        self.limpiar_ventana()
        self.crear_header()
        self.root.title(f"Bufete Legal Seguro - Bandeja de {self.nombre_usuario}")
        
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        VentanaPrincipal(main_frame, self)

    def mostrar_ventana_admin(self):
        self.limpiar_ventana()
        self.crear_header()
        self.root.title("Bufete Legal Seguro - Panel de Administración")
        
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        VentanaAdmin(main_frame, self, es_frame_principal=True)

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión", 
                              "¿Está seguro de que desea cerrar sesión?",
                              icon='warning'):
            self.token = None
            self.nombre_usuario = None
            self.uuid_usuario = None
            self.soy_admin = False
            self.limpiar_ventana()
            self.mostrar_ventana_login()

    def mostrar_error(self, mensaje):
        messagebox.showerror("Error del Sistema", mensaje, icon='error')

    def mostrar_exito(self, mensaje):
        messagebox.showinfo("Operación Exitosa", mensaje, icon='info')

    def mostrar_acerca_de(self):
        about_text = f"""Bufete Legal Seguro
Sistema de Gestión Documental Cifrada

Versión 1.0
Desarrollado para garantizar la máxima seguridad
y confidencialidad de sus documentos legales.

© 2024 Bufete Legal Seguro - Todos los derechos reservados"""
        
        messagebox.showinfo("Acerca del Sistema", about_text)

    def crear_boton_estilizado(self, parent, text, command, style='Primary.TButton'):
        return ttk.Button(parent, text=text, command=command, style=style)

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap(default='')
    root.eval('tk::PlaceWindow . center')
    
    app = App(root)
    root.mainloop()
