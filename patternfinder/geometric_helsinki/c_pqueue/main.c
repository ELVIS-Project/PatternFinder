#include <stdio.h>
#include <stdlib.h>

#include "pqueue.h"

int cmp_ints(const void *int1, const void *int2) {
    return *(int*) int1 - *(int*) int2;
}

int main(int argc, char** argv) {
    
    PQueue* pq = pqueue_new(cmp_ints, 200);
    
    int x = 100, y = 50, z = 300, k = 100, w = 1000;
    
    pqueue_enqueue(pq, &x);
    pqueue_enqueue(pq, &y);
    pqueue_enqueue(pq, &z);
    pqueue_enqueue(pq, &k);
    pqueue_enqueue(pq, &w);
    
    int i = 0;
    for(;i<5;++i)
        printf("%d\n", *(int*) pqueue_dequeue(pq));
    
    pqueue_delete(pq);
    
    return (EXIT_SUCCESS);
}

