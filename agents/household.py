import mesa
import numpy as np
from utils.rounding import proportional_split

class Household(mesa.Agent):
    """Агент-домохозяйство."""

    def __init__(self, unique_id, model, params):
        super().__init__(unique_id, model)
        # Основные атрибуты
        self.region_id = params['region_id']
        self.employer_id = params['employer_id']  # ID фирмы или биржи труда
        self.category = params.get('category', 'worker')  # worker, pensioner, disabled, veteran, child_family, unemployed
        self.age = params.get('age', 40)
        self.children = params.get('children', 0)
        self.savings = params.get('savings', 0)
        self.consumption_rate = params.get('consumption_rate', 0.8)
        self.income_labor = 0
        self.income_transfer = 0

    def step(self):
        # В этом методе не делаем ничего, так как действия распределены по фазам
        pass

    def receive_wage(self, amount):
        """Получение зарплаты (вызывается из фирмы)."""
        self.model.clearing_house.transfer(0, self.unique_id, amount, is_taxable=False)
        self.income_labor += amount

    def receive_transfer(self, amount):
        """Получение социальных выплат."""
        self.model.clearing_house.transfer(0, self.unique_id, amount, is_taxable=False)
        self.income_transfer += amount

    def consume(self):
        """Принятие решения о потреблении и совершение покупок."""
        # Общий доход за месяц (зарплата + трансферты)
        total_income = self.income_labor + self.income_transfer
        # Сумма потребления (может превышать доход, тогда тратятся сбережения)
        C = round(total_income * self.consumption_rate)

        if C == 0:
            return

        # 1. Импортная часть
        import_share = self.model.config['foreign_trade']['import_share_household']
        C_import = round(C * import_share)
        if C_import > 0:
            self.model.clearing_house.transfer(
                self.unique_id,
                5,  # ForeignSector
                C_import,
                is_taxable=True,
                tax_rate=self.model.config['tax']['rate']
            )

        # 2. Внутренняя часть
        C_domestic = C - C_import
        if C_domestic <= 0:
            return

        # Получаем всех внутренних продавцов (фирмы + самозанятые)
        sellers = self.model.get_all_domestic_sellers()
        if not sellers:
            return

        # Веса пропорциональны размеру (для фирм) или доходу (для самозанятых)
        weights = [s.size for s in sellers]  # size определён у всех продавцов
        # Распределяем C_domestic пропорционально весам
        amounts = proportional_split(C_domestic, weights)

        for seller, amount in zip(sellers, amounts):
            if amount > 0:
                self.model.clearing_house.transfer(
                    self.unique_id,
                    seller.unique_id,
                    amount,
                    is_taxable=True,
                    tax_rate=self.model.config['tax']['rate']
                )

        # После покупок обнуляем доходы (для следующего месяца)
        self.income_labor = 0
        self.income_transfer = 0