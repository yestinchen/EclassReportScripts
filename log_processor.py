from csv_io import CSVTable
from collections import defaultdict
import datetime
import math
import statistics

import matplotlib.pyplot as plt
import numpy as np

import sys
import csv
import os, shutil

def group_by(data, idx):
  grouped = defaultdict(list)
  for tuple in data:
    grouped[tuple[idx]].append(tuple)
  return grouped


def plot_scatter(dur_map, key_mapper=lambda x:x):
  x = np.array(list(map(key_mapper, dur_map.keys())))
  y = np.array(list(dur_map.values()))

  plt.scatter(x, y)
  plt.show()


class CSVLogs(CSVTable):
  def __init__(self, file_path):
    super().__init__(file_path)
    # parse data. 
    self.data = []
    for tuple in self.tuples:
      self.data.append([datetime.datetime.strptime(tuple[0], '%d/%m/%y, %H:%M'),
       *tuple[1:]])

  def group_by(self, column):
    idx = self.head.index(column)
    if idx < 0:
      return 
    return group_by(self.data, idx)

  def report_per_student(self, start_time = datetime.datetime(2021,1,11),
   end_time=datetime.datetime(2021,3,7), excludes=[]):
    '''
    result:
    ---
    week_start
      - user 
        - module
          time spent
    '''
    week_dict = self.get_time_statistcs_by_week(start_time, end_time)
    per_student_dict = defaultdict(lambda: defaultdict(dict))
    average_dict = {}
    highest_dict = {}
    median_dict = {}

    # 1. get # of students, get 
    for start_date, user_dict in week_dict.items():
      total_module_duration = defaultdict(lambda: 0)
      highest_per_module = defaultdict(lambda: (0, None))
      time_list_per_module = defaultdict(list)
      total_user_count = 0
      for user, module_dict in user_dict.items():
        if user in excludes:
          # print('excluding', user)
          continue
        total_user_count += 1
        for module, duration in module_dict.items():
          total_module_duration[module] += duration
          time_list_per_module[module].append(duration)
          if duration > highest_per_module[module][0]:
            highest_per_module[module] = (duration, user)
        per_student_dict[start_date][user] = module_dict
      for key in total_module_duration:
        total_module_duration[key] /= total_user_count
      median_per_module = dict()
      for module, duration_list in time_list_per_module.items():
        median_per_module[module] = statistics.median(duration_list)

      average_dict[start_date] = total_module_duration
      highest_dict[start_date] = highest_per_module
      median_dict[start_date] = median_per_module
    return per_student_dict, average_dict, highest_dict, median_dict

  def get_time_statistcs_by_week(self, start_time, end_time):
    '''
    result:
    ---
    start_date
      - user
        - module
          - time list
    '''
    user_dict = self.compute_user_time(start_time, end_time)
    week_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))
    for user, time_dict in user_dict.items():
      for time_key, module_dict in time_dict.items():
        date_object = datetime.datetime.strptime(time_key, '%y-%m-%d')
        week_num = math.floor( (date_object - start_time).days / 7 )
        start_date = start_time + datetime.timedelta(days=week_num*7)
        start_date_key = start_date.strftime('%y-%m-%d')
        # print('start:', start_date_key, time_key, week_num, (date_object - start_time).days)
        for module_key, duration in module_dict.items():
          week_dict[start_date_key][user][module_key] += duration

    return week_dict

  def compute_user_time(self, start_time, end_time):
    time_idx = self.head.index('Time')
    component_idx = self.head.index('Event context')
    user_dict = {}
    for (user, time_tuples) in self.compute_time_span_for_user().items():
      time_dict = defaultdict(lambda: defaultdict(lambda: 0))
      for [dur, row] in time_tuples:
        timestamp = row[time_idx] 
        if (timestamp < start_time) or (timestamp > end_time):
          continue
        date_key = row[time_idx].strftime('%y-%m-%d')
        component_key = row[component_idx]
        # print('component_key', component_key)
        # return
        time_dict[date_key][component_key] += dur
      user_dict[user] = time_dict
    return user_dict

  def compute_time_span_for_user(self):
    user_idx = self.head.index('User full name')
    time_idx = self.head.index('Time')
    ip_idx = self.head.index('IP address')

    user_list = defaultdict(list)

    for user, user_data in group_by(self.data, user_idx).items():
      for ip, user_ip_data in group_by(user_data, ip_idx).items():
        # sort accroding to time.
        user_ip_data.sort(key=lambda x: x[0])
        # compute time span.
        for idx in range(len(user_ip_data) -1):
          spantime = user_ip_data[idx + 1][time_idx] - user_ip_data[idx][time_idx]
          dur = math.ceil(spantime.total_seconds() / 60 )
          if dur == 0:
            continue
          if dur < 10: # 10 minutes.
            user_list[user].append([dur, user_ip_data[idx]])
    return user_list

  def compute_adjacent_duration(self):
    user_idx = self.head.index('User full name')
    time_idx = self.head.index('Time')
    ip_idx = self.head.index('IP address')

    duration_count = defaultdict(lambda: 0)

    for user, user_data in group_by(self.data, user_idx).items():
      for ip, user_ip_data in group_by(user_data, ip_idx).items():
        # sort accroding to time.
        user_ip_data.sort(key=lambda x: x[0])
        # compute time span.
        for idx in range(len(user_ip_data) -1):
          spantime = user_ip_data[idx + 1][time_idx] - user_ip_data[idx][time_idx]
          dur = math.ceil(spantime.total_seconds() / 60 )
          if dur == 0:
            continue
          if dur < 10 * 60:
            duration_count[dur] = duration_count[dur] + 1
    return duration_count

  def compute_hit_time(self):
    time_idx = self.head.index('Time')
    count_map = defaultdict(lambda: 0)
    max_count =0
    for row in self.data:
      dt = row[time_idx]
      minutes = dt.hour * 60 + dt.minute
      count_map[minutes] = count_map[minutes] + 1
      if count_map[minutes] > max_count:
        max_count = count_map[minutes]
        # print('update:', max_count, minutes)
    print('max: ', max_count)
    return count_map

