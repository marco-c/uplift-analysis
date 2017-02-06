import csv
import locale
from datetime import datetime
import get_bugs
import utils

# The month abbreviation should be in English.
locale.setlocale(locale.LC_TIME, 'C')

if __name__ == '__main__':
    bugs = get_bugs.get_all()
    uplifts = utils.get_uplifts(bugs)

    months = {}

    for uplift in uplifts:
        for channel in utils.uplift_approved_channels(uplift):
            uplift_date = utils.get_uplift_date(uplift, channel)
            key = (uplift_date.strftime('%b %Y'), channel)
            if key not in months:
                months[key] = 0
            months[key] += 1

    with open('uplift_dates.csv', 'w') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(['Month', 'Channel', 'Number_of_uplifts'])
        for (month, channel), number in sorted(months.items(), key=lambda x: datetime.strptime(x[0][0], '%b %Y')):
            csv_writer.writerow([month, channel, number])
