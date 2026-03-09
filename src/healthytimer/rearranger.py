from healthytimer.models import TimeUnit, Importance


def calc_frequency(interval, unit):
    unit_days = {
        TimeUnit.DAYS: 1,
        TimeUnit.WEEKS: 7
    }

    frequency = 1 / (interval * unit_days[unit])
    return frequency
