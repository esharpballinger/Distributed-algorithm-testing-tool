from math import log2

if __name__ == "__main__":
    with open('src/graph_kmw_1000.txt') as f:
        n = int(f.readline())
        kmw_degree = max([len(f.readline().strip().split()) for _ in range(n)])
    print(kmw_degree)
    print(log2(log2(kmw_degree)))
    