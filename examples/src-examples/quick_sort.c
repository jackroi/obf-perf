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

// quick sort
/* void sort(int arr[], int len) { */
/*   if (len < 2) { */
/*     return; */
/*   } */

/*   int pivot = arr[len / 2]; */
/*   int i, j; */
/*   for (i = 0, j = len - 1; ; i++, j--) { */
/*     while (arr[i] < pivot) { */
/*       i++; */
/*     } */
/*     while (arr[j] > pivot) { */
/*       j--; */
/*     } */
/*     if (i >= j) { */
/*       break; */
/*     } */
/*     int temp = arr[i]; */
/*     arr[i] = arr[j]; */
/*     arr[j] = temp; */
/*   } */
/*   sort(arr, i); */
/*   sort(arr + i, len - i); */
/* } */

// non recursive quick sort
/* void sort(int arr[], int len) { */
/*   int stack[len]; */
/*   int top = -1; */
/*   stack[++top] = 0; */
/*   stack[++top] = len - 1; */

/*   while (top >= 0) { */
/*     int end = stack[top--]; */
/*     int start = stack[top--]; */

/*     if (start >= end) { */
/*       continue; */
/*     } */

/*     int pivot = arr[end]; */
/*     int i, j; */
/*     for (i = start, j = end - 1; ; i++, j--) { */
/*       while (arr[i] < pivot) { */
/*         i++; */
/*       } */
/*       while (arr[j] > pivot) { */
/*         j--; */
/*       } */
/*       if (i >= j) { */
/*         break; */
/*       } */
/*       int temp = arr[i]; */
/*       arr[i] = arr[j]; */
/*       arr[j] = temp; */
/*     } */
/*     int temp = arr[i]; */
/*     arr[i] = arr[end]; */
/*     arr[end] = temp; */

/*     stack[++top] = start; */
/*     stack[++top] = i - 1; */
/*     stack[++top] = i + 1; */
/*     stack[++top] = end; */
/*   } */
/* } */

#define MAX_LEVELS  48

// non recursive quick sort (and fixed size stack)
void sort(int arr[], int elements) {
  size_t beg[MAX_LEVELS], end[MAX_LEVELS], L, R;
  int i = 0;

  beg[0] = 0;
  end[0] = elements;
  while (i >= 0) {
    L = beg[i];
    R = end[i];
    if (R - L > 1) {
      size_t M = L + ((R - L) >> 1);
      int piv = arr[M];
      arr[M] = arr[L];

      if (i == MAX_LEVELS - 1)
        return;
      R--;
      while (L < R) {
        while (arr[R] >= piv && L < R)
          R--;
        if (L < R)
          arr[L++] = arr[R];
        while (arr[L] <= piv && L < R)
          L++;
        if (L < R)
          arr[R--] = arr[L];
      }
      arr[L] = piv;
      M = L + 1;
      while (L > beg[i] && arr[L - 1] == piv)
        L--;
      while (M < end[i] && arr[M] == piv)
        M++;
      if (L - beg[i] > end[i] - M) {
        beg[i + 1] = M;
        end[i + 1] = end[i];
        end[i++] = L;
      } else {
        beg[i + 1] = beg[i];
        end[i + 1] = L;
        beg[i++] = M;
      }
    } else {
      i--;
    }
  }
}
