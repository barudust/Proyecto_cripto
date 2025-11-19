import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, Listbox, Scrollbar, Toplevel, MULTIPLE
import os
import sys

# Importamos módulos lógicos (subiendo un nivel si es necesario)
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
            # No mostrarse a uno mismo en la lista
            if contacto["uuid"] != mi_uuid:
                self.lista_box.insert("end", contacto["nombre"])
                self.indices_map.append(contacto)

        btn_seleccionar = tk.Button(self, text="Seleccionar", command=self.seleccionar, bg="#4CAF50", fg="white")
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

class VentanaPrincipal:
    def __init__(self, master, app_instance):
        self.master = master
        self.app = app_instance
        
        main_frame = tk.Frame(master, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # Cabecera
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill="x", pady=5)
        
        rol_txt = " (ADMIN)" if self.app.soy_admin else ""
        color_u = "red" if self.app.soy_admin else "black"
        tk.Label(header_frame, text=f"Usuario: {self.app.nombre_usuario}{rol_txt}", font=("Arial", 14, "bold"), fg=color_u).pack(side="left")
        
        right_header = tk.Frame(header_frame)
        right_header.pack(side="right")

        # Botón ADMIN
        if self.app.soy_admin:
            btn_admin = tk.Button(right_header, text="🛠️ PANEL ADMIN", bg="black", fg="white", command=self.abrir_panel_admin)
            btn_admin.pack(side="left", padx=10)

        btn_refrescar = tk.Button(right_header, text="🔄 Refrescar", command=self.refrescar_bandeja)
        btn_refrescar.pack(side="left", padx=5)

        btn_salir = tk.Button(right_header, text="🚪 Salir", command=self.app.cerrar_sesion, bg="#ffcdd2")
        btn_salir.pack(side="left", padx=5)

        # Botones de Acción
        action_frame = tk.Frame(main_frame, pady=10)
        action_frame.pack(fill="x")
        
        btn_generar_claves = tk.Button(action_frame, text="🔑 Generar/Subir Claves", command=self.generar_y_subir_claves, bg="#e1f5fe")
        btn_generar_claves.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_cifrar = tk.Button(action_frame, text="🔒 Cifrar y Subir Archivo", command=self.ejecutar_cifrado_completo, bg="#e1f5fe")
        btn_cifrar.pack(side="left", padx=5, fill="x", expand=True)

        # Bandeja
        tk.Label(main_frame, text="Bandeja de Entrada (Documentos):", font=("Arial", 12)).pack(anchor="w", pady=(15,0))
        
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        self.lista_documentos = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10, font=("Consolas", 10))
        scrollbar.config(command=self.lista_documentos.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista_documentos.pack(side="left", fill="both", expand=True)
        
        # Descarga
        tk.Label(main_frame, text="Acciones para el documento seleccionado:", font=("Arial", 10, "italic")).pack(anchor="w", pady=(10,5))
        
        botones_descarga_frame = tk.Frame(main_frame)
        botones_descarga_frame.pack(fill="x")
        
        btn_descifrar = tk.Button(botones_descarga_frame, text="📂 Descifrar y Guardar", command=self.accion_solo_descifrar, bg="#fff9c4")
        btn_descifrar.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_verificar = tk.Button(botones_descarga_frame, text="✅ Verificar Firma", command=self.accion_solo_verificar, bg="#c8e6c9")
        btn_verificar.pack(side="left", padx=5, fill="x", expand=True)

        self.refrescar_bandeja()

    def abrir_panel_admin(self):
        try:
            # Actualizamos contactos antes de abrir
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
                autor_nombre = "Desconocido"
                for c in self.app.contactos:
                    if c["uuid"] == doc["propietario_uuid"]:
                        autor_nombre = c["nombre"]
                        break
                texto = f"[{doc['id']}] {doc['nombre_original']} | De: {autor_nombre}"
                self.lista_documentos.insert("end", texto)
        except Exception as e:
            self.app.mostrar_error(str(e))

    def _preparar_datos_documento(self):
        seleccion = self.lista_documentos.curselection()
        if not seleccion: 
            self.app.mostrar_error("Primero selecciona un documento de la lista.")
            return None

        # Validar que no sea el mensaje "(No tienes documentos)"
        if not self.app.documentos_en_lista:
             return None

        doc_info = self.app.documentos_en_lista[seleccion[0]]
        doc_id = doc_info["id"]
        
        ruta_privada = filedialog.askopenfilename(title="Selecciona tu Clave Privada (.pem)", filetypes=[("PEM files", "*.pem")])
        if not ruta_privada: return None
        
        pass_privada = simpledialog.askstring("Contraseña", "Contraseña de tu clave privada:", show="*")
        if not pass_privada: return None

        try:
            self.app.mostrar_exito("Procesando... Espere.")
            zip_bytes = api_cliente.descargar_documento_zip(self.app.token, doc_id)
            
            plaintext, firma_bytes, autor_uuid = logica_descifrado.descifrar_contenido(
                zip_bytes=zip_bytes,
                mi_uuid=self.app.uuid_usuario,
                ruta_clave_privada=ruta_privada,
                password_clave_privada=pass_privada
            )
            return (plaintext, firma_bytes, autor_uuid, doc_info['nombre_original'])
            
        except Exception as e:
            self.app.mostrar_error(f"Error en el proceso: {e}")
            return None

    def accion_solo_descifrar(self):
        datos = self._preparar_datos_documento()
        if not datos: return
        
        plaintext, _, _, nombre_orig = datos
        
        ruta_guardado = filedialog.asksaveasfilename(title="Guardar Archivo", initialfile=f"DESCIFRADO_{nombre_orig}")
        if not ruta_guardado: return
        
        try:
            with open(ruta_guardado, "wb") as f: f.write(plaintext)
            self.app.mostrar_exito(f"Archivo guardado correctamente en:\n{ruta_guardado}")
        except Exception as e:
            self.app.mostrar_error(f"Error al guardar: {e}")

    def accion_solo_verificar(self):
        datos = self._preparar_datos_documento()
        if not datos: return
        
        plaintext, firma_bytes, autor_uuid_zip, _ = datos
        
        clave_autor = None
        nombre_autor = "Desconocido"
        for c in self.app.contactos:
            if c["uuid"] == autor_uuid_zip:
                clave_autor = c["clave_publica"]
                nombre_autor = c["nombre"]
                break
        
        if not clave_autor:
            self.app.mostrar_error(f"No se puede verificar.\nNo tienes la clave pública del autor (UUID: {autor_uuid_zip}).")
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
                nombre_usuario=self.app.nombre_usuario
            )
            
            api_cliente.subir_clave_publica(self.app.token, clave_publica_pem)
            self.app.mostrar_exito(f"¡Claves generadas! Tu clave privada se guardó en:\n{ruta_privada}")
        except Exception as e:
            self.app.mostrar_error(str(e))
            
    def ejecutar_cifrado_completo(self):
        try:
            ruta_original = filedialog.askopenfilename(title="Selecciona un archivo para cifrar")
            if not ruta_original: return
            
            ruta_privada = filedialog.askopenfilename(title="Selecciona TU Clave Privada (.pem) para FIRMAR", filetypes=[("PEM files", "*.pem")])
            if not ruta_privada: return
            
            pass_privada = simpledialog.askstring("Contraseña", "Contraseña de tu clave privada:", show="*")
            if not pass_privada: return
            
            # Actualizar contactos antes de mostrar la lista
            self.app.contactos = api_cliente.obtener_contactos(self.app.token)
            receptores_disponibles = self.app.contactos
            dialogo = DialogoSeleccionReceptores(self.master, receptores_disponibles, self.app.uuid_usuario)
            
            receptores_seleccionados = dialogo.receptores_seleccionados
            if not receptores_seleccionados:
                return 

            # Auto-inclusión (para poder descifrar tus propios archivos)
            mi_contacto = next((c for c in self.app.contactos if c["uuid"] == self.app.uuid_usuario), None)
            if mi_contacto and mi_contacto not in receptores_seleccionados:
                receptores_seleccionados.append(mi_contacto)

            # Validación de claves públicas
            for receptor in receptores_seleccionados:
                if not receptor.get("clave_publica"):
                    self.app.mostrar_error(f"El usuario '{receptor['nombre']}' NO ha generado/subido sus claves todavía.\nNo se puede cifrar para él.")
                    return

            self.app.mostrar_exito("Cifrando y subiendo...")
            
            ruta_zip_temporal, metadata_api = logica_cifrado.crear_paquete_cifrado(
                ruta_archivo_original=ruta_original,
                ruta_clave_privada_autor=ruta_privada,
                password_clave_privada=pass_privada,
                uuid_autor=self.app.uuid_usuario,
                receptores=receptores_seleccionados
            )
            
            api_cliente.subir_documento_cifrado(
                token=self.app.token,
                ruta_archivo_zip=ruta_zip_temporal,
                nombre_original=metadata_api["nombre_original"],
                deks_cifradas=metadata_api["deks_cifradas"]
            )
            
            if os.path.exists(ruta_zip_temporal):
                os.remove(ruta_zip_temporal)
                
            self.app.mostrar_exito(f"¡Archivo '{metadata_api['nombre_original']}' cifrado y subido con éxito!")
            self.refrescar_bandeja()

        except Exception as e:
            self.app.mostrar_error(f"Error en el cifrado: {e}")