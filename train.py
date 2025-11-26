from ultralytics import YOLO

model = YOLO("yolov8m.pt")

results = model.train(
    data="/Users/alejandrodavila/Documents/Universidad/7mo Semestre/Artificial Vision/Proyecto/data/data.yaml",
    epochs=100,
    lr0=0.001,
    imgsz=640,
    iou=0.5,

    hsv_s=0.2,  #variación de saturación
    hsv_v=0.2,  #variación de brillo
    scale=0.3,
    degrees=10,
    translate=0.05,

    batch=16,
    device="mps",
    workers=2,
    name="test_yolo8m",
    save=True,
    save_period=5,
