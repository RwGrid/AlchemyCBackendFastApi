import datetime as dt_lib
from datetime import datetime as dtm


def return_date(dt):
    year = dt.year
    month = dt.month
    day = dt.day
    return str(year) + '/' + str(month) + '/' + str(day)


def process_date(date):
    year = date.year
    month = date.month
    day = date.day
    hour = 0
    minute = 0
    dt = dt_lib.date(year, month, day)
    tm = dt_lib.time(hour, minute)
    combined = dtm.isoformat(dtm.combine(dt, tm))
    return combined


def main():
    pass


if __name__ == "__main__":
    main()
