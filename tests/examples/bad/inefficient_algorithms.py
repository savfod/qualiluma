def calculate_statistics(numbers):
    total = 0
    for num in numbers:
        total += num
    
    average = total / len(numbers)
    
    variance_sum = 0
    for num in numbers:
        variance_sum += (num - average) ** 2
    
    variance = variance_sum / len(numbers)
    
    sorted_numbers = []
    for num in numbers:
        sorted_numbers.append(num)
    
    for i in range(len(sorted_numbers)):
        for j in range(i + 1, len(sorted_numbers)):
            if sorted_numbers[i] > sorted_numbers[j]:
                temp = sorted_numbers[i]
                sorted_numbers[i] = sorted_numbers[j]
                sorted_numbers[j] = temp
    
    median = sorted_numbers[len(sorted_numbers) // 2]
    
    return {"mean": average, "variance": variance, "median": median}

def find_maximum(numbers):
    max_val = numbers[0]
    for i in range(1, len(numbers)):
        if numbers[i] > max_val:
            max_val = numbers[i]
    return max_val

def reverse_string(text):
    reversed_text = ""
    for i in range(len(text) - 1, -1, -1):
        reversed_text += text[i]
    return reversed_text

def factorial(n):
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True

def fibonacci(n):
    if n <= 1:
        return n
    a = 0
    b = 1
    for i in range(2, n + 1):
        temp = a + b
        a = b
        b = temp
    return b

def search_list(lst, target):
    for i in range(len(lst)):
        if lst[i] == target:
            return i
    return -1

def count_occurrences(text, char):
    count = 0
    for c in text:
        if c == char:
            count += 1
    return count
