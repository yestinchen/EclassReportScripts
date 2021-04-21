import logging
from utils import create_parent_folders
from csv_io import CSVRTSubmissions, CSVRTAnswers, save_csv
import os
import csv
class RoadTestGrader:
  '''
  grade road test
  '''

  def grade(self, submissions, answer):
    '''
    grade all submissions and return the table with grades
    ------
    result: with head: [...other info, ... questions, total(max:?)]
    '''
    submission_table = CSVRTSubmissions(submissions)
    answer_table = CSVRTAnswers(answer)

    # check columns match.

    assert len(submission_table.head) > answer_table.qs[-1], \
      '# of columns not match between submissions [{}] and answer [{}]'.format(len(submission_table.head), answer_table.qs[-1]+1)

    result = []
    # add head.
    first_pos = submission_table.qs[0]
    result.append([*submission_table.head, 'total(max:{})'.format(answer_table.max)])
    for student in submission_table.tuples:
      row = student[:first_pos]
      grade = answer_table.grade(student, first_pos)
      # only count 1s
      result.append([*row,*grade, sum([1 if i =='1' else 0 for i in grade])])
    return RoadTestResult(result, answer_table.max)

class RoadTestResult:
  '''
  holder for the road test results
  '''
  def __init__(self, data, max):
    '''
    ---
    data: first row: head\n...
    '''
    self.data = data
    self.max = max
  
  def find_column(self, name):
    for i,col in enumerate(self.data[0]):
      if col == name:
         return i
    return -1

  def topk(self, k):
    '''
    get topk results.
    '''
    rows = self.data[1:]
    rows.sort(reverse=True, key = lambda x: x[-1])
    return rows[:k]

  def __average(self, rows):
    return sum([i[-1] for i in rows]) / len(rows)

  def average(self):
    '''
    compute average, return tuple: (correct cound, wrong count, total)
    '''
    return self.__average(self.data[1:])

  def topk_average(self, k):
    return self.__average(self.topk(k))

  def save(self, output):
    save_csv(self.data, output)
    return self
  
  def save_summary(self, k, output):
    '''
    save result summary to the output file
    ---
    file format:

    $average\n
    $k\n
    k lines, each line represents one student.
    '''
    avg = self.average()
    kstudents = self.topk(k)
    create_parent_folders(output)
    with open(output, mode='w', encoding='utf-8-sig') as f:
      f.write(str(avg))
      f.write('\n')
      f.write(str(k))
      f.write('\n')
      f.write(str(self.topk_average(k)))
      f.write('\n')
      csvwriter = csv.writer(f, delimiter=',',
                              quotechar='"', quoting=csv.QUOTE_MINIMAL)
      csvwriter.writerows(kstudents)
    return self

def grade_pipeline(submission, answer, output, base_path='', k=5):
  if len(base_path) > 0:
    submission = os.path.join(base_path, submission)
    answer = os.path.join(base_path, answer)
    output = os.path.join(base_path, output)

  logging.info('grading: {}, with {}, to {}'.format(submission, answer, output))
  RoadTestGrader().grade(submission, answer)\
    .save('{}/details.csv'.format(output)).save_summary(k, '{}/summary.txt'.format(output))

if __name__ == '__main__':
  base_path = 'midterm/data/'
  grade_pipeline('raw/Road_test_2.csv', 'answer/RT2.csv', 'graded/RT2', base_path)
