import uuid
import random

def generate_unique_budget_name(budget_name):
    budget_name = budget_name.replace(" ", "")
    uuid_string = uuid.uuid1()
    combined = f"{uuid_string}{budget_name}"
    combined_to_chars_list = list(combined)
    random.shuffle(combined_to_chars_list)
    scrambled = ''.join(combined_to_chars_list)
    return scrambled

print(generate_unique_budget_name("My BudGet Name"))

