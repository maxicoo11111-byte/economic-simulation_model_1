import numpy as np
from agents.household import Household
from agents.firm import Firm
from agents.self_employed import SelfEmployed

def generate_households(config, model):
    """
    Генерирует список домохозяйств на основе конфигурации.
    config: словарь из раздела 'households'
    """
    np.random.seed(model.config['model']['seed'])
    count = config['count']
    unemployment_rate = config['unemployment_rate']
    region_ids = list(range(101, 109))  # 8 регионов
    households = []
    next_id = 1000  # начнём с 1000, чтобы не пересекаться с гос. агентами

    # Распределение по регионам (равномерное)
    region_counts = np.random.multinomial(count, [1/8]*8)

    for reg_idx, reg_count in enumerate(region_counts):
        reg_id = region_ids[reg_idx]
        for _ in range(reg_count):
            # Категории
            category = np.random.choice(
                ['worker', 'pensioner', 'disabled', 'veteran', 'child_family', 'unemployed'],
                p=[0.5, 0.25, 0.03, 0.01, 0.15, 0.06]  # примерно
            )
            # Определяем employer_id
            if category == 'unemployed':
                employer_id = 3  # биржа труда
            else:
                # Позже привяжем к фирме
                employer_id = None  # временно
            # Начальные сбережения (логнормальное)
            savings = max(0, int(np.random.lognormal(
                mean=np.log(config['initial_savings_mean']),
                sigma=config['initial_savings_std']/config['initial_savings_mean']
            )))
            # consumption_rate (нормальное)
            consumption_rate = np.random.normal(config['consumption_rate_mean'], config['consumption_rate_std'])
            consumption_rate = max(0.1, min(2.0, consumption_rate))  # ограничим

            hh_params = {
                'region_id': reg_id,
                'employer_id': employer_id,
                'category': category,
                'age': np.random.randint(18, 80),
                'children': np.random.poisson(0.5) if category in ['child_family', 'worker'] else 0,
                'savings': savings,
                'consumption_rate': consumption_rate,
            }
            hh = Household(next_id, model, hh_params)
            households.append(hh)
            next_id += 1

    # Привязка работников к фирмам (будет позже)
    return households

def generate_firms(config, model):
    """
    Генерирует список фирм.
    config: словарь из раздела 'firms'
    """
    np.random.seed(model.config['model']['seed'])
    count = config['count']
    sector_dist = config['sector_distribution']
    region_ids = list(range(101, 109))
    firms = []
    next_id = 2000  # начнём с 2000

    # Распределение по секторам
    sector_counts = np.random.multinomial(count, sector_dist)

    for sector, sector_count in enumerate(sector_counts, start=1):
        if sector_count == 0:
            continue
        # Распределение по регионам (равномерное)
        reg_counts = np.random.multinomial(sector_count, [1/8]*8)
        for reg_idx, reg_count in enumerate(reg_counts):
            reg_id = region_ids[reg_idx]
            for _ in range(reg_count):
                # Размер фирмы (логнормальное)
                size_mean = config['size_mean']
                size_std = config['size_std']
                size = int(np.random.lognormal(mean=np.log(size_mean), sigma=size_std/size_mean))
                size = max(1, size)
                # Категории работников
                share_dir = config['share_director']
                share_men = config['share_manager']
                size_dir = max(1, int(size * share_dir))
                size_men = max(1, int(size * share_men))
                size_worker = size - size_dir - size_men
                if size_worker < 1:
                    size_worker = 1
                    size_dir = 1
                    size_men = 1

                # Зарплаты
                base_wage = config['wage_base_by_sector'][sector-1]
                wage_per_dir = round(base_wage * config['wage_ratio_director'])
                wage_per_men = round(base_wage * config['wage_ratio_manager'])
                wage_per_worker = base_wage

                # Начальный баланс (несколько месячных зарплат)
                monthly_payroll = (size_dir * wage_per_dir + size_men * wage_per_men + size_worker * wage_per_worker)
                initial_balance = monthly_payroll * config['initial_balance_months']

                firm_params = {
                    'sector': sector,
                    'region_id': reg_id,
                    'size_dir': size_dir,
                    'size_men': size_men,
                    'size_worker': size_worker,
                    'wage_per_dir': wage_per_dir,
                    'wage_per_men': wage_per_men,
                    'wage_per_worker': wage_per_worker,
                    'balance': initial_balance,
                    'export_share': 0.6 if sector == 3 else 0.0,
                }
                firm = Firm(next_id, model, firm_params)
                firms.append(firm)
                next_id += 1
    return firms

def generate_self_employed(config, model):
    """Генерирует самозанятых."""
    np.random.seed(model.config['model']['seed'])
    count = config['count']
    avg_income = config['avg_income']
    region_ids = list(range(101, 109))
    self_employed = []
    next_id = 3000

    reg_counts = np.random.multinomial(count, [1/8]*8)
    for reg_idx, reg_count in enumerate(reg_counts):
        reg_id = region_ids[reg_idx]
        for _ in range(reg_count):
            se_params = {
                'region_id': reg_id,
                'savings': np.random.randint(0, 50000),
                'income': avg_income,
            }
            se = SelfEmployed(next_id, model, se_params)
            self_employed.append(se)
            next_id += 1
    return self_employed