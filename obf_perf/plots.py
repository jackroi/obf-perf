import matplotlib.pyplot as plt
import numpy as np


def violin_plot():
    all_data = [np.random.normal(0, std, 100) for std in range(6, 10)]

    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(9, 4))
    # plot violin plot
    axs[0].violinplot(all_data,
                      showmeans=True,
                      showmedians=True)
    axs[0].set_title('Violin plot')

    # plot box plot
    axs[1].boxplot(all_data)
    axs[1].set_title('Box plot')

    plt.savefig("test.png")


violin_plot()