def generate_log_report(input, output, start_time, end_time, force=False,  excludes=[]):
  logs = CSVLogs(input)
  if os.path.exists(output):
    if not force:
      print("please delete existing folder!")
      sys.exit(-1)
    else:
      shutil.rmtree(output)
  os.mkdir(output)
  os.mkdir('{}/students'.format(output))
  per_students, averages, highest, medians = logs.report_per_student(start_time, end_time, excludes)
  for start_date in sorted(per_students.keys()):
    # week, module, time spent, average, highest
    for student in per_students[start_date].keys():
      student_file_path = '{}/students/{}.csv'.format(output, student)
      if os.path.exists(student_file_path):
        mode = 'a'
      else:
        mode = 'w'
      with open(student_file_path, mode, encoding='utf-8-sig') as f:
        if mode == 'w':
          f.write("week, module, time spent (m), class average (m), highest per module(m), median(m)\n")
        else:
          # spliter
          f.write('\n')
        csvwriter = csv.writer(f, delimiter=',',
                              quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # construct rows
        for module in averages[start_date].keys():
          row = [start_date, module, per_students[start_date][student][module], 
                  round(averages[start_date][module], 2), highest[start_date][module][0], medians[start_date][module]]
          csvwriter.writerow(row)
    highest_file_path = '{}/summary.csv'.format(output)
    if os.path.exists(highest_file_path):
      mode = 'a'
    else:
      mode = 'w'
    with open(highest_file_path, mode, encoding='utf-8-sig') as f:
      if mode == 'w':
        f.write('week, module, average (m), highest (m), student with highest time, median(m)\n')
      else:
        f.write('\n')
      csvwriter = csv.writer(f, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
      # construct rows
      for module, pair in highest[start_date].items():
        csvwriter.writerow([start_date, module, round(averages[start_date][module],2), *pair, medians[start_date][module]])

      



def inspect_time(logs):
  user_dict = logs.compute_user_time()
  # print start date.
  earliest_time = datetime.datetime.now()
  most_recent_time = datetime.datetime(2020, 1, 1)
  for (user, time_dict) in user_dict.items():
    for (time_key, module_dict) in time_dict.items():
      # print('time,key', time_key)
      date_object = datetime.datetime.strptime(time_key, '%y-%m-%d')
      if earliest_time > date_object:
        earliest_time = date_object
      if most_recent_time < date_object:
        most_recent_time = date_object
  print('start time: {}'.format(earliest_time.strftime('%y-%m-%d')))
  print('end time: {}'.format(most_recent_time.strftime('%y-%m-%d')))


if __name__=='__main__':
  generate_log_report('./final/data/logs/exported_log.csv', 
    './final/data/log_report', force=True, 
    start_time = datetime.datetime(2021,1,11),
    end_time=datetime.datetime(2021,4,18),
    excludes=['-']
  )

