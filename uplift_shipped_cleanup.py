import csv


rows = []


all_reproducible = set()
all_how_found = set()


for channel in ['aurora', 'beta', 'release']:
    with open('manual_classification/regressions_shipped_to_users_{}.csv'.format(channel), 'r') as f:
        with open('manual_classification/regressions_shipped_to_users_{}_clean.csv'.format(channel), 'w') as of:
            csv_reader = csv.reader(f)

            csv_writer = csv.writer(of)
            csv_writer.writerow(next(csv_reader))

            for uplift_id, regression_id, reproducible, how_found in csv_reader:
                if reproducible == 'INVALID':
                    continue

                if reproducible == '' and how_found == '':
                    continue

                if how_found in ['found by fuzzing', 'found by static analysis']:
                    how_found = 'found by tooling'
                elif how_found.startswith('found by developer') or how_found in ['found by user (developers embedding JS engine)', 'found by external security researcher']:
                    how_found = 'found by developers'
                elif 'found by user' in how_found or 'found by QA' in how_found:
                    if 'wide' in how_found:
                        how_found = 'found on a widely used feature/website/config'
                    elif 'rare' in how_found:
                        how_found = 'found on a rarely used feature/website/config'
                    else:
                        print(how_found)
                        assert False
                elif how_found in ['found via crash reports', 'found via telemetry']:
                    how_found = 'found via telemetry'
                else:
                    print(how_found)
                    assert False

                all_reproducible.add(reproducible)
                all_how_found.add(how_found)

                csv_writer.writerow([uplift_id, regression_id, reproducible, how_found])


print(all_reproducible)
print(all_how_found)
