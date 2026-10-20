def evaluate(models, X_train, y_train, X_test, y_test):
    """
    Обучает модели и собирает метрики на тестовой выборке.
    """
    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        residuals = y_test - predicted
        mse = float((residuals ** 2).mean())
        mae = float(abs(residuals).mean())
        total = float(((y_test - y_test.mean()) ** 2).sum())
        r2 = 1.0 - float((residuals ** 2).sum()) / total
        results[name] = {'mse': mse, 'mae': mae, 'r2': r2}
    return results


def best(results, metric='r2'):
    """
    Имя модели с лучшим значением метрики (для ошибок — наименьшим).
    """
    lower_is_better = metric in ('mse', 'mae')
    key = lambda name: results[name][metric]
    return min(results, key=key) if lower_is_better else max(results, key=key)


def report(results):
    lines = []
    for name, metrics in sorted(results.items(), key=lambda item: -item[1]['r2']):
        lines.append(f"{name:<12} MSE={metrics['mse']:8.3f} MAE={metrics['mae']:7.3f} R2={metrics['r2']:6.3f}")
    return '\n'.join(lines)


if __name__ == '__main__':
    from sklearn.datasets import load_diabetes
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeRegressor

    X, y = load_diabetes(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    models = {
        'linear': LinearRegression(),
        'tree': DecisionTreeRegressor(max_depth=4, random_state=0),
        'forest': RandomForestRegressor(n_estimators=100, random_state=0),
    }
    scores = evaluate(models, X_train, y_train, X_test, y_test)
    print(report(scores))
    print('Лучшая модель:', best(scores))
