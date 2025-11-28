import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from ultralytics import YOLO

MODEL_PATH = "../runs/detect/test_yolo8m/weights/best.pt"

DENOMINATIONS = {
    "20_bill": 20, "50_bill": 50, "100_bill": 100, "200_bill": 200, "500_bill": 500,
    "50c_coin": 0.5, "1_coin": 1, "2_coin": 2, "5_coin": 5, "10_coin": 10
}

PRODUCTS = {
    "Refresco": 18,
    "Galletas": 12,
    "Chips": 30,
    "Chocolate": 15,
    "Agua": 10
}

model = YOLO(MODEL_PATH)

# ======= VARIABLES GLOBALES =======
fase = 1
selected_product = None
product_cost = 0

customer_money = 0
change_expected = 0
change_given = 0

paused = False
cap = None
video_path = None


# ================= PANTALLA INICIAL =================
def start_screen():
    """Pantalla inicial de selección."""
    screen = tk.Tk()
    screen.title("Detector de Billetes — Inicio")
    screen.geometry("400x300")

    tk.Label(screen, text="Seleccione el modo de operación", font=("Arial", 16)).pack(pady=30)

    def open_realtime():
        screen.destroy()
        start_main_interface(rt_camera=True)

    def open_video():
        global video_path
        video_path = filedialog.askopenfilename(
            title="Selecciona un video",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if video_path:
            screen.destroy()
            start_main_interface(rt_camera=False, video_file=video_path)

    ttk.Button(screen, text="Detección en tiempo real (Cámara)", command=open_realtime).pack(pady=10)
    ttk.Button(screen, text="Probar con un video", command=open_video).pack(pady=10)

    screen.mainloop()


# ================= INTERFAZ PRINCIPAL =================
def start_main_interface(rt_camera=True, video_file=None):
    global cap, fase, customer_money, change_given

    fase = 1
    customer_money = 0
    change_given = 0

    # Inicializar captura
    if rt_camera:
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(video_file)

    # --------- Ventana principal ---------
    root = tk.Tk()
    root.title("Detector de Billetes - Sistema Completo")
    root.geometry("1280x800")

    root.grid_columnconfigure(0, weight=3)
    root.grid_columnconfigure(1, weight=1)

    # VIDEO
    video_label = tk.Label(root)
    video_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    # PANEL LATERAL
    panel = tk.Frame(root)
    panel.grid(row=0, column=1, padx=15, pady=10, sticky="ns")

    # --------- SELECCIÓN DE PRODUCTO ---------
    tk.Label(panel, text="Selecciona un producto", font=("Arial", 14)).pack(pady=10)

    product_var = tk.StringVar()
    product_menu = ttk.Combobox(panel, textvariable=product_var, values=list(PRODUCTS.keys()))
    product_menu.pack()

    price_label = tk.Label(panel, text="", font=("Arial", 12))
    price_label.pack(pady=5)

    fase_label = tk.Label(panel, text="Fase: 1 - Selecciona el producto", font=("Arial", 13))
    fase_label.pack(pady=15)

    totals_label = tk.Label(panel, text="Total detectado: $0", font=("Arial", 13))
    totals_label.pack(pady=10)

    change_label = tk.Label(panel, text="", font=("Arial", 13))
    change_label.pack(pady=10)

    # ---------------- FUNCIONES ----------------
    def seleccionar_producto():
        global selected_product, product_cost, fase
        if not product_var.get():
            messagebox.showwarning("Error", "Elige un producto primero")
            return

        selected_product = product_var.get()
        product_cost = PRODUCTS[selected_product]
        price_label.config(text=f"Precio: ${product_cost}")

        fase = 2
        fase_label.config(text="Fase: 2 - Entrada de dinero del cliente")

    def avanzar_fase():
        global fase, change_expected

        if fase == 2:
            if customer_money < product_cost:
                messagebox.showwarning("Dinero insuficiente",
                                       "El cliente no dio suficiente dinero para comprar el producto.")
                return

            change_expected = customer_money - product_cost
            change_label.config(text=f"Cambio esperado: ${round(change_expected, 2)}")

            fase = 3
            fase_label.config(text="Fase: 3 - Validación del cambio")
            return

        if fase == 3:
            if abs(change_given - change_expected) < 0.01:
                messagebox.showinfo("Venta exitosa", "El cambio dado es correcto.")
            else:
                messagebox.showerror("Error de cambio", "El cambio entregado es incorrecto.")

    def reset_totals():
        global customer_money, change_given
        customer_money = 0
        change_given = 0
        totals_label.config(text="Total detectado: $0")
        change_label.config(text="")

    def toggle_pause():
        global paused
        paused = not paused

    # --------- BOTONES ---------
    ttk.Button(panel, text="Confirmar producto", command=seleccionar_producto).pack(pady=5)
    ttk.Button(panel, text="→ Siguiente Fase", command=avanzar_fase).pack(pady=5)
    ttk.Button(panel, text="Reiniciar totales", command=reset_totals).pack(pady=5)
    ttk.Button(panel, text="⏸ Pausar / Reanudar", command=toggle_pause).pack(pady=5)

    # --------- DETECCIÓN CON TRACKING ---------
    def detectar_billetes(frame):
        global customer_money, change_given, fase

        # TRACKING
        results = model.track(frame, persist=True)

        total = 0

        for r in results:
            boxes = r.boxes

            for box in boxes:
                cls = int(box.cls)
                cls_name = model.names[cls]

                if cls_name in DENOMINATIONS:
                    total += DENOMINATIONS[cls_name]

        if fase == 2:
            customer_money = total
        elif fase == 3:
            change_given = total

        totals_label.config(text=f"Total detectado: ${round(total,2)}")

        # DIBUJAR CAJAS Y ETIQUETAS
        annotated = results[0].plot()
        return annotated

    # --------- LOOP VIDEO ---------
    def update_frame():
        if not paused:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = detectar_billetes(frame)

                imgtk = ImageTk.PhotoImage(image=Image.fromarray(frame))
                video_label.imgtk = imgtk
                video_label.config(image=imgtk)

        video_label.after(10, update_frame)

    update_frame()
    root.mainloop()


# ================= EJECUTAR =================
if __name__ == "__main__":
    start_screen()
