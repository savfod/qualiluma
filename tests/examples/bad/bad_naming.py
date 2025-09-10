def process_data(x):
    temp = x * 2
    temp2 = temp + 5
    result = temp2 / 3
    return result

class Calculator:
    def __init__(self):
        self.v = 0
        self.cnt = 0
    
    def do_calc(self, n):
        self.v += n
        self.cnt += 1
        return self.v / self.cnt

def f(a, b, c):
    d = a + b
    e = d * c
    return e

GLOBAL_VAR = 100

def use_global():
    global GLOBAL_VAR
    GLOBAL_VAR = GLOBAL_VAR + 1
    return GLOBAL_VAR

def process_list(lst):
    new_lst = []
    for item in lst:
        processed_item = item * 2
        new_lst.append(processed_item)
    return new_lst

class data_handler:
    def __init__(self, Data):
        self.Data = Data
        self.processed_data = None
    
    def ProcessData(self):
        self.processed_data = [x * 2 for x in self.Data]
    
    def GetResult(self):
        return self.processed_data
