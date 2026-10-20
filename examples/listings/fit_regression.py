import numpy as np
from sklearn.linear_model import LinearRegression


def fit(X, y):
    """
    Обучает линейную регрессию и возвращает R^2.
    """
    model = LinearRegression().fit(X, y)
    return model.score(X, y)  # коэффициент детерминации


if __name__ == "__main__":
    X = np.random.rand(100, 3)
    print(f"R2 = {fit(X, X @ [1.0, 2.0, 3.0]):.3f}")
