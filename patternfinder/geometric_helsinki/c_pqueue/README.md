# Generic Priority Queue in C

"Academical" implementation of a priority queue in old C, nothing fancy.

I guess I (re)did this to keep my CS skills sharp.

### How it works.

The "constructor" method expects a comparator method and the capacity of the Queue:

```C
PQueue *pqueue_new(int (*cmp)(const void *d1, const void *d2), size_t capacity);
```

A simple comparator method for `int` values can look like:

```C
int cmp_ints(const void *int1, const void *int2) {
    return *(int*) int1 - *(int*) int2;
}
```

Once we have the comparator method we can create the `PQueue` and elements to it (in our case int numbers):

```C
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

// De-allocate the memory (PQueue only, not the elements)
pqueue_delete(pq);
```

Output:

```
1000
300
100
100
50
```
