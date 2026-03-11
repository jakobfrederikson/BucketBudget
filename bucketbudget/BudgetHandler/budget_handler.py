from decimal import Decimal
from enum import Enum

class Frequency(Enum):
    WEEKLY = 1
    FORTNIGHTLY = 2
    FOUR_WEEKLY = 3
    MONTHLY = 4
    YEARLY = 5

class MoneyItem():
    __name: str
    __user_id: int
    __amount: Decimal
    __frequency: Frequency

    def __init__(self, name: str, user_id: int, amount: Decimal, frequency: Frequency):
        self.__name = name
        self.__user_id = user_id
        self.__amount = amount
        self.__frequency = frequency

    def get_name(self) -> str:
        return self.__name
    
    def get_amount(self) -> Decimal:
        return Decimal(format(self.__amount, ".2f"))

    def get_frequency(self) -> Frequency:
        return self.__frequency

    def get_user_id(self) -> int:
        return self.__user_id

    def convert_frequency_to(self, new_frequency: Frequency):
        if self.__frequency == new_frequency:
            return
        
        # WEEKLY
        if self.__frequency == Frequency.WEEKLY:
            if new_frequency == Frequency.FORTNIGHTLY:
                self.__amount = Decimal(self.__amount * 2)
            elif new_frequency == Frequency.FOUR_WEEKLY:
                self.__amount = Decimal(self.__amount * 4)
            elif new_frequency == Frequency.MONTHLY:
                self.__amount == Decimal((self.__amount * 52) / 12)
            elif new_frequency == Frequency.YEARLY:
                self.__amount = Decimal(self.__amount * 52)

        # FORTNIGHTLY
        elif self.__frequency == Frequency.FORTNIGHTLY:
            if new_frequency == Frequency.WEEKLY:
                self.__amount = Decimal(self.__amount / 1)
            elif new_frequency == Frequency.FOUR_WEEKLY:
                self.__amount = Decimal(self.__amount * 2)
            elif new_frequency == Frequency.MONTHLY:
                print(f"In budget handler, new amount: {(self.__amount * 26) / 12}")
                self.__amount = Decimal((self.__amount * 26) / 12)
            elif new_frequency == Frequency.YEARLY:
                self.__amount = Decimal(self.__amount * 26)

        # FOUR WEEKLY
        elif self.__frequency == Frequency.FOUR_WEEKLY:
            if new_frequency == Frequency.WEEKLY:
                self.__amount = Decimal(self.__amount / 4)
            elif new_frequency == Frequency.FORTNIGHTLY:
                self.__amount = Decimal(self.__amount / 2)
            elif new_frequency == Frequency.MONTHLY:
                self.__amount = Decimal((self.__amount * 13) / 12)
            elif new_frequency == Frequency.YEARLY:
                self.__amount = Decimal(self.__amount * 13)

        # MONTHLY
        elif self.__frequency == Frequency.MONTHLY:
            if new_frequency == Frequency.WEEKLY:
                self.__amount = Decimal((self.__amount * 12) / 52)
            elif new_frequency == Frequency.FORTNIGHTLY:
                self.__amount = Decimal((self.__amount * 12) / 26)
            elif new_frequency == Frequency.FOUR_WEEKLY:
                self.__amount = Decimal((self.__amount * 12) / 13)
            elif new_frequency == Frequency.YEARLY:
                self.__amount = Decimal(self.__amount * 12)
            
        # YEARLY
        elif self.__frequency == Frequency.YEARLY:
            if new_frequency == Frequency.WEEKLY:
                self.__amount = Decimal(self.__amount / 52)
            elif new_frequency == Frequency.FORTNIGHTLY:
                self.__amount = Decimal(self.__amount / 26)
            elif new_frequency == Frequency.FOUR_WEEKLY:
                self.__amount = Decimal(self.__amount / 13)
            elif new_frequency == Frequency.MONTHLY:
                self.__amount = Decimal(self.__amount / 12)

        self.__frequency = new_frequency


class ExpenseItem(MoneyItem):
    __is_expense_bucket: bool

    def __init__(self, name: str, user_id: int, amount: Decimal, frequency: Frequency, is_expense_bucket: bool):
        super().__init__(name, user_id, amount, frequency)
        self.__is_expense_bucket = is_expense_bucket

    def is_expense_bucket(self) -> bool:
        if self.__is_expense_bucket:
            return True

        return False


class IncomeItem(MoneyItem):
    __is_split_income: bool

    def __init__(self, name: str, user_id: int, amount: Decimal, frequency: Frequency, is_split_income: bool):
        super().__init__(name, user_id, amount, frequency)
        self.__is_split_income = is_split_income

    def is_split_income(self) -> bool:
        if self.__is_split_income:
            return True

        return False