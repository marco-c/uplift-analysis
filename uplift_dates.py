import csv
from datetime import datetime, timedelta
from dateutil import relativedelta
from libmozdata.utils import as_utc
import get_bugs
import utils

if __name__ == '__main__':
    bugs = get_bugs.get_all()
    uplifts = utils.get_uplifts(bugs)

    months = {}

    for uplift in uplifts:
        for channel in utils.uplift_approved_channels(uplift):
            diff = relativedelta.relativedelta(utils.get_uplift_date(uplift, channel), as_utc(datetime(2014, 7, 22)))
            month = str(diff.years * 12 + diff.months)
            key = (month, channel)
            if key not in months:
                months[key] = 0
            months[key] += 1

    with open('uplift_dates.csv', 'w') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(['month', 'channel', 'number_of_uplifts'])
        for (month, channel), number in sorted(months.items(), lambda x, y: int(x[0][0]) - int(y[0][0])):
            csv_writer.writerow([month, channel, number])
