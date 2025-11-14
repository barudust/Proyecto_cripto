# cliente_gui/main_app.py
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, Listbox, Scrollbar, Toplevel, MULTIPLE

# Importamos todas las "herramientas" que construimos
import api_cliente
import logica_claves
import logica_cifrado
import logica_descifrado

import os

# --- CLASE PARA LA VENTANA POP-UP DE SELECCIÓN DE CONTACTOS ---
class DialogoSeleccionReceptores(Toplevel):
    def __init__(self, parent, contactos):
        super().__init__(parent)
        self.title("Seleccionar Receptores")
        self.geometry("300x400")
        
        self.contactos = contactos
        self.receptores_seleccionados = [] # Aquí guardamos los dicts

        tk.Label(self, text="Selecciona uno o más receptores:").pack(pady=10)

        # Frame para la lista
        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10)

        scrollbar = Scrollbar(list_frame, orient="vertical")
        self.lista_box = Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=MULTIPLE)
        scrollbar.config(command=self.lista_box.yview)
        
        scrollbar.pack(side="right", fill="y")
        self.lista_box.pack(side="left", fill="both", expand=True)

        # Llenar la lista
        for contacto in self.contactos:
            # Añadimos el nombre para que el usuario lo vea
            self.lista_box.insert("end", contacto["nombre"])

        btn_seleccionar = tk.Button(self, text="Seleccionar", command=self.seleccionar)
        btn_seleccionar.pack(pady=10)
        
        # Hacer que la ventana sea "modal" (bloquea la ventana principal)
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def seleccionar(self):
        indices_seleccionados = self.lista_box.curselection()
        
        # Mapeamos los índices de vuelta a los objetos de contacto
        for i in indices_seleccionados:
            self.receptores_seleccionados.append(self.contactos[i])
            
        if not self.receptores_seleccionados:
            messagebox.showerror("Error", "Debes seleccionar al menos un receptor.", parent=self)
            return
            
        self.destroy() # Cerrar la ventana pop-up

