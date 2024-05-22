#include <math.h>
#include <stdio.h>
#include <time.h>

static int
clockNative()
{
    return round(clock() / CLOCKS_PER_SEC);
}

int
fib(int n)
{
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

int
main(void)
{
    int start = clockNative();

    printf("%d\n", fib(50));
    printf("%d\n", clockNative() - start);

    return 0;
}
