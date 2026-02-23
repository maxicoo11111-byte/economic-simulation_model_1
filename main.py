#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import yaml
import random
import numpy as np
from core.model import EconomyModel

def main(config_path, output_path):
    # Загрузка конфигурации
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Установка seed
    seed = config['model'].get('seed', 42)
    random.seed(seed)
    np.random.seed(seed)

    # Создание модели
    model = EconomyModel(config)

    # Запуск симуляции
    for step in range(config['model']['steps']):
        model.step()
        if step % 12 == 0:
            print(f"Шаг {step+1}/{config['model']['steps']} завершён")

    # Сохранение результатов
    model.metrics.save(output_path)
    print(f"Результаты сохранены в {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yaml', help='Путь к файлу конфигурации')
    parser.add_argument('--output', type=str, default='results.csv', help='Путь для сохранения результатов')
    args = parser.parse_args()
    main(args.config, args.output)