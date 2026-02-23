import mesa
import numpy as np
from utils.rounding import proportional_split

class Firm(mesa.Agent):
    """Агент-фирма."""

    def __init__(self, unique_id, model, params):
        super().__init__(unique_id, model)
        self.sector = params['sector']
        self.region_id = params['region_id']
        self.size_dir = params['size_dir']
        self.size_men = params['size_men']
        self.size_worker = params['size_worker']
        self.wage_per_dir = params['wage_per_dir']
        self.wage_per_men = params['wage_per_men']
        self.wage_per_worker = params['wage_per_worker']
        self.balance = params['balance']
        self.revenue = 0
        self.export_share = params.get('export_share', 0.0)

    @property
    def size(self):
        return self.size_dir + self.size_men + self.size_worker

    def step(self):
        # Выплата зарплаты происходит в начале месяца (вызывается из модели)
        pass

    def pay_wages(self):
        """Выплата заработной платы работникам."""
        total_wage = (self.size_dir * self.wage_per_dir +
                      self.size_men * self.wage_per_men +
                      self.size_worker * self.wage_per_worker)

        tax_wage = self.model.config['tax']['tax_wage']
        tax_rate = self.model.config['tax']['rate']

        if tax_wage:
            tax = round(total_wage * tax_rate)
            total_expense = total_wage + tax
        else:
            tax = 0
            total_expense = total_wage

        # Списание со счёта фирмы
        self.model.clearing_house.transfer(self.unique_id, 0, total_expense, is_taxable=False)

        # Получаем работников
        workers = self.model.get_workers_of_firm(self.unique_id)
        # Разделяем по категориям (нужно знать, кто есть кто)
        # В модели у каждого работника есть employer_id, но нет категории в явном виде.
        # Для простоты будем считать, что все работники имеют category='worker'.
        # В реальности нужно хранить соответствие.
        # Пока раздадим зарплату поровну между всеми работниками (упрощение)
        # Но лучше иметь распределение по категориям, как обсуждалось.
        # Для этого нужно при создании домохозяйств назначать им категорию и зарплату.
        # Оставим этот момент на доработку. Пока просто разделим общую сумму между всеми работниками.

        if workers:
            # Простое равномерное распределение (упрощение)
            amount_per_worker = total_wage // len(workers)
            remainder = total_wage % len(workers)
            for i, worker in enumerate(workers):
                amt = amount_per_worker + (1 if i < remainder else 0)
                self.model.clearing_house.transfer(0, worker.unique_id, amt, is_taxable=False)
                worker.income_labor += amt
        else:
            # Если нет работников, деньги остаются у фирмы (не должно быть)
            self.model.clearing_house.transfer(0, self.unique_id, total_wage, is_taxable=False)

        if tax > 0:
            self.model.clearing_house.transfer(0, 1, tax, is_taxable=False)  # налоговая

    def receive_revenue(self, amount):
        """Получение выручки от продаж."""
        self.model.clearing_house.transfer(0, self.unique_id, amount, is_taxable=False)
        self.revenue += amount
        self.balance = self.model.clearing_house.accounts.get(self.unique_id, 0)

    def receive_export(self, amount):
        """Получение экспортной выручки (с налогом)."""
        # Приходит сумма, включающая налог
        tax_rate = self.model.config['tax']['rate']
        # Налог, который нужно выделить
        tax = round(amount * tax_rate / (1 + tax_rate))
        net = amount - tax
        self.model.clearing_house.transfer(5, self.unique_id, net, is_taxable=False)
        self.model.clearing_house.transfer(5, 1, tax, is_taxable=False)
        self.revenue += net
        self.balance = self.model.clearing_house.accounts.get(self.unique_id, 0)