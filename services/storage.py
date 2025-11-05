"""Модуль для хранения данных пользователей."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


STORAGE_FILE = Path("User_Data.json")


def load_user(user_id: int) -> dict:
    """
    Загружает данные пользователя из файла.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Словарь с данными пользователя или пустой словарь, если пользователь не найден
    """
    if not STORAGE_FILE.exists():
        return {}
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        user_id_str = str(user_id)
        return data.get(user_id_str, {})
    except (json.JSONDecodeError, IOError, Exception):
        return {}


def save_user(user_id: int, data: dict) -> None:
    """
    Сохраняет данные пользователя в файл.
    
    Args:
        user_id: ID пользователя
        data: Словарь с данными пользователя для сохранения
    """
    # Загружаем все существующие данные
    all_data = {}
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_data = {}
    
    # Обновляем данные конкретного пользователя
    user_id_str = str(user_id)
    all_data[user_id_str] = data
    
    # Сохраняем обратно в файл
    try:
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass  # Игнорируем ошибки записи


def load_all_users() -> dict:
    """
    Загружает данные всех пользователей из файла.
    
    Returns:
        dict: Словарь со всеми пользователями
    """
    if not STORAGE_FILE.exists():
        return {}
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, Exception):
        return {}


def delete_user(user_id: int) -> None:
    """
    Удаляет данные пользователя из файла.
    
    Args:
        user_id: ID пользователя
    """
    if not STORAGE_FILE.exists():
        return
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        user_id_str = str(user_id)
        if user_id_str in all_data:
            del all_data[user_id_str]
            
            with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, IOError):
        pass

