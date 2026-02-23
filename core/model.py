import mesa
import numpy as np
from agents.household import Household
from agents.firm import Firm
from agents.self_employed import SelfEmployed
from agents.government import TaxService, MinistryOfFinance, Region, EmploymentExchange
from agents.central_bank import CentralBank
from agents.foreign_sector import ForeignSector
from core.clearing_house import ClearingHouse
from core.scheduler import CustomScheduler
from utils.distributions import generate_households, generate_firms, generate_self_employed
from utils.metrics import MetricsCollector

class EconomyModel(mesa.Model):
    """Основной класс модели экономики."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.schedule = CustomScheduler(self)

        # Инициализация клирингового центра (синглтон)
        self.clearing_house = ClearingHouse(self)

        # Создание агентов
        self._create_agents()

        # Инициализация сборщика метрик
        self.metrics = MetricsCollector(self)

        # Установка seed для воспроизводимости
        np.random.seed(config['model']['seed'])
        self.random = np.random

    def _create_agents(self):
        # 1. Налоговая служба (ID = 1)
        self.tax_service = TaxService(1, self)
        self.clearing_house.add_account(1, 0)

        # 2. Министерство финансов (ID = 2)
        self.minfin = MinistryOfFinance(2, self)
        self.clearing_house.add_account(2, 0)

        # 3. Биржа труда (ID = 3)
        self.employment_exchange = EmploymentExchange(3, self)
        self.clearing_house.add_account(3, 0)

        # 4. Центральный банк (ID = 4)
        self.central_bank = CentralBank(4, self, self.config['bank']['initial_capital'])
        self.clearing_house.add_account(4, self.config['bank']['initial_capital'])

        # 5. Внешний мир (ID = 5)
        self.foreign_sector = ForeignSector(5, self)
        self.clearing_house.add_account(5, 0)

        # 6. Регионы (ID = 101..108)
        self.regions = []
        region_config = self.config['government']
        for i in range(8):
            region_id = 101 + i
            region = Region(region_id, self, region_config)
            self.regions.append(region)
            self.clearing_house.add_account(region_id, 0)

        # 7. Домохозяйства
        self.households = []
        hh_data = generate_households(self.config['households'], self)
        for hh in hh_data:
            self.clearing_house.add_account(hh.household_id, hh.savings)
            self.households.append(hh)

        # 8. Фирмы
        self.firms = []
        firm_data = generate_firms(self.config['firms'], self)
        for f in firm_data:
            self.clearing_house.add_account(f.firm_id, f.balance)
            self.firms.append(f)

        # 9. Самозанятые
        self.self_employed = []
        se_data = generate_self_employed(self.config['self_employed'], self)
        for se in se_data:
            self.clearing_house.add_account(se.agent_id, se.savings)
            self.self_employed.append(se)

        # Добавление всех агентов в расписание
        self.schedule.add(self.tax_service)
        self.schedule.add(self.minfin)
        self.schedule.add(self.employment_exchange)
        self.schedule.add(self.central_bank)
        self.schedule.add(self.foreign_sector)
        for r in self.regions:
            self.schedule.add(r)
        for a in self.households + self.firms + self.self_employed:
            self.schedule.add(a)

    def step(self):
        """Один шаг симуляции (1 месяц)."""
        self.schedule.step()
        self.clearing_house.check_invariant(self)
        self.metrics.collect(self.schedule.steps)

    def get_all_domestic_sellers(self):
        """Возвращает список всех внутренних продавцов (фирмы + самозанятые)."""
        return self.firms + self.self_employed

    def get_workers_of_firm(self, firm_id):
        """Возвращает список домохозяйств, работающих в данной фирме."""
        return [hh for hh in self.households if hh.employer_id == firm_id]

    def get_households_in_region(self, region_id):
        return [hh for hh in self.households if hh.region_id == region_id]

    def get_firms_in_region(self, region_id):
        return [f for f in self.firms if f.region_id == region_id]