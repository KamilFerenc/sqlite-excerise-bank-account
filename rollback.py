import datetime
import pickle
import pytz
import sqlite3

db = sqlite3.connect("accounts.sqlite")
db.execute('CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY NOT NULL, balance INTEGER NOT NULL, '
           'class_object INTEGER NOT NULL)')
db.execute('CREATE TABLE IF NOT EXISTS history (time TIMESTAMP NOT NULL, account TEXT NOT NULL, '
           'amount INTEGER NOT NULL, time_object INTEGER NOT NULL, PRIMARY KEY(time, account))')


class Account:
    """Class which can creates bank account and saves the operations like deposit and withdraw.
    The data is saved in database. Database contains two tables:
    - accounts (with user name and balance)
    - history (time_object (used module pickle), time operation in UTC, account, amount) """

    @staticmethod
    def _current_time():
        time = pytz.utc.localize(datetime.datetime.utcnow())
        time_object = pickle.dumps(time)
        return time, time_object

    def __init__(self, name: str, opening_balance: int = 0):
        cursor = db.execute("SELECT name, balance FROM accounts WHERE (name = ?)", (name,))
        row = cursor.fetchone()
        if row:
            self.name, self._balance = row
            print("{} account already exist, choose different name. Retrieved record for {}."
                  .format(self.name, self.name), end=" ")
        else:
            self.name = name
            self._balance = opening_balance
            cursor.execute("INSERT INTO accounts VALUES (?, ?, ?)", (name, opening_balance, 0))
            cursor.connection.commit()
            print("Account created for {}. ".format(self.name), end="")
        self.show_balance()

    def _save_update(self, amount):
        new_balance = self._balance + amount
        deposit_time, time_object = Account._current_time()

        try:
            db.execute("UPDATE accounts SET balance = ? WHERE name = ?", (new_balance, self.name))
            db.execute("INSERT INTO history VALUES (?, ?, ?, ?)", (deposit_time, self.name, amount, time_object))
        except sqlite3.Error:
            db.rollback()
        else:
            db.commit()
            self._balance = new_balance

    def deposit(self, amount: int) -> float:
        if amount > 0:
            self._save_update(amount)
            print("{:.2f} deposited.".format(amount / 100))
        return self._balance / 100

    def withdraw(self, amount: int) -> float:
        if 0 < amount <= self._balance:
            self._save_update(-amount)
            print("{:.2f} withdraw.".format(amount / 100))
            return amount
        else:
            print("The amount must be greater than 0 and no more than your account balance.")
            return 0.0

    def show_balance(self):
        print("Balance on account {} is {:.2f}.".format(self.name, self._balance / 100))


if __name__ == "__main__":

    while True:
        type_operation = input("Enter what kind operation you would like do: Create account - C, Deposit - D, "
                               "Withdraw - W, Show Balance - S, Quit - Q.").upper()
        if type_operation.upper() == "Q" or type_operation.upper() == "QUIT":
            break

        elif type_operation == "C" or type_operation == "CREATE":
            user_name = input("Enter the name of account.")
            balance = 0
            try:
                balance = int(input("Enter the opening balance (float) or press enter (default balance = 0)."))
            except ValueError:
                print("Opening balance = 0.")
            user = Account(name=user_name, opening_balance=balance*100)
            class_object = pickle.dumps(user)
            db.execute("UPDATE accounts SET class_object =?", (class_object,))

        elif type_operation == "D" or type_operation == "DEPOSIT":
            user = None
            account_name = input("Enter the name of account to record the deposit.")
            try:
                user = db.execute("SELECT class_object FROM accounts WHERE name = ?", (account_name,)).fetchone()[0]
            except TypeError:
                print("{} bank account doesn't exists, process stopped.".format(account_name))

            if user:
                user = pickle.loads(user)
                try:
                    deposit_amount = int(input("Enter the amount to deposit."))
                except ValueError:
                    print("Entered incorrect value you have written {}, it should been integer or float. "
                          "Process stopped.".format(type(account_name)))
                    continue
                user.deposit(amount=deposit_amount)

        else:
            print("Entered incorrect letter.")
            continue
