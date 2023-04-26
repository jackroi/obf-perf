from typing import Dict, List

import matplotlib.pyplot as plt

# TODO: y axis label


# TODO: evenutally remove
def violin_plot(data_dict: Dict[str, List[float]], title: str, out_filename: str):
    labels = list(data_dict.keys())
    data = [ curr_data for curr_data in data_dict.values() ]

    _, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 10), tight_layout=True)
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

    _, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 10), tight_layout=True)
    ax.violinplot(data,
                  showmeans=False,
                  showmedians=True)
    ax.set_title(title)
    ax.set_xticks(range(1, len(labels)+1), labels, rotation=45)

    # plot the average
    avg_data = [ sum(curr_data) / len(curr_data) for curr_data in data ]
    ax.plot(range(1, len(labels)+1), avg_data, color="red")

    plt.savefig(out_filename)

# generate a grouped bar plot with the average of the data
def grouped_bar_plot(data_dict_by_group: Dict[str,Dict[str, List[float]]], title: str, y_label: str, out_filename: str):
    # TODO: format better the numbers over the bars (round them)
    groups = list(data_dict_by_group.keys())
    labels = list(data_dict_by_group[groups[0]].keys())
    data_means_by_label = dict()
    for label in labels:
        data_means = []
        for group in groups:
            data = data_dict_by_group[group][label]
            data_means.append(sum(data) / len(data))
        data_means_by_label[label] = data_means

    xs = list(range(len(groups)))
    width = 0.25
    multiplier = 0

    _, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 10), tight_layout=True)

    for label, values in data_means_by_label.items():
        offset = multiplier * width
        rects = ax.bar([ x + offset for x in xs ],
                       values,
                       width=width,
                       label=label)
        ax.bar_label(rects, fmt="{:.3f}", padding=3)
        multiplier += 1

    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.set_xticks([ x + width for x in xs ], groups, rotation=45)
    ax.legend()

    plt.savefig(out_filename)
