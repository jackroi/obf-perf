from typing import Dict, List

import matplotlib.pyplot as plt


def violin_plot(data_dict: Dict[str, List[float]], title: str, out_filename: str):
    labels = list(data_dict.keys())
    data = [ curr_data for curr_data in data_dict.values() ]

    _, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 10))
    ax.violinplot(data,
                  showmeans=True,
                  showmedians=True)
    ax.set_title(title)
    ax.set_xticks(range(1, len(labels)+1), labels)

    plt.savefig(out_filename)
