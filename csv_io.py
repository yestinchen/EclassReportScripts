
import logging
import csv
import os
from utils import create_parent_folders

def save_csv(data, output_file):
  create_parent_folders(output_file)
  with open(output_file, mode='w', encoding='utf-8-sig') as f:
    csvwriter = csv.writer(f, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerows(data)

def load_csv(csv_file):
  return CSVTable(csv_file)

class CSVTable:

  def __init__(self, csv_file):
    self.file_path = csv_file
    self._load(csv_file)

  def _load(self, csv_file):
    logging.info("loading file: {} as {}".format(csv_file, self.__class__))
    with open(csv_file, mode='r', encoding='utf-8-sig') as f:
      reader = csv.reader(f.readlines(), quotechar='"', delimiter=',',
                     quoting=csv.QUOTE_ALL, skipinitialspace=True)
      self._update_head(next(reader))
      self.tuples = []
      for row in reader:
        self.tuples.append(row)
  
  def _update_head(self, head):
    self.head = head

class CSVRoadTestTable(CSVTable):
  def _update_head(self, head):
    # calculate Q?
    self.qs = []
    for (i,v) in enumerate(head):
      if v[0] == 'Q':
        self.qs.append(i)
    return super()._update_head(head)

class CSVRTSubmissions(CSVRoadTestTable):
  pass


class CSVRTAnswers(CSVRoadTestTable):
  def __init__(self, csv_file):
    super().__init__(csv_file)
    # allow only one line.
    assert len(self.tuples) == 1, "answer table should contain only one answer"
    for (i, value) in enumerate(self.tuples[0]):
      assert value in ['0', '1', 'N/A'], 'value [{}] at pos [{}] is illegal!'.format(value, i)

    self.answer = self.tuples[0]
    self.max = len(list(filter(self.__need_mark, self.answer)))

  def __need_mark(self, value):
    return value not in ['N/A', '']

  def __grade_cell(self, value, answer):
    if self.__need_mark(answer):
      return '1' if value == answer else '0'
    return 'N/A'

  def grade(self, record, start_pos):
    points = []
    for q in self.qs:
      points.append(self.__grade_cell(record[q+start_pos], self.answer[q]))
    return points
        

__all__ = ['CSVRTAnswers', 'CSVRTSubmissions', 'CSVTable', 'CSVRoadTestTable']

if __name__ == '__main__':

  # set logging
  import utils
  utils.setup_log()
  csv_table = load_csv('./midterm/data/raw/test.csv')
  print(csv_table.head)
