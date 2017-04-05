import re

with open('raw_conflicts_beta_fault.txt') as f:
    bug_id = ''
    line_cnt = 0
    reader = f.read().split('\n')
    for line in reader:
        if line.startswith('Difference'):
            bug_id = line.split(' ')[-1]
            line_cnt = 0
        else:
            results = re.findall('\'(.+?)\'', line)
            if line_cnt == 0:
                le_result = '+'.join(results)     # Le's results
            else:
                marco_result = '+'.join(results)     # Marco's results 
            line_cnt += 1
        if line_cnt == 2:
            print '{}\t{}\t{}'.format(bug_id, le_result, marco_result)