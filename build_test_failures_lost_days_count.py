import csv


total_aurora = 0
cases_aurora = 0
total_beta = 0
cases_beta = 0

with open('manual_classification/lost_days_testbuild_failures.csv', 'r') as f:
    csv_reader = csv.reader(f)

    for bug, channel, seconds in csv_reader:
        if channel == 'aurora':
            total_aurora += int(seconds)
            cases_aurora += 1
        elif channel == 'beta':
            total_beta += int(seconds)
            cases_beta += 1

print((float(total_aurora) / float(cases_aurora)) / 86400.0)
print((float(total_beta) / float(cases_beta)) / 86400.0)
