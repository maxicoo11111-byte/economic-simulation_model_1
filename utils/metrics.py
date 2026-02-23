import csv
import numpy as np

class MetricsCollector:
    """Сбор метрик в процессе симуляции."""
    def __init__(self, model):
        self.model = model
        self.data = []

    def collect(self, step):
        """Сбор метрик за текущий шаг."""
        # Доходы домохозяйств
        incomes = [hh.income_labor + hh.income_transfer for hh in self.model.households]
        savings = [hh.savings for hh in self.model.households]
        # Долги
        hh_debt = sum(-s for s in savings if s < 0)
        firm_debt = sum(-f.balance for f in self.model.firms if f.balance < 0)
        # ВВП (упрощённо: сумма всех зарплат + прибыль фирм)
        total_wages = sum(hh.income_labor for hh in self.model.households)
        total_profits = sum(f.revenue - (f.size_dir*f.wage_per_dir + f.size_men*f.wage_per_men + f.size_worker*f.wage_per_worker) for f in self.model.firms)
        gdp = total_wages + total_profits

        # Банковские показатели
        bank = self.model.central_bank
        bank.update_stats()

        metrics = {
            'step': step,
            'gdp': gdp,
            'total_tax': self.model.tax_service.tax_collected,  # до перевода в Минфин
            'export': sum(f.revenue * f.export_share for f in self.model.firms if f.sector == 3),
            'import': self.model.foreign_sector.balance,  # не совсем точно, но для оценки
            'avg_wage': np.mean([hh.income_labor for hh in self.model.households if hh.income_labor > 0]),
            'unemployment': len([hh for hh in self.model.households if hh.employer_id == 3]) / len(self.model.households),
            'gini_income': self.gini(incomes),
            'gini_wealth': self.gini(savings),
            'hh_debt': hh_debt,
            'firm_debt': firm_debt,
            'bank_capital': bank.capital,
            'bank_loans': bank.total_loans,
            'bank_deposits': bank.total_deposits,
            'capital_adequacy': bank.get_capital_adequacy(),
        }
        self.data.append(metrics)

    def gini(self, x):
        """Коэффициент Джини."""
        x = np.array(x)
        if np.sum(x) == 0:
            return 0
        x = np.sort(x)
        n = len(x)
        cum = np.cumsum(x)
        return (n + 1 - 2 * np.sum(cum) / cum[-1]) / n

    def save(self, path):
        """Сохраняет метрики в CSV."""
        if not self.data:
            return
        keys = self.data[0].keys()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.data)