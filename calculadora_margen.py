import tkinter as tk
from tkinter import messagebox

# Función para calcular margen
def calcular_margen(precio, lote, apalancamiento, tamaño_lote_base=100):
    valor_nominal = precio * lote * tamaño_lote_base
    margen = valor_nominal / apalancamiento
    return valor_nominal, margen

# Función que se ejecuta al presionar el botón
def calcular():
    try:
        precio = float(entry_precio.get())
        lote = float(entry_lote.get())
        apalancamiento = float(entry_apalancamiento.get())
        tamaño_lote_base = float(entry_tamaño_lote_base.get())

        valor_nominal, margen = calcular_margen(precio, lote, apalancamiento, tamaño_lote_base)

        label_resultado.config(
            text=f"📊 Valor nominal: ${valor_nominal:,.2f}\n💰 Margen requerido: ${margen:,.2f}"
        )
    except ValueError:
        messagebox.showerror("Error", "Por favor ingresa valores numéricos válidos")

# Crear ventana principal
root = tk.Tk()
root.title("Calculadora de Margen XM")
root.geometry("400x300")  # Tamaño de la ventana

# Etiquetas y entradas
tk.Label(root, text="Precio actual del activo:").pack()
entry_precio = tk.Entry(root)
entry_precio.pack()

tk.Label(root, text="Tamaño del lote:").pack()
entry_lote = tk.Entry(root)
entry_lote.pack()

tk.Label(root, text="Apalancamiento:").pack()
entry_apalancamiento = tk.Entry(root)
entry_apalancamiento.pack()

tk.Label(root, text="Tamaño base del lote:").pack()
entry_tamaño_lote_base = tk.Entry(root)
entry_tamaño_lote_base.pack()

# Botón para calcular
tk.Button(root, text="Calcular Margen", command=calcular).pack(pady=10)

# Etiqueta para mostrar resultado
label_resultado = tk.Label(root, text="", font=("Arial", 12), fg="blue")
label_resultado.pack()

# Ejecutar la aplicación
root.mainloop()
