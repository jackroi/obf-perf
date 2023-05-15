"""Module containing functions to generate plots.

Functions:
    violin_plot: Generate a violin plot with the given data.
    violin_plot_with_avg: Generate a violin plot with the given data
        and a red line that passes through the averages of the various
        data.
    grouped_bar_plot: Generate a grouped bar plot with the given data.

Typical usage example:
    import plots

    data_dict = {
        "label1": [1, 2, 3],
        "label2": [4, 5, 6],
        "label3": [7, 8, 9]
    }
    plots.violin_plot_with_avg(data_dict, "Title", "Y label", "out.png")

    data_dict_by_group = {
        "group1": {
            "label1": [1, 2, 3],
            "label2": [4, 5, 6],
            "label3": [7, 8, 9]
        },
        "group2": {
            "label1": [1, 2, 3],
            "label2": [4, 5, 6],
            "label3": [7, 8, 9]
        }
    }
    plots.grouped_bar_plot(data_dict_by_group, "Title", "Y label", "out.png")
"""


from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


def violin_plot(data_dict: Dict[str, List[float]],
                title: str,
                y_label: str,
                out_filename: Optional[str] = None
                ) -> Tuple[plt.Figure, plt.Axes]:
    """Generates a violin plot with the given data.

    Args:
        data_dict: Dictionary mapping labels to lists of data.
        title: Title of the plot.
        y_label: Label of the y axis.
        out_filename: Path of the file where to save the plot.
            Optional, if not provided the plot is not saved.

    Returns:
        The figure and the axis of the plot.
    """

    # extract the labels
    labels = list(data_dict.keys())
    # extract the data (list of lists)
    data = [ curr_data for curr_data in data_dict.values() ]

    # create the plot
    fig, ax = plt.subplots(nrows=1,
                           ncols=1,
                           figsize=(20,10),
                           tight_layout=True)
    ax.violinplot(data,
                  showmeans=False,
                  showmedians=True)

    # customize the plot
    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.set_xticks(range(1, len(labels)+1), labels)

    # save the plot if an output filename is provided
    if out_filename: plt.savefig(out_filename)

    return fig, ax


def violin_plot_with_avg(data_dict: Dict[str, List[float]],
                         title: str,
                         y_label: str,
                         out_filename: Optional[str] = None
                         ) -> Tuple[plt.Figure, plt.Axes]:
    """Generates a violin plot with the given data and a red line that
    passes through the averages of the various data.

    Args:
        data_dict: Dictionary mapping labels to lists of data.
        title: Title of the plot.
        y_label: Label of the y axis.
        out_filename: Path of the file where to save the plot.
            Optional, if not provided the plot is not saved.

    Returns:
        The figure and the axis of the plot.
    """

    # extract the labels and the data
    labels = list(data_dict.keys())
    # extract the data (list of lists)
    data = [ curr_data for curr_data in data_dict.values() ]

    # create the underlying violin plot
    fig, ax = violin_plot(data_dict, title, y_label)

    # compute the averages of the data
    avg_data = [ sum(curr_data) / len(curr_data) for curr_data in data ]
    # plot the average line
    ax.plot(range(1, len(labels)+1), avg_data, color="red")

    # save the plot if an output filename is provided
    if out_filename: plt.savefig(out_filename)

    return fig, ax


def grouped_bar_plot(data_dict_by_group: Dict[str,Dict[str, List[float]]],
                     title: str,
                     y_label: str,
                     out_filename: Optional[str] = None
                     ) -> Tuple[plt.Figure, plt.Axes]:
    """Generates a grouped bar plot with the given data.

    Args:
        data_dict_by_group: Dictionary mapping groups to dictionaries
            mapping labels to lists of data.
            Groups represent the different groups of bars in the plot.
            Labels represent the different bars in each group.
        title: Title of the plot.
        y_label: Label of the y axis.
        out_filename: Path of the file where to save the plot.
            Optional, if not provided the plot is not saved.

    Returns:
        The figure and the axis of the plot.
    """

    # extract the groups and the labels
    groups = list(data_dict_by_group.keys())
    labels = list(data_dict_by_group[groups[0]].keys())

    # compute the means of the data for each label and each group
    data_means_by_label: Dict[str, List[float]] = dict()
    for label in labels:
        # compute the mean of the data for the current label
        # (one for each group)
        data_means = []
        for group in groups:
            # compute the mean of the data for the current group and label
            data = data_dict_by_group[group][label]
            data_means.append(sum(data) / len(data))
        # store the means for the current label
        data_means_by_label[label] = data_means

    # x positions of the groups of bars
    x_coords = list(range(len(groups)))
    # compute the width of each bar
    # 1 / len(labels) would fill the whole space, but we want to leave
    # some space between the groups of bars
    # so 0.8 means that 80% of the space is used for the bars
    bar_width = 0.8 / len(labels)

    fig, ax = plt.subplots(nrows=1,
                           ncols=1,
                           figsize=(20,10),
                           tight_layout=True)

    # plot the bars for each label
    # all the bars for the same label are plotted together
    # in the same position relative to each group
    for i, (label, values) in enumerate(data_means_by_label.items()):
        # compute the offset of the current set of bars
        offset = i * bar_width
        # plot the bars
        # the x position of the bars is shifted by the offset
        rects = ax.bar([ x + offset for x in x_coords ],
                       values,
                       width=bar_width,
                       label=label)
        # add the bar labels over the bars
        ax.bar_label(rects, fmt="{:.3f}", rotation=90, padding=3)

    # customize the plot
    ax.set_title(title)
    ax.set_ylabel(y_label)
    # set the x ticks in the middle of the groups of bars
    ax.set_xticks([ x + bar_width * (len(labels) - 1) / 2 for x in x_coords ],
                  groups,
                  rotation=45)
    # increase by 10% the top limit of the y axis to make the bar labels fit
    _, top_lim = ax.get_ylim()
    ax.set_ylim(top=top_lim + 0.1 * top_lim)
    ax.legend(loc="upper left")

    # save the plot if an output filename is provided
    if out_filename: plt.savefig(out_filename)

    return fig, ax
