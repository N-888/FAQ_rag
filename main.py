# -*- coding: utf-8 -*-
"""
Основной модуль проекта FAQ RAG
Предоставляет утилиты для работы с базой знаний
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """
    Класс для управления конфигурацией проекта
    Загружает переменные окружения и предоставляет доступ к настройкам
    """

    def __init__(self):
        """
        Инициализация конфигурации
        Загружает переменные окружения из файла .env
        """
        logger.info("Инициализация конфигурации проекта")
        self._load_env()

    def _load_env(self) -> None:
        """
        Загрузка переменных окружения из файла .env
        Если файл не найден, используются переменные окружения системы
        """
        try:
            # Пытаемся импортировать python-dotenv
            from dotenv import load_dotenv
            # Ищем файл .env в корне проекта
            env_path = Path(__file__).parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Переменные окружения загружены из {env_path}")
            else:
                logger.warning(f"Файл .env не найден: {env_path}")
        except ImportError:
            logger.warning("python-dotenv не установлен, используем переменные окружения системы")

    @property
    def gigachat_auth_key(self) -> Optional[str]:
        """
        Получение ключа авторизации GigaChat

        Returns:
            str или None: Ключ авторизации или None, если не задан
        """
        key = os.getenv('GIGACHAT_AUTH_KEY')
        if not key:
            logger.error("Переменная GIGACHAT_AUTH_KEY не задана")
        return key

    @property
    def qdrant_endpoint(self) -> Optional[str]:
        """
        Получение адреса кластера Qdrant

        Returns:
            str или None: Адрес кластера или None, если не задан
        """
        endpoint = os.getenv('QDRANT_ENDPOINT')
        if not endpoint:
            logger.error("Переменная QDRANT_ENDPOINT не задана")
        return endpoint

    @property
    def qdrant_collection(self) -> str:
        """
        Получение названия коллекции Qdrant

        Returns:
            str: Название коллекции (по умолчанию 'faq_documents')
        """
        return os.getenv('QDRANT_COLLECTION', 'faq_documents')

    @property
    def qdrant_api_key(self) -> Optional[str]:
        """
        Получение API-ключа Qdrant

        Returns:
            str или None: API-ключ или None, если не задан
        """
        key = os.getenv('QDRANT_API_KEY')
        if not key:
            logger.error("Переменная QDRANT_API_KEY не задана")
        return key

    def validate(self) -> bool:
        """
        Проверка заполненности всех необходимых переменных

        Returns:
            bool: True, если все переменные заданы, иначе False
        """
        required_vars = [
            ('GIGACHAT_AUTH_KEY', self.gigachat_auth_key),
            ('QDRANT_ENDPOINT', self.qdrant_endpoint),
            ('QDRANT_API_KEY', self.qdrant_api_key)
        ]

        all_valid = True
        for var_name, var_value in required_vars:
            if not var_value:
                logger.error(f"Отсутствует обязательная переменная: {var_name}")
                all_valid = False

        if all_valid:
            logger.info("Все переменные окружения корректны")

        return all_valid


class FileManager:
    """
    Драйвер для работы с файловой системой
    Предоставляет методы для чтения и записи файлов
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Инициализация менеджера файлов

        Args:
            base_path: Базовый путь для работы с файлами
                      Если не указан, используется текущая директория
        """
        logger.info("Инициализация менеджера файлов")
        self.base_path = Path(base_path) if base_path else Path.cwd()
        logger.info(f"Базовый путь: {self.base_path}")

    def read_text(self, filename: str) -> Optional[str]:
        """
        Чтение текстового файла

        Args:
            filename: Имя файла для чтения

        Returns:
            str или None: Содержимое файла или None, если файл не найден
        """
        file_path = self.base_path / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Файл успешно прочитан: {file_path}")
            return content
        except FileNotFoundError:
            logger.error(f"Файл не найден: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            return None

    def write_text(self, filename: str, content: str) -> bool:
        """
        Запись текстового файла

        Args:
            filename: Имя файла для записи
            content: Содержимое для записи

        Returns:
            bool: True, если запись успешна, иначе False
        """
        file_path = self.base_path / filename
        try:
            # Создаем директорию, если она не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Файл успешно записан: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка записи файла {file_path}: {e}")
            return False

    def read_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Чтение JSON-файла

        Args:
            filename: Имя JSON-файла для чтения

        Returns:
            dict или None: Содержимое JSON-файла или None, если файл не найден
        """
        file_path = self.base_path / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"JSON-файл успешно прочитан: {file_path}")
            return data
        except FileNotFoundError:
            logger.error(f"JSON-файл не найден: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка чтения JSON-файла {file_path}: {e}")
            return None

    def write_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """
        Запись JSON-файла

        Args:
            filename: Имя JSON-файла для записи
            data: Данные для записи в JSON

        Returns:
            bool: True, если запись успешна, иначе False
        """
        file_path = self.base_path / filename
        try:
            # Создаем директорию, если она не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON-файл успешно записан: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка записи JSON-файла {file_path}: {e}")
            return False

    def list_files(self, pattern: str = "*") -> List[Path]:
        """
        Получение списка файлов по маске

        Args:
            pattern: Маска для поиска файлов (по умолчанию все файлы)

        Returns:
            list: Список найденных файлов
        """
        try:
            files = list(self.base_path.glob(pattern))
            logger.info(f"Найдено файлов: {len(files)} по маске {pattern}")
            return files
        except Exception as e:
            logger.error(f"Ошибка поиска файлов: {e}")
            return []


def main():
    """
    Основная функция проекта
    Демонстрирует работу конфигурации и менеджера файлов
    """
    logger.info("Запуск проекта FAQ RAG")

    # Инициализация конфигурации
    config = Config()

    # Проверка переменных окружения
    if not config.validate():
        logger.error("Проверьте переменные окружения в файле .env")
        return

    # Инициализация менеджера файлов
    file_manager = FileManager()

    # Пример чтения документа
    document = file_manager.read_text('faq_document.txt')
    if document:
        logger.info(f"Документ загружен, длина: {len(document)} символов")
    else:
        logger.warning("Документ не найден")

    logger.info("Проект FAQ RAG готов к работе")


if __name__ == "__main__":
    main()
