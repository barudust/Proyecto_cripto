import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, Listbox, Scrollbar, Toplevel, MULTIPLE
import api_cliente
import logica_claves
import logica_cifrado
import logica_descifrado
import os

class DialogoSeleccionReceptores(Toplevel):
    def __init__(self, parent, contactos, mi_uuid):
        super().__init__(parent)
        self.title("Seleccionar Receptores")
        self.geometry("300x400")
        
        self.contactos = contactos
        self.receptores_seleccionados = [] 

        tk.Label(self, text="Selecciona uno o más receptores:").pack(pady=10)

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10)

        scrollbar = Scrollbar(list_frame, orient="vertical")
        self.lista_box = Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=MULTIPLE)
        scrollbar.config(command=self.lista_box.yview)
        
        scrollbar.pack(side="right", fill="y")
        self.lista_box.pack(side="left", fill="both", expand=True)

        self.indices_map = []
        for contacto in self.contactos:
            if contacto["uuid"] != mi_uuid:
                self.lista_box.insert("end", contacto["nombre"])
                self.indices_map.append(contacto)

        btn_seleccionar = tk.Button(self, text="Seleccionar", command=self.seleccionar)
        btn_seleccionar.pack(pady=10)
        
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def seleccionar(self):
        indices_seleccionados = self.lista_box.curselection()
        for i in indices_seleccionados:
            self.receptores_seleccionados.append(self.indices_map[i])   
        if not self.receptores_seleccionados:
            messagebox.showerror("Error", "Debes seleccionar al menos un receptor.", parent=self)
            return
        self.destroy() 

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente de Documentos Seguros")
        self.root.geometry("700x600")

        self.token = None
        self.nombre_usuario = None
        self.uuid_usuario = None
        self.contactos = []
        self.documentos_en_lista = []

        self.mostrar_ventana_login()

    def mostrar_ventana_login(self):
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
            
            self.contactos = api_cliente.obtener_contactos(self.token)
            mi_info_encontrada = False
            for c in self.contactos:
                if c["nombre"] == self.nombre_usuario:
                    self.uuid_usuario = c["uuid"]
                    mi_info_encontrada = True
                    break
            
            if not mi_info_encontrada:
                print("Advertencia: No se encontró el UUID del usuario.")
            
            self.mostrar_ventana_principal()
        except Exception as e:
            self.mostrar_error(str(e))
            
    def ejecutar_registro(self):
        usuario = self.entry_usuario.get()
        password = self.entry_pass.get()
        if not usuario or not password:
            self.mostrar_error("Para registrarse, ingrese un nuevo usuario y contraseña.")
            return
        
        codigo = simpledialog.askstring("Seguridad", "Ingrese el Código de Invitación del Despacho:", show="*")
        if not codigo: return

        try:
            nuevo_usuario = api_cliente.registrar_usuario(usuario, password, codigo)
            self.mostrar_exito(f"Usuario '{usuario}' registrado.\nAhora inicia sesión.")
        except Exception as e:
            self.mostrar_error(str(e))
            
    def mostrar_ventana_principal(self):
        self.limpiar_ventana()
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill="x", pady=5)
        tk.Label(header_frame, text=f"Usuario: {self.nombre_usuario}", font=("Arial", 14, "bold")).pack(side="left")
        
        right_header = tk.Frame(header_frame)
        right_header.pack(side="right")

        btn_refrescar = tk.Button(right_header, text="🔄 Refrescar", command=self.refrescar_bandeja)
        btn_refrescar.pack(side="left", padx=5)

        btn_salir = tk.Button(right_header, text="🚪 Salir", command=self.cerrar_sesion, bg="#ffcdd2")
        btn_salir.pack(side="left", padx=5)

        action_frame = tk.Frame(main_frame, pady=10)
        action_frame.pack(fill="x")
        
        btn_generar_claves = tk.Button(action_frame, text="🔑 Generar/Subir Claves", command=self.generar_y_subir_claves, bg="#e1f5fe")
        btn_generar_claves.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_cifrar = tk.Button(action_frame, text="🔒 Cifrar y Subir Archivo", command=self.ejecutar_cifrado_completo, bg="#e1f5fe")
        btn_cifrar.pack(side="left", padx=5, fill="x", expand=True)

        tk.Label(main_frame, text="Bandeja de Entrada (Documentos):", font=("Arial", 12)).pack(anchor="w", pady=(15,0))
        
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        self.lista_documentos = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10, font=("Consolas", 10))
        scrollbar.config(command=self.lista_documentos.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista_documentos.pack(side="left", fill="both", expand=True)
        
        tk.Label(main_frame, text="Acciones para el documento seleccionado:", font=("Arial", 10, "italic")).pack(anchor="w", pady=(10,5))
        
        botones_descarga_frame = tk.Frame(main_frame)
        botones_descarga_frame.pack(fill="x")
        
        btn_descifrar = tk.Button(botones_descarga_frame, text="📂 Descifrar y Guardar", command=self.accion_solo_descifrar, bg="#fff9c4")
        btn_descifrar.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_verificar = tk.Button(botones_descarga_frame, text="✅ Verificar Firma", command=self.accion_solo_verificar, bg="#c8e6c9")
        btn_verificar.pack(side="left", padx=5, fill="x", expand=True)

        self.refrescar_bandeja()

    def cerrar_sesion(self):
        if messagebox.askyesno("Salir", "¿Desea cerrar sesión?"):
            self.token = None
            self.nombre_usuario = None
            self.uuid_usuario = None
            self.contactos = []
            self.documentos_en_lista = []
            self.mostrar_ventana_login()

    def refrescar_bandeja(self):
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
                texto = f"[{doc['id']}] {doc['nombre_original']} | De: {autor_nombre}"
                self.lista_documentos.insert("end", texto)
        except Exception as e:
            self.mostrar_error(str(e))

    def _preparar_datos_documento(self):
        seleccion = self.lista_documentos.curselection()
        if not seleccion: 
            self.mostrar_error("Primero selecciona un documento de la lista.")
            return None

        doc_info = self.documentos_en_lista[seleccion[0]]
        doc_id = doc_info["id"]
        
        ruta_privada = filedialog.askopenfilename(title="Selecciona tu Clave Privada (.pem)", filetypes=[("PEM files", "*.pem")])
        if not ruta_privada: return None
        
        pass_privada = simpledialog.askstring("Contraseña", "Contraseña de tu clave privada:", show="*")
        if not pass_privada: return None

        try:
            self.mostrar_exito("Procesando... Espere.")
            zip_bytes = api_cliente.descargar_documento_zip(self.token, doc_id)
            
            plaintext, firma_bytes, autor_uuid = logica_descifrado.descifrar_contenido(
                zip_bytes=zip_bytes,
                mi_uuid=self.uuid_usuario,
                ruta_clave_privada=ruta_privada,
                password_clave_privada=pass_privada
            )
            return (plaintext, firma_bytes, autor_uuid, doc_info['nombre_original'])
            
        except Exception as e:
            self.mostrar_error(f"Error en el proceso: {e}")
            return None

    def accion_solo_descifrar(self):
        datos = self._preparar_datos_documento()
        if not datos: return
        
        plaintext, _, _, nombre_orig = datos
        
        ruta_guardado = filedialog.asksaveasfilename(title="Guardar Archivo", initialfile=f"DESCIFRADO_{nombre_orig}")
        if not ruta_guardado: return
        
        try:
            with open(ruta_guardado, "wb") as f: f.write(plaintext)
            self.mostrar_exito(f"Archivo guardado correctamente en:\n{ruta_guardado}")
        except Exception as e:
            self.mostrar_error(f"Error al guardar: {e}")

    def accion_solo_verificar(self):
        datos = self._preparar_datos_documento()
        if not datos: return
        
        plaintext, firma_bytes, autor_uuid_zip, _ = datos
        
        clave_autor = None
        nombre_autor = "Desconocido"
        for c in self.contactos:
            if c["uuid"] == autor_uuid_zip:
                clave_autor = c["clave_publica"]
                nombre_autor = c["nombre"]
                break
        
        if not clave_autor:
            self.mostrar_error(f"No se puede verificar.\nNo tienes la clave pública del autor (UUID: {autor_uuid_zip}).")
            return

        es_valida = logica_descifrado.verificar_firma(plaintext, firma_bytes, clave_autor)
        
        if es_valida:
            messagebox.showinfo("Verificación de Firma", f"✅ FIRMA VÁLIDA\n\nEl documento es auténtico y fue firmado por:\n{nombre_autor}")
        else:
            messagebox.showerror("Verificación de Firma", f"❌ FIRMA INVÁLIDA\n\n¡Cuidado! El documento ha sido modificado o no proviene de {nombre_autor}.")

    def generar_y_subir_claves(self):
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
    def ejecutar_cifrado_completo(self):
        try:
            ruta_original = filedialog.askopenfilename(title="Selecciona un archivo para cifrar")
            if not ruta_original: return
            
            ruta_privada = filedialog.askopenfilename(title="Selecciona TU Clave Privada (.pem) para FIRMAR", filetypes=[("PEM files", "*.pem")])
            if not ruta_privada: return
            
            pass_privada = simpledialog.askstring("Contraseña", "Contraseña de tu clave privada:", show="*")
            if not pass_privada: return
            
            receptores_disponibles = self.contactos
            dialogo = DialogoSeleccionReceptores(self.root, receptores_disponibles, self.uuid_usuario)
            
            receptores_seleccionados = dialogo.receptores_seleccionados
            if not receptores_seleccionados:
                return 

            # Auto-inclusión del autor
            mi_contacto = next((c for c in self.contactos if c["uuid"] == self.uuid_usuario), None)
            if mi_contacto:
                receptores_seleccionados.append(mi_contacto)
            else:
                self.mostrar_error("Error interno: No se encontró tu usuario en la lista de contactos.")
                return

            # --- ¡VALIDACIÓN NUEVA! ---
            # Verificamos que TODOS tengan clave pública antes de seguir
            for receptor in receptores_seleccionados:
                if not receptor.get("clave_publica"):
                    self.mostrar_error(f"El usuario '{receptor['nombre']}' NO ha generado/subido sus claves todavía.\nNo se puede cifrar para él.")
                    return
            # --------------------------

            self.mostrar_exito("Cifrando y subiendo...")
            
            ruta_zip_temporal, metadata_api = logica_cifrado.crear_paquete_cifrado(
                ruta_archivo_original=ruta_original,
                ruta_clave_privada_autor=ruta_privada,
                password_clave_privada=pass_privada,
                uuid_autor=self.uuid_usuario,
                receptores=receptores_seleccionados
            )
            
            api_cliente.subir_documento_cifrado(
                token=self.token,
                ruta_archivo_zip=ruta_zip_temporal,
                nombre_original=metadata_api["nombre_original"],
                deks_cifradas=metadata_api["deks_cifradas"]
            )
            
            if os.path.exists(ruta_zip_temporal):
                os.remove(ruta_zip_temporal)
                
            self.mostrar_exito(f"¡Archivo '{metadata_api['nombre_original']}' cifrado y subido con éxito!")
            self.refrescar_bandeja()

        except Exception as e:
            self.mostrar_error(f"Error en el cifrado: {e}")            



    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    def mostrar_error(self, mensaje: str):
        messagebox.showerror("Error", mensaje)
    def mostrar_exito(self, mensaje: str):
        print(f"INFO: {mensaje}") 

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()