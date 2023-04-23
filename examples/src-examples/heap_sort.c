#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE 100000


void sort(int arr[], int len);
void print_array(int array[], int size);
void init_random_array(int array[], int size);


int main() {
  int array[SIZE];

  srand(time(NULL));   // Initialization, should only be called once.

  init_random_array(array, SIZE);

  print_array(array, SIZE);

  sort(array, SIZE);

  print_array(array, SIZE);

  return 0;
}

void init_random_array(int array[], int size) {
  for (int i = 0; i < size; ++i) {
    int r = rand();      // Returns a pseudo-random integer between 0 and RAND_MAX.
    array[i] = r % 10000;
  }
}

void print_array(int array[], int size) {
  printf("[ ");
  for (int i = 0; i < size; ++i) {
    printf("%d ", array[i]);
  }
  printf("]\n");
}

// heap sort
void sort(int arr[], int len) {
  if (len < 2) {
    return;
  }

  int i, j, k;
  int temp;

  // heapify
  for (i = len / 2 - 1; i >= 0; i--) {
    k = i;
    j = 2 * k + 1;
    temp = arr[k];
    while (j < len) {
      if (j + 1 < len && arr[j] < arr[j + 1]) {
        j++;
      }
      if (arr[j] > temp) {
        arr[k] = arr[j];
        k = j;
        j = 2 * k + 1;
      } else {
        break;
      }
    }
    arr[k] = temp;
  }

  // sort
  for (i = len - 1; i > 0; i--) {
    temp = arr[0];
    arr[0] = arr[i];
    arr[i] = temp;
    k = 0;
    j = 2 * k + 1;
    temp = arr[k];
    while (j < i) {
      if (j + 1 < i && arr[j] < arr[j + 1]) {
        j++;
      }
      if (arr[j] > temp) {
        arr[k] = arr[j];
        k = j;
        j = 2 * k + 1;
      } else {
        break;
      }
    }
    arr[k] = temp;
  }
}
