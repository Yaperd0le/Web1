from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
import uvicorn
from PIL import Image
from io import BytesIO
import base64
import requests
import matplotlib.pyplot as plt
import numpy as np

app = FastAPI()

# Указываем папку с шаблонами
templates = Jinja2Templates(directory="templates")

# Возвращаем основной обработанный шаблон index.html
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Обрабатываем POST-запрос с данными формы и Captcha
@app.post("/rotate_cross")
async def rotate_cross(request: Request, angle: int = Form(...), resp: str = Form(...), file: UploadFile = File(...)):
    secret_key = "6Le77c4pAAAAACpowdtBWUBMmK1Wpw61jgW_hphO"  # Замените на ваш секретный ключ
    # Подготавливаем секретный ключ и ответ, полученный от браузера со стороны клиента
    payload = {
        "secret": secret_key,
        "response": resp
    }
    # Посылаем POST-запрос на сайт Google для проверки прохождения Captcha
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
    result = response.json()
    if result["success"]:
        # Читаем загруженное изображение
        image_data = await file.read()
        with Image.open(BytesIO(image_data)) as img:
            # Поворачиваем изображение на указанный угол
            rotated_img = img.rotate(angle)

            # Создаем гистограммы для исходного изображения
            original_hist = create_color_histogram(img)
            # Создаем гистограммы для повернутого изображения
            rotated_hist = create_color_histogram(rotated_img)

            # Конвертируем изображения в base64
            rotated_img_base64 = image_to_base64(rotated_img, img.format)

        return templates.TemplateResponse("result.html", {
            "request": request,
            "image": rotated_img_base64,
            "original_hist": original_hist,
            "rotated_hist": rotated_hist
        })
    else:
        # В случае неудачи проверки Captcha возвращаем ошибку 400
        raise HTTPException(status_code=400, detail="Ошибка проверки капчи")

def create_color_histogram(image):
    # Конвертируем изображение в numpy массив
    np_image = np.array(image)
    # Создаем гистограмму для всех цветовых каналов
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ('r', 'g', 'b')
    for i, color in enumerate(colors):
        hist, bins = np.histogram(np_image[..., i], bins=256, range=(0, 256))
        ax.plot(bins[:-1], hist, color=color)
    ax.set_xlim([0, 256])
    ax.set_title('Color Histogram (RGB)')
    ax.set_xlabel('Pixel Intensity')
    ax.set_ylabel('Number of Pixels')

    # Сохраняем гистограмму в буфер
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    # Конвертируем гистограмму в base64
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def image_to_base64(image, format):
    # Создаем байтовый объект для сохранения изображения
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    # Конвертируем байтовый объект в base64
    return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

# Запускаем локальный веб-сервер
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
