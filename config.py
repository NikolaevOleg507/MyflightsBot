from enum import Enum

token = '1284094110:AAGj4l3KQK_ge3NhNcbaraRUdISdEJE7Br4'
db_file = "database.vdb"
class States(Enum):
    S_START = "0"  # Начало нового диалога
    S_AIRPORT = "1"
    S_VILET_OR_PRILET= "2"
    S_REIS_NUMBER = "3"
    S_GOROD = "4"