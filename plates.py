import re

CHECK_LETTERS = "AZYXUTSRPMLKJHGEDCB"
WEIGHTS = (9, 4, 5, 4, 3, 2)


def is_valid_singapore_plate(plate: str) -> bool:
    match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,3})([A-Z])", plate)
    if match is None:
        return False

    prefix, number, check_letter = match.groups()
    prefix_values = [ord(letter) - ord("A") + 1 for letter in prefix[-2:]]
    if len(prefix_values) == 1:
        prefix_values.insert(0, 0)

    values = prefix_values + [int(digit) for digit in number.zfill(4)]
    total = sum(value * weight for value, weight in zip(values, WEIGHTS))
    return check_letter == CHECK_LETTERS[total % 19]