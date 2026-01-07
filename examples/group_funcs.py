from func_to_web import run

def calc_sum(a: int, b: int) -> int:
    return a + b

def calc_multiply(a: int, b: int) -> int:
    return a * b

def text_upper(text: str) -> str:
    return text.upper()

def text_lower(text: str) -> str:
    return text.lower()

def text_reverse(text: str) -> str:
    return text[::-1]

def text_length(text: str) -> int:
    return len(text)

def text_concat(text1: str, text2: str) -> str:
    return text1 + text2


run({
    'Math Operations': [calc_sum, calc_multiply],
    'Text Operations': [text_upper, text_lower, text_reverse, text_length, text_concat]
})