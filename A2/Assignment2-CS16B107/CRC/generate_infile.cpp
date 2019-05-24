#include <bits/stdc++.h>
using namespace std;

int main()
{
	srand(time(NULL));
    
    for(int i=0; i<50; i++)
    {
        if(rand()%2 == 0)
        {//positive
            bitset<32> b(rand()%INT_MAX);
            cout<<b<<endl;
        }
        else
        {//negative
            bitset<32> b(-(rand()%INT_MAX));
            cout<<b<<endl; 
        }
    }

    return 0;
}