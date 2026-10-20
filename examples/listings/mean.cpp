#include <iostream>
#include <vector>

template <typename T>
T mean(const std::vector<T>& values) {
    T sum = 0;
    for (const auto& v : values) sum += v;   // сумма элементов
    return values.empty() ? T{} : sum / static_cast<T>(values.size());
}

int main() {
    std::vector<double> data{1.5, 2.5, 4.0};
    std::cout << "mean = " << mean(data) << '\n';
    return 0;
}
