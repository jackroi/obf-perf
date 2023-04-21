#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE 10000


void insertion_sort(int arr[], int len);
void print_array(int array[], int size);


int main() {
  int array[SIZE];

  srand(time(NULL));   // Initialization, should only be called once.


  for (int i = 0; i < SIZE; ++i) {
    int r = rand();      // Returns a pseudo-random integer between 0 and RAND_MAX.
    array[i] = r % 10000;
  }

  print_array(array, SIZE);

  insertion_sort(array, SIZE);

  print_array(array, SIZE);

  return 0;
}

void print_array(int array[], int size) {
  printf("[ ");
  for (int i = 0; i < size; ++i) {
    printf("%d ", array[i]);
  }
  printf("]\n");
}


/**
 * insertion_sort
 * - in place
 * - stable
 * - O(n^2)
 */
void insertion_sort(int arr[], int len) {
  int i, j;
  int key;

  for (j = 1; j < len; j++) {             /* for each element in the unsorted portion */
    key = arr[j];                         /* save the value */
    i = j - 1;                            /* i starts from the right bound of the sorted portion */
    while (i >= 0 && arr[i] > key) {      /* for each element less than key, of the sorted portion */
      arr[i+1] = arr[i];                  /* shift the element right */
      i--;                                /* go to the next (going backwards) */
    }
    arr[i+1] = key;                       /* store key on the correct cell */
  }
}