# --- CLASE PRINCIPAL DE LA APLICACIÓN ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente de Documentos Seguros")
        self.root.geometry("600x500")

        self.token = None
        self.nombre_usuario = None
        self.uuid_usuario = None
        self.contactos = []
        self.documentos_en_lista = []

        self.mostrar_ventana_login()

    def mostrar_ventana_login(self):
        # ... (Esta función es idéntica a la que ya tienes)
        self.limpiar_ventana()
        login_frame = tk.Frame(self.root, pady=20)
        login_frame.pack(expand=True)
        tk.Label(login_frame, text="Usuario:", font=("Arial", 12)).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.entry_usuario = tk.Entry(login_frame, font=("Arial", 12), width=20)
        self.entry_usuario.grid(row=0, column=1, pady=5, padx=5)
        tk.Label(login_frame, text="Contraseña:", font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.entry_pass = tk.Entry(login_frame, font=("Arial", 12), width=20, show="*")
        self.entry_pass.grid(row=1, column=1, pady=5, padx=5)
        btn_login = tk.Button(login_frame, text="Iniciar Sesión", command=self.ejecutar_login, font=("Arial", 12), bg="#4CAF50", fg="white")
        btn_login.grid(row=2, column=0, columnspan=2, pady=10)
        btn_registrar = tk.Button(login_frame, text="Registrarse", command=self.ejecutar_registro, font=("Arial", 10))
        btn_registrar.grid(row=3, column=0, columnspan=2, pady=5)

    def ejecutar_login(self):
        usuario = self.entry_usuario.get()
        password = self.entry_pass.get()
        if not usuario or not password:
            self.mostrar_error("Usuario y contraseña son requeridos.")
            return
        try:
            self.token = api_cliente.login(usuario, password)
            self.nombre_usuario = usuario
            
            # Obtenemos la lista de contactos y nuestro propio UUID
            self.contactos = api_cliente.obtener_contactos(self.token)
            mi_info_encontrada = False
            for c in self.contactos:
                if c["nombre"] == self.nombre_usuario:
                    self.uuid_usuario = c["uuid"]
                    mi_info_encontrada = True
                    break
            
            if not mi_info_encontrada:
                # Esto podría pasar si el usuario es nuevo y aún no tiene clave pública
                print("Advertencia: No se encontró el UUID del usuario (quizás no ha subido su clave).")
            
            self.mostrar_ventana_principal()
        except Exception as e:
            self.mostrar_error(str(e))
            
    def ejecutar_registro(self):
        usuario = self.entry_usuario.get()
        password = self.entry_pass.get()
        if not usuario or not password:
            self.mostrar_error("Para registrarse, ingrese un nuevo usuario y contraseña.")
            return
        try:
            nuevo_usuario = api_cliente.registrar_usuario(usuario, password)
            self.mostrar_exito(f"Usuario '{usuario}' registrado.\nAhora inicia sesión.")
        except Exception as e:
            self.mostrar_error(str(e))
            
    def mostrar_ventana_principal(self):
        # ... (Idéntica a la que ya tienes, pero con la función de cifrado)
        self.limpiar_ventana()
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        tk.Label(main_frame, text=f"Bienvenido, {self.nombre_usuario}", font=("Arial", 16)).pack(anchor="w")
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        btn_generar_claves = tk.Button(btn_frame, text="Generar/Subir Claves", command=self.generar_y_subir_claves)
        btn_generar_claves.pack(side="left", padx=5)
        
        # ¡Este botón ahora funciona!
        btn_cifrar = tk.Button(btn_frame, text="Cifrar Nuevo Archivo", command=self.ejecutar_cifrado_completo)
        btn_cifrar.pack(side="left", padx=5)

        tk.Label(main_frame, text="Documentos Recibidos:", font=("Arial", 12)).pack(anchor="w", pady=(10,0))
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        self.lista_documentos = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.lista_documentos.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista_documentos.pack(side="left", fill="both", expand=True)
        
        self.lista_documentos.bind("<Double-Button-1>", self.ejecutar_descifrado)
        btn_refrescar = tk.Button(main_frame, text="Refrescar Bandeja", command=self.refrescar_bandeja)
        btn_refrescar.pack(pady=10)
        self.refrescar_bandeja()

    def refrescar_bandeja(self):
        # ... (Idéntica a la que ya tienes)
        try:
            self.lista_documentos.delete(0, "end")
            documentos = api_cliente.listar_documentos_recibidos(self.token)
            self.documentos_en_lista = documentos
            if not documentos:
                self.lista_documentos.insert("end", " (No tienes documentos)")
                return
            for i, doc in enumerate(documentos):
                autor_nombre = "Desconocido"
                for c in self.contactos:
                    if c["uuid"] == doc["propietario_uuid"]:
                        autor_nombre = c["nombre"]
                        break
                texto = f"{doc['nombre_original']} (ID: {doc['id']}) (De: {autor_nombre})"
                self.lista_documentos.insert("end", texto)
        except Exception as e:
            self.mostrar_error(str(e))

    def ejecutar_descifrado(self, event):
        # ... (Idéntica a la que ya tienes)
        try:
            seleccion = self.lista_documentos.curselection()
            if not seleccion: return
            doc_info = self.documentos_en_lista[seleccion[0]]
            doc_id = doc_info["id"]
            
            ruta_privada = filedialog.askopenfilename(title="Selecciona tu Clave Privada (.pem)", filetypes=[("PEM files", "*.pem")])
            if not ruta_privada: return
            pass_privada = simpledialog.askstring("Contraseña", "Contraseña de tu clave privada:", show="*")
            if not pass_privada: return

            self.mostrar_exito("Descargando y descifrando...")
            zip_bytes = api_cliente.descargar_documento_zip(self.token, doc_id)
            
            clave_autor = None
            for c in self.contactos:
                if c["uuid"] == doc_info["propietario_uuid"]:
                    clave_autor = c["clave_publica"]
                    break
            if not clave_autor:
                raise Exception("No se encontró la clave pública del autor para verificar la firma.")

            plaintext, firma_valida = logica_descifrado.descifrar_paquete(
                zip_bytes=zip_bytes,
                mi_uuid=self.uuid_usuario,
                ruta_clave_privada=ruta_privada,
                password_clave_privada=pass_privada,
                clave_publica_autor=clave_autor
            )
            
            ruta_guardado = filedialog.asksaveasfilename(title="Guardar archivo descifrado", initialfile=f"DESCIFRADO_{doc_info['nombre_original']}")
            if not ruta_guardado: return
            
            with open(ruta_guardado, "wb") as f: f.write(plaintext)
            
            firma_texto = "¡FIRMA VÁLIDA!" if firma_valida else "¡FIRMA INVÁLIDA O CORRUPTA!"
            self.mostrar_exito(f"¡Archivo guardado!\n{ruta_guardado}\n\nVerificación de firma: {firma_texto}")
        except Exception as e:
            self.mostrar_error(f"Error al descifrar: {e}")

    def generar_y_subir_claves(self):
        # ... (Idéntica a la que ya tienes)
        try:
            pass_privada = simpledialog.askstring("Contraseña de Clave", "Crea una contraseña para tu clave privada (¡NO LA OLVIDES!):", show="*")
            if not pass_privada: return
            carpeta_descargas = os.path.join(os.path.expanduser('~'), 'Downloads')
            if not os.path.exists(carpeta_descargas):
                carpeta_descargas = os.path.expanduser('~')
            
            clave_publica_pem, ruta_privada = logica_claves.generar_par_claves(
                password=pass_privada,
                carpeta_guardado=carpeta_descargas,
                nombre_usuario=self.nombre_usuario
            )
            
            api_cliente.subir_clave_publica(self.token, clave_publica_pem)
            self.mostrar_exito(f"¡Claves generadas! Tu clave privada se guardó en:\n{ruta_privada}")
        except Exception as e:
            self.mostrar_error(str(e))
            
    # --- ¡FUNCIÓN NUEVA Y FINAL! ---
    def ejecutar_cifrado_completo(self):
        """Reemplaza el placeholder 'mostrar_dialogo_cifrar'."""
        try:
            # 1. Seleccionar archivo a cifrar
            ruta_original = filedialog.askopenfilename(title="Selecciona un archivo para cifrar")
            if not ruta_original: return
            
            # 2. Seleccionar clave privada para firmar
            ruta_privada = filedialog.askopenfilename(title="Selecciona TU Clave Privada (.pem) para FIRMAR", filetypes=[("PEM files", "*.pem")])
            if not ruta_privada: return
            
            # 3. Pedir contraseña de la clave
            pass_privada = simpledialog.askstring("Contraseña", "Contraseña de tu clave privada:", show="*")
            if not pass_privada: return
            
            # 4. Seleccionar receptores (¡usando la nueva ventana pop-up!)
            # Nos aseguramos de incluirnos a nosotros mismos
            receptores_disponibles = self.contactos
            dialogo = DialogoSeleccionReceptores(self.root, receptores_disponibles)
            # (El código se pausa aquí hasta que el usuario cierre el pop-up)
            
            receptores_seleccionados = dialogo.receptores_seleccionados
            if not receptores_seleccionados:
                self.mostrar_error("No se seleccionó ningún receptor.")
                return

            self.mostrar_exito("Cifrando... esto puede tardar.")
            
            # 5. Llamar a la lógica de cifrado
            ruta_zip_temporal, metadata_api = logica_cifrado.crear_paquete_cifrado(
                ruta_archivo_original=ruta_original,
                ruta_clave_privada_autor=ruta_privada,
                password_clave_privada=pass_privada,
                uuid_autor=self.uuid_usuario,
                receptores=receptores_seleccionados
            )
            
            # 6. Llamar a la API para subir el ZIP
            api_cliente.subir_documento_cifrado(
                token=self.token,
                ruta_archivo_zip=ruta_zip_temporal,
                nombre_original=metadata_api["nombre_original"],
                deks_cifradas=metadata_api["deks_cifradas"]
            )
            
            # 7. Limpiar el ZIP temporal
            if os.path.exists(ruta_zip_temporal):
                os.remove(ruta_zip_temporal)
                
            self.mostrar_exito(f"¡Archivo '{metadata_api['nombre_original']}' cifrado y subido con éxito!")
            
            # 8. Refrescar la bandeja
            self.refrescar_bandeja()

        except Exception as e:
            self.mostrar_error(f"Error en el cifrado: {e}")

    # --- Funciones de Utilidad ---
    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    def mostrar_error(self, mensaje: str):
        messagebox.showerror("Error", mensaje)
    def mostrar_exito(self, mensaje: str):
        messagebox.showinfo("Éxito", mensaje)

# --- Punto de Entrada ---
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()