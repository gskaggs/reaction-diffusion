import numpy as np

class Chromosome:
    def __init__(self, F, k):
        self._F = F
        self._k = k

    @property 
    def F(self):
        return self._F

    @property
    def k(self):
        return self._k

    @property
    def fitness(self):
        return self._fitness

    @property
    def image(self):
        return self._image

    @property
    def pattern(self):
        return self._pattern

    def mutate(self):
        self._F += np.random.normal(0, .001)
        self._k += np.random.normal(0, .001)

    def set_pattern(self, pattern):
        self._pattern = pattern

    def set_fitness(self, fitness):
        self._fitness = fitness

    def set_image(self, image):
        self._image = image

    def crossover(self, other):
        loc = np.random.choice([0, 1, 2])
        
        F = other.F if loc == 0 else self.F
        k = self.k if loc == 2 else other.k
        result = Chromosome(F, k)
        result.mutate()

        return result

def apply_fitness_function(chromosomes, type):
    N = len(chromosomes)
    result = [None] * N

    if type == 'default':
        chromosomes.sort(key=lambda c: -c.fitness) # sorted by decreasing fitness
        for i in range(N//2):
            result[i] = chromosomes[i]
            if 2*i >= N:
                break
            result[2*i] = chromosomes[i].crossover(chromosomes[i+1])

    else:
        best = []
        while True:
            try:
                best = map(int, input(f'Top {N//4} performers:').split(' '))
            except:
                print("Input integers please.")
                continue 
            if len(best) != N//4:
                continue
            
            if any(map(lambda x: x < 1 or x > N, best)):
                continue
            
            # 0-index
            best = map(lambda x: x-1, best)

            break
        
        for i in range(N//4):
            result[i] = chromosomes[best[i]]

        for i in range(N//4, N):
            mate1, mate2 = np.random.choice(best, 2)
            result[i] = mate1.crossover(mate2)

    return result