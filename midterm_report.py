import os, logging
from collections import defaultdict
from grade_road_test import RoadTestGrader
import csv

def generate_RT_report_str(correct, total, digit_num=1):
  # round?
  correct = round(correct, digit_num)
  # format str: {:.?f} correct\n{:.?f} wrong
  return ('{:.'+str(digit_num)+'f} correct\n{:.'+str(digit_num)+'f} wrong')\
    .format(correct, total-correct)

def compute_indexed_result(submission, answer, k):
  grading_result = RoadTestGrader().grade(submission, answer)
  # find student name
  name_idx = grading_result.find_column('Username')

  average = grading_result.average()
  topk_average = grading_result.topk_average(k)

  indexed = dict()
  max_score = grading_result.max
  for row in grading_result.data[1:]:
    indexed[row[name_idx]] = generate_RT_report_str(row[-1], max_score)

  return (indexed, generate_RT_report_str(average, max_score),
      generate_RT_report_str(topk_average, max_score))

class RTReport:
  def __init__(self, k):
    self.k = k
    self.list =[]

  def register(self, name, submission, answer):
    logging.info('registering report, name {}, submission: {}, with {}'\
      .format(name, submission, answer))
    self.list.append([name, submission, answer])

  def save_to(self, output):
    indexed = defaultdict(dict)
    average_indexed = dict()
    # 
    for task in self.list:
      res = compute_indexed_result(task[1], task[2], self.k)
      for (student, col) in res[0].items():
        indexed[student][task[0]] = col
      average_indexed[task[0]] = res[1:]

    # produce result.
    if not os.path.exists(output):
      os.makedirs(output)
    for (student, items) in indexed.items():
      with open( os.path.join(output, '{}.csv'.format(student)), mode='w', 
        encoding='utf-8-sig') as f:
        csvwriter = csv.writer(f, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(['Test Name', 'Your Performance', 'Class Average', 'Top 5 Students'])
        for [test_name,*_] in self.list[:]:
          if test_name not in items:
            csvwriter.writerow([test_name, 'No Submission', *average_indexed[test_name]])
          else:
            csvwriter.writerow([test_name, col, *average_indexed[test_name]])
      


def generate_roadtest_report(tests, output, base_path='', k=5):
  reporter = RTReport(k)
  extra_path = len(base_path) > 0
  for test in tests:
    submission = os.path.join(base_path, test[1]) if extra_path else test[1]
    answer = os.path.join(base_path, test[2]) if extra_path else test[2]
    reporter.register(test[0], submission, answer)
  if extra_path:
    output = os.path.join(base_path, output)

  reporter.save_to(output)


if __name__ == '__main__':
  print('generating report...')
  tests = [
    ['Road Test 2', 'raw/Road_test_2.csv', 'answer/RT2.csv'], 
  ]
  generate_roadtest_report(tests, 'rt_report', 'midterm/data/')
