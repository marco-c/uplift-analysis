import random
import json

import get_bugs

bugs = get_bugs.__download_bugs('all_bugs', get_bugs.__get_all_bugs_query())

# 380 is the size of the sample needed to get a 95% confidence level with 5% interval for 35815.
bugs_sample = random.sample(bugs, 380)

actual_bugs = get_bugs.__filter_bugs(bugs_sample)

print(str(len(actual_bugs)) + ' identified as actual bugs out of a sample of ' + str(len(bugs_sample)) + ' bugs (the total is ' + str(len(bugs)) + ')')

with open('all_bugs/bugs_to_validate.json', 'w') as f:
    json.dump([{ 'id': bug['id'], 'is_bug': bug in actual_bugs, 'correct': None } for bug in bugs_sample], f)
