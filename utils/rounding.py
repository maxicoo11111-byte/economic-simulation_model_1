def proportional_split(total: int, weights):
    """
    Распределяет целое число total пропорционально весам weights.
    Возвращает список целых чисел, сумма которых равна total.
    Используется алгоритм наибольшего остатка.
    """
    if not weights or total == 0:
        return [0] * len(weights)
    # Нормализация весов
    total_weight = sum(weights)
    if total_weight == 0:
        return [0] * len(weights)
    norm_weights = [w / total_weight for w in weights]
    ideal = [total * w for w in norm_weights]
    floors = [int(x) for x in ideal]
    remainder = total - sum(floors)
    fractions = [(ideal[i] - floors[i], i) for i in range(len(weights))]
    fractions.sort(reverse=True, key=lambda x: x[0])
    result = floors[:]
    for i in range(remainder):
        idx = fractions[i][1]
        result[idx] += 1
    return result