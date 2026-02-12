import subprocess
import sys

def install_requirements():
    # Список необходимых библиотек
    packages = [
        "gigachat",
        "fastapi",
        "uvicorn",
        "pydantic"
    ]
    
    print("--- Проверка и установка необходимых библиотек ---")
    try:
        # Запуск pip install для списка пакетов
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + packages)
        print("--- Все библиотеки успешно установлены ---\n")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке библиотек: {e}")

if __name__ == "__main__":
    install_requirements()