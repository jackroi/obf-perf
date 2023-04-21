from typing import Dict, List

import matplotlib.pyplot as plt


# TODO: evenutally remove
def violin_plot(data_dict: Dict[str, List[float]], title: str, out_filename: str):
    labels = list(data_dict.keys())
    data = [ curr_data for curr_data in data_dict.values() ]

    _, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 10))
    ax.violinplot(data,
                  showmeans=False,
                  showmedians=True)
    ax.set_title(title)
    ax.set_xticks(range(1, len(labels)+1), labels)

    plt.savefig(out_filename)

# generate a violin plot with a red line that pass through the averages of the various data
def violin_plot_with_avg(data_dict: Dict[str, List[float]], title: str, out_filename: str):
    labels = list(data_dict.keys())
    data = [ curr_data for curr_data in data_dict.values() ]

    _, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 10))
    ax.violinplot(data,
                  showmeans=False,
                  showmedians=True)
    ax.set_title(title)
    ax.set_xticks(range(1, len(labels)+1), labels)

    # plot the average
    avg_data = [ sum(curr_data) / len(curr_data) for curr_data in data ]
    ax.plot(range(1, len(labels)+1), avg_data, color="red")

    plt.savefig(out_filename)
