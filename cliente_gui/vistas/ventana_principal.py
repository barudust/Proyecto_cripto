import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, Listbox, Scrollbar, Toplevel, MULTIPLE
import os
import sys

# Importamos módulos lógicos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_cliente
import logica_claves
import logica_cifrado
import logica_descifrado
from vistas.ventana_admin_panel import VentanaAdmin

class DialogoSeleccionReceptores(Toplevel):
    def __init__(self, parent, contactos, mi_uuid):
        super().__init__(parent)
        self.title("Seleccionar Receptores")
        self.geometry("350x400")
        
        self.contactos = contactos
        self.receptores_seleccionados = [] 

        tk.Label(self, text="Selecciona quién podrá ver el archivo:", font=("Arial", 10, "bold")).pack(pady=10)
        tk.Label(self, text="(El administrador y tú mismo están ocultos)", font=("Arial", 8), fg="grey").pack(pady=0)

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        scrollbar = Scrollbar(list_frame, orient="vertical")
        self.lista_box = Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=MULTIPLE, font=("Arial", 11))
        scrollbar.config(command=self.lista_box.yview)
        
        scrollbar.pack(side="right", fill="y")
        self.lista_box.pack(side="left", fill="both", expand=True)

        self.indices_map = []
        
        for contacto in self.contactos:
            if contacto["uuid"] == mi_uuid: continue
            if contacto.get("es_admin") is True: continue

            self.lista_box.insert("end", contacto["nombre"])
            self.indices_map.append(contacto)

        if not self.indices_map:
            self.lista_box.insert("end", "(No hay usuarios disponibles)")
            self.lista_box.config(state="disabled")

        btn_seleccionar = tk.Button(self, text="Confirmar Selección", command=self.seleccionar, bg="#4CAF50", fg="white")
        btn_seleccionar.pack(pady=10)
        
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def seleccionar(self):
        if not self.indices_map:
            self.destroy()
            return

        indices_seleccionados = self.lista_box.curselection()
        for i in indices_seleccionados:
            self.receptores_seleccionados.append(self.indices_map[i])   
        
        if not self.receptores_seleccionados:
            messagebox.showerror("Error", "Debes seleccionar al menos un receptor.", parent=self)
            return
        self.destroy()


