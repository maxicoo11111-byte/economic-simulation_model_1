import mesa
from utils.rounding import proportional_split

class TaxService(mesa.Agent):
    """Налоговая служба — аккумулирует налоги."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.tax_collected = 0

    def step(self):
        # В конце месяца передаём налоги в Минфин
        if self.tax_collected > 0:
            self.model.clearing_house.transfer(self.unique_id, 2, self.tax_collected, is_taxable=False)
            self.tax_collected = 0

    def receive_tax(self, amount):
        self.tax_collected += amount


class MinistryOfFinance(mesa.Agent):
    """Министерство финансов — распределяет бюджет."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.budget = 0
        self.reserve_fund = 0

    def step(self):
        # Распределение бюджета происходит после поступления налогов (вызывается вручную из модели)
        pass

    def distribute(self):
        """Распределение бюджета по регионам, федеральным закупкам и резерв."""
        X = self.model.config['government']['X']
        Y = self.model.config['government']['Y']
        Z = self.model.config['government']['Z']

        total = self.budget
        to_regions = round(total * X)
        to_fed_proc = round(total * Y)
        reserve = total - to_regions - to_fed_proc  # остаток

        # Трансферты регионам
        # Веса регионов по населению
        populations = [len(self.model.get_households_in_region(r.region_id)) for r in self.model.regions]
        region_amounts = proportional_split(to_regions, populations)
        for region, amount in zip(self.model.regions, region_amounts):
            self.model.clearing_house.transfer(self.unique_id, region.unique_id, amount, is_taxable=False)

        # Федеральные госзакупки
        if to_fed_proc > 0:
            # Выбираем фирмы пропорционально размеру
            firms = self.model.firms
            weights = [f.size for f in firms]
            fed_proc_amounts = proportional_split(to_fed_proc, weights)
            for firm, amount in zip(firms, fed_proc_amounts):
                if amount > 0:
                    # Государство покупает у фирмы (платит цену + налог)
                    self.model.clearing_house.transfer(
                        self.unique_id,
                        firm.unique_id,
                        amount,
                        is_taxable=True,
                        tax_rate=self.model.config['tax']['rate']
                    )

        # Резерв
        self.reserve_fund += reserve
        self.budget = 0


class Region(mesa.Agent):
    """Регион (федеральный округ)."""
    def __init__(self, unique_id, model, config):
        super().__init__(unique_id, model)
        self.social_budget = 0
        self.procurement_budget = 0
        self.poverty_line = config.get('poverty_line', 16000)

    def step(self):
        # В начале месяца регион получает трансферты из Минфина
        pass

    def receive_transfer(self, amount):
        """Получение трансферта из Минфина."""
        self.model.clearing_house.transfer(0, self.unique_id, amount, is_taxable=False)
        # Делим на социальную часть и закупки
        social_share = self.model.config['government']['region_social_share']
        self.social_budget = round(amount * social_share)
        self.procurement_budget = amount - self.social_budget

    def distribute_social(self):
        """Распределение социальных выплат домохозяйствам региона."""
        households = self.model.get_households_in_region(self.unique_id)
        # Сначала категориальные выплаты
        for hh in households:
            if hh.category == 'disabled':
                amt = self.model.config['social']['disability_allowance']
                if self.social_budget >= amt:
                    self.model.clearing_house.transfer(self.unique_id, hh.unique_id, amt, is_taxable=False)
                    self.social_budget -= amt
            elif hh.category == 'veteran':
                amt = self.model.config['social']['veteran_allowance']
                if self.social_budget >= amt:
                    self.model.clearing_house.transfer(self.unique_id, hh.unique_id, amt, is_taxable=False)
                    self.social_budget -= amt

        # Затем адресная помощь малоимущим
        poor = [hh for hh in households if (hh.income_labor + hh.income_transfer) < self.poverty_line]
        if poor and self.social_budget > 0:
            deficits = [self.poverty_line - (hh.income_labor + hh.income_transfer) for hh in poor]
            total_deficit = sum(deficits)
            if total_deficit > 0:
                amounts = proportional_split(self.social_budget, [d/total_deficit for d in deficits])
                for hh, amt in zip(poor, amounts):
                    if amt > 0:
                        self.model.clearing_house.transfer(self.unique_id, hh.unique_id, amt, is_taxable=False)
                        self.social_budget -= amt
        # Остаток social_budget можно игнорировать (останется на счету региона)

    def procure(self):
        """Региональные госзакупки."""
        if self.procurement_budget <= 0:
            return
        firms = self.model.get_firms_in_region(self.unique_id)
        if not firms:
            return
        weights = [f.size for f in firms]
        amounts = proportional_split(self.procurement_budget, weights)
        for firm, amt in zip(firms, amounts):
            if amt > 0:
                self.model.clearing_house.transfer(
                    self.unique_id,
                    firm.unique_id,
                    amt,
                    is_taxable=True,
                    tax_rate=self.model.config['tax']['rate']
                )
        self.procurement_budget = 0


class EmploymentExchange(mesa.Agent):
    """Биржа труда — выплачивает пособия безработным."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.benefit_amount = model.config['social']['unemployment_benefit']

    def step(self):
        # Выплата пособий безработным
        unemployed = [hh for hh in self.model.households if hh.employer_id == self.unique_id]
        for hh in unemployed:
            self.model.clearing_house.transfer(self.unique_id, hh.unique_id, self.benefit_amount, is_taxable=False)
            hh.income_transfer += self.benefit_amount