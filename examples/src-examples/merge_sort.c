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

// merge sort
/* void sort(int arr[], int len) { */
/*   if (len < 2) { */
/*     return; */
/*   } */

/*   int mid = len / 2; */
/*   sort(arr, mid); */
/*   sort(arr + mid, len - mid); */

/*   int *temp = malloc(len * sizeof(int)); */
/*   int i = 0; */
/*   int j = mid; */
/*   int k = 0; */

/*   while (i < mid && j < len) { */
/*     if (arr[i] <= arr[j]) { */
/*       temp[k++] = arr[i++]; */
/*     } else { */
/*       temp[k++] = arr[j++]; */
/*     } */
/*   } */

/*   while (i < mid) { */
/*     temp[k++] = arr[i++]; */
/*   } */

/*   while (j < len) { */
/*     temp[k++] = arr[j++]; */
/*   } */

/*   for (i = 0; i < len; i++) { */
/*     arr[i] = temp[i]; */
/*   } */

/*   free(temp); */
/* } */

// non recursive merge sort
void sort(int arr[], int len) {
  int *temp = malloc(len * sizeof(int));
  int i, j, k, l, m, n;
  for (i = 1; i < len; i *= 2) {
    for (j = 0; j < len - i; j += 2 * i) {
      k = j;
      l = j + i;
      m = j + 2 * i;
      if (m > len) {
        m = len;
      }
      n = j;
      while (k < j + i && l < m) {
        if (arr[k] <= arr[l]) {
          temp[n++] = arr[k++];
        } else {
          temp[n++] = arr[l++];
        }
      }
      while (k < j + i) {
        temp[n++] = arr[k++];
      }
      while (l < m) {
        temp[n++] = arr[l++];
      }
    }
    for (j = 0; j < len; j++) {
      arr[j] = temp[j];
    }
  }
  free(temp);
}
