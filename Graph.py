import matplotlib.pyplot as plt
from ast import literal_eval as le

with open('data.txt', 'r', encoding='utf-8') as file:
    data = le(file.read())

names = list(data.keys())
values = list(data.values())

fig, ax = plt.subplots()
ax.plot(names, values)
plt.show()