class VentanaPrincipal:
    def __init__(self, master, app_instance):
        self.master = master
        self.app = app_instance
        self.colores = app_instance.colores
        
        main_frame = tk.Frame(master, padx=15, pady=15, bg=self.colores['light'])
        main_frame.pack(fill="both", expand=True)
        
        # --- HEADER ---
        header_frame = tk.Frame(main_frame, bg=self.colores['light'])
        header_frame.pack(fill="x", pady=8)
        
        rol_txt = " (ADMIN)" if self.app.soy_admin else ""
        color_u = self.colores['secondary'] if self.app.soy_admin else self.colores['primary']
        
        user_label = tk.Label(header_frame, 
                             text=f"👤 Usuario: {self.app.nombre_usuario}{rol_txt}", 
                             font=("Segoe UI", 14, "bold"), 
                             fg=color_u, bg=self.colores['light'])
        user_label.pack(side="left")
        
        right_header = tk.Frame(header_frame, bg=self.colores['light'])
        right_header.pack(side="right")

        if self.app.soy_admin:
            btn_admin = tk.Button(right_header, text="🛠️ PANEL ADMIN", bg=self.colores['primary'], fg='white',
                                 font=("Segoe UI", 10, "bold"), relief='flat', command=self.abrir_panel_admin)
            btn_admin.pack(side="left", padx=8)

        btn_refrescar = tk.Button(right_header, text="🔄 Refrescar", bg=self.colores['secondary'], fg='white',
                                 font=("Segoe UI", 10), relief='flat', command=self.refrescar_bandeja)
        btn_refrescar.pack(side="left", padx=5)

        btn_salir = tk.Button(right_header, text="🚪 Salir", bg=self.colores['danger'], fg='white',
                             font=("Segoe UI", 10), relief='flat', command=self.app.cerrar_sesion)
        btn_salir.pack(side="left", padx=5)

        # --- BOTONES PRINCIPALES ---
        action_frame = tk.Frame(main_frame, pady=15, bg=self.colores['light'])
        action_frame.pack(fill="x")
        
        btn_generar_claves = tk.Button(action_frame, text="🔑 Generar/Subir Claves", command=self.generar_y_subir_claves, 
                                      bg=self.colores['primary'], fg='white', font=("Segoe UI", 11, "bold"), relief='flat', height=2)
        btn_generar_claves.pack(side="left", padx=8, fill="x", expand=True)
        
        btn_cifrar = tk.Button(action_frame, text="🔒 Cifrar y Subir Archivo", command=self.ejecutar_cifrado_completo, 
                              bg=self.colores['secondary'], fg='white', font=("Segoe UI", 11, "bold"), relief='flat', height=2)
        btn_cifrar.pack(side="left", padx=8, fill="x", expand=True)

        # --- BANDEJA ---
        docs_label = tk.Label(main_frame, text="📁 Bandeja de Documentos Cifrados:", font=("Segoe UI", 12, "bold"),
                             fg=self.colores['primary'], bg=self.colores['light'])
        docs_label.pack(anchor="w", pady=(20, 5))
        
        list_frame = tk.Frame(main_frame, bg=self.colores['light'])
        list_frame.pack(fill="both", expand=True, pady=8)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", bg=self.colores['light'])
        self.lista_documentos = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10, font=("Segoe UI", 10),
                                          bg='white', fg=self.colores['text'], selectbackground=self.colores['primary'], selectforeground='white')
        scrollbar.config(command=self.lista_documentos.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista_documentos.pack(side="left", fill="both", expand=True)
        
        # --- ACCIONES AUDITORÍA / DESCARGA ---
        acciones_label = tk.Label(main_frame, text="🎯 Acciones para el documento seleccionado:", font=("Segoe UI", 10, "italic"),
                                 fg=self.colores['text_light'], bg=self.colores['light'])
        acciones_label.pack(anchor="w", pady=(10, 5))
        
        # Fila 1: Operaciones Normales
        row1_frame = tk.Frame(main_frame, bg=self.colores['light'])
        row1_frame.pack(fill="x", pady=2)
        
        btn_descifrar = tk.Button(row1_frame, text="📂 Descifrar y Guardar", command=self.accion_solo_descifrar, 
                                 bg=self.colores['success'], fg='white', font=("Segoe UI", 10), relief='flat')
        btn_descifrar.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_verificar = tk.Button(row1_frame, text="✅ Verificar Firma (App)", command=self.accion_solo_verificar, 
                                 bg=self.colores['warning'], fg='white', font=("Segoe UI", 10), relief='flat')
        btn_verificar.pack(side="left", padx=5, fill="x", expand=True)

        # Fila 2: Operaciones de Auditoría (Lo que pidió la Profa)
        row2_frame = tk.Frame(main_frame, bg=self.colores['light'])
        row2_frame.pack(fill="x", pady=5)

        # BOTÓN NUEVO: Descargar ZIP RAW
        btn_raw_zip = tk.Button(row2_frame, text="💾 Bajar ZIP Cifrado (Raw)", command=self.accion_bajar_zip_raw, 
                               bg='#555555', fg='white', font=("Segoe UI", 9, "bold"), relief='flat')
        btn_raw_zip.pack(side="left", padx=5, fill="x", expand=True)

        # BOTÓN NUEVO: Descargar Llave Pública
        btn_pub_key = tk.Button(row2_frame, text="🔑 Bajar Key Pública del Autor", command=self.accion_bajar_public_key, 
                               bg='#777777', fg='white', font=("Segoe UI", 9, "bold"), relief='flat')
        btn_pub_key.pack(side="left", padx=5, fill="x", expand=True)

        self.refrescar_bandeja()

    def abrir_panel_admin(self):
        try:
            self.app.contactos = api_cliente.obtener_contactos(self.app.token)
            VentanaAdmin(self.master, self.app) 
        except Exception as e:
            self.app.mostrar_error(str(e))

    def refrescar_bandeja(self):
        try:
            self.lista_documentos.delete(0, "end")
            documentos = api_cliente.listar_documentos_recibidos(self.app.token)
            self.app.documentos_en_lista = documentos
            if not documentos:
                self.lista_documentos.insert("end", " (No tienes documentos)")
                return
            for doc in documentos:
                # Buscar nombre del autor
                autor_nombre = "Desconocido"
                for c in self.app.contactos:
                    if c["uuid"] == doc["propietario_uuid"]:
                        autor_nombre = c["nombre"]
                        break
                texto = f"[{doc['id']}] {doc['nombre_original']} | De: {autor_nombre}"
                self.lista_documentos.insert("end", texto)
        except Exception as e:
            self.app.mostrar_error(str(e))

    def _get_seleccion(self):
        seleccion = self.lista_documentos.curselection()
        if not seleccion: 
            self.app.mostrar_error("Primero selecciona un documento de la lista.")
            return None
        if not self.app.documentos_en_lista: return None
        return self.app.documentos_en_lista[seleccion[0]]

    # --- NUEVA FUNCIÓN: BAJAR ZIP RAW ---
    def accion_bajar_zip_raw(self):
        doc = self._get_seleccion()
        if not doc: return
        
        try:
            self.app.loguear(f"Descargando ZIP Cifrado (Raw) del Doc ID {doc['id']}...", "AUDIT")
            zip_bytes = api_cliente.descargar_documento_zip(self.app.token, doc['id'])
            
            # Sugerir nombre con extensión .zip
            nombre_sugerido = f"CIFRADO_{doc['nombre_original']}.zip"
            ruta_guardado = filedialog.asksaveasfilename(title="Guardar ZIP Cifrado", initialfile=nombre_sugerido, defaultextension=".zip")
            
            if ruta_guardado:
                with open(ruta_guardado, "wb") as f:
                    f.write(zip_bytes)
                self.app.mostrar_exito(f"ZIP Cifrado guardado en:\n{ruta_guardado}")
                self.app.loguear(f"ZIP guardado para inspección externa.", "AUDIT_OK")
        except Exception as e:
            self.app.mostrar_error(str(e))

    # --- NUEVA FUNCIÓN: BAJAR KEY PÚBLICA ---
    def accion_bajar_public_key(self):
        doc = self._get_seleccion()
        if not doc: return

        # Buscar al autor
        autor_uuid = doc["propietario_uuid"]
        autor_obj = next((c for c in self.app.contactos if c["uuid"] == autor_uuid), None)
        
        if not autor_obj:
            # Intentar refrescar contactos por si acaso
            self.app.contactos = api_cliente.obtener_contactos(self.app.token)
            autor_obj = next((c for c in self.app.contactos if c["uuid"] == autor_uuid), None)

        if not autor_obj:
            self.app.mostrar_error("No se encontró la información del autor (UUID desconocido).")
            return
            
        pem_key = autor_obj.get("clave_publica")
        if not pem_key:
            self.app.mostrar_error(f"El autor {autor_obj['nombre']} no tiene clave pública registrada.")
            return

        try:
            self.app.loguear(f"Exportando Llave Pública de {autor_obj['nombre']}...", "AUDIT")
            nombre_sugerido = f"PUBLIC_KEY_{autor_obj['nombre']}.pem"
            ruta_guardado = filedialog.asksaveasfilename(title="Guardar Llave Pública", initialfile=nombre_sugerido, defaultextension=".pem")
            
            if ruta_guardado:
                with open(ruta_guardado, "w") as f:
                    f.write(pem_key)
                self.app.mostrar_exito(f"Llave Pública guardada en:\n{ruta_guardado}")
                self.app.loguear(f"Llave PEM exportada para verificación manual.", "AUDIT_OK")
        except Exception as e:
            self.app.mostrar_error(str(e))


    def accion_solo_descifrar(self):
        doc = self._get_seleccion()
        if not doc: return
        
        ruta_privada = filedialog.askopenfilename(title="Selecciona tu Clave Privada (.pem)", filetypes=[("PEM files", "*.pem")])
        if not ruta_privada: return
        
        pass_privada = simpledialog.askstring("Contraseña", "Contraseña de tu clave privada:", show="*")
        if not pass_privada: return

        try:
            self.app.mostrar_exito("Procesando... Espere.")
            zip_bytes = api_cliente.descargar_documento_zip(self.app.token, doc['id'])
            
            # --- CORRECCIÓN AQUÍ: Recibimos solo 3 valores, no 4 ---
            plaintext, _, _ = logica_descifrado.descifrar_contenido(
                zip_bytes=zip_bytes,
                mi_uuid=self.app.uuid_usuario,
                ruta_clave_privada=ruta_privada,
                password_clave_privada=pass_privada
            )
            
            ruta_guardado = filedialog.asksaveasfilename(title="Guardar Archivo Descifrado", initialfile=f"DESCIFRADO_{doc['nombre_original']}")
            if ruta_guardado:
                with open(ruta_guardado, "wb") as f: f.write(plaintext)
                self.app.mostrar_exito(f"Archivo guardado correctamente.")
                self.app.loguear("Archivo descifrado exitosamente.", "DECRYPT_OK")
            
        except Exception as e:
            self.app.mostrar_error(f"Error: {e}")

    def accion_solo_verificar(self):
        doc = self._get_seleccion()
        if not doc: return
        
        ruta_privada = filedialog.askopenfilename(title="Tu Clave Privada (Para abrir el sobre)", filetypes=[("PEM files", "*.pem")])
        if not ruta_privada: return
        pass_privada = simpledialog.askstring("Contraseña", "Contraseña:", show="*")
        if not pass_privada: return

        try:
            zip_bytes = api_cliente.descargar_documento_zip(self.app.token, doc['id'])
            
            # --- CORRECCIÓN AQUÍ: Recibimos solo 3 valores ---
            plaintext, firma_bytes, autor_uuid = logica_descifrado.descifrar_contenido(
                zip_bytes=zip_bytes, 
                mi_uuid=self.app.uuid_usuario, 
                ruta_clave_privada=ruta_privada, 
                password_clave_privada=pass_privada
            )
            
            # Buscar clave pública del autor para verificar
            self.app.contactos = api_cliente.obtener_contactos(self.app.token)
            autor = next((c for c in self.app.contactos if c["uuid"] == autor_uuid), None)
            
            if not autor:
                self.app.mostrar_error("Autor desconocido (UUID no encontrado en contactos), no se puede verificar firma.")
                return

            es_valida = logica_descifrado.verificar_firma(plaintext, firma_bytes, autor["clave_publica"])
            
            if es_valida:
                messagebox.showinfo("Verificación", f"✅ FIRMA VÁLIDA\n\nEl documento es auténtico y no ha sido modificado.\nFirmado por: {autor['nombre']}")
                self.app.loguear(f"Firma RSA-PSS Verificada: OK. Autor: {autor['nombre']}", "VERIFY_OK")
            else:
                messagebox.showerror("Verificación", "❌ FIRMA INVÁLIDA\n\nEl documento ha sido alterado o la llave pública no coincide.")
                self.app.loguear("Fallo de verificación de firma.", "VERIFY_FAIL")
                
        except Exception as e:
            self.app.mostrar_error(str(e))


    def generar_y_subir_claves(self):
        try:
            pass_privada = simpledialog.askstring("Contraseña", "Crea contraseña para tu clave privada:", show="*")
            if not pass_privada: return
            carpeta = filedialog.askdirectory(title="Dónde guardar tus claves")
            if not carpeta: return
            
            pub, priv_path = logica_claves.generar_par_claves(pass_privada, carpeta, self.app.nombre_usuario)
            api_cliente.subir_clave_publica(self.app.token, pub)
            
            self.app.mostrar_exito(f"Claves generadas en: {carpeta}")
            self.app.loguear("Nuevas claves RSA-2048 generadas y Clave Pública subida al servidor.", "KEYS_GEN")
        except Exception as e:
            self.app.mostrar_error(str(e))

    def ejecutar_cifrado_completo(self):
        # Esta es la misma lógica que te pasé en el paso anterior (con logs), 
        # asegúrate de que use 'self.app.loguear'
        try:
            ruta_original = filedialog.askopenfilename(title="Selecciona archivo")
            if not ruta_original: return
            
            self.app.loguear(f"Seleccionado para cifrar: {os.path.basename(ruta_original)}", "INPUT")
            
            ruta_privada = filedialog.askopenfilename(title="Tu Clave Privada (Para FIRMAR)", filetypes=[("PEM", "*.pem")])
            if not ruta_privada: return
            pass_privada = simpledialog.askstring("Contraseña", "Contraseña:", show="*")
            if not pass_privada: return
            
            self.app.contactos = api_cliente.obtener_contactos(self.app.token)
            dialogo = DialogoSeleccionReceptores(self.master, self.app.contactos, self.app.uuid_usuario)
            destinatarios = dialogo.receptores_seleccionados
            if not destinatarios: return

            # Auto-add self
            yo = next((c for c in self.app.contactos if c["uuid"] == self.app.uuid_usuario), None)
            if yo and yo not in destinatarios: destinatarios.append(yo)

            self.app.loguear("Iniciando Cifrado Híbrido...", "START")
            
            ruta_zip, meta = logica_cifrado.crear_paquete_cifrado(
                ruta_original, ruta_privada, pass_privada, self.app.uuid_usuario, destinatarios,
                log_callback=self.app.loguear
            )
            
            api_cliente.subir_documento_cifrado(self.app.token, ruta_zip, meta["nombre_original"], meta["deks_cifradas"])
            
            if os.path.exists(ruta_zip): os.remove(ruta_zip)
            self.app.mostrar_exito("Archivo cifrado y subido.")
            self.app.loguear("Subida finalizada.", "DONE")
            self.refrescar_bandeja()
            
        except Exception as e:
            self.app.mostrar_error(f"Error: {e}")
            self.app.loguear(f"Error: {e}", "FAIL")