#include <bits/stdc++.h>
using namespace std;

string getRemainder(string dividend, string divisor)
{
	int dividend_len = dividend.size(), divisor_len = divisor.size();

	for(int i=0; i <= dividend_len-divisor_len; i++)
	{
		if(dividend[i] == '1')
		{
			for(int j=0; j<divisor_len; j++)
			{
				if(divisor[j] == dividend[i+j])
					dividend[i+j] = '0';
				else
					dividend[i+j] = '1';
			}
		}
	}

	return dividend.substr(dividend_len-divisor_len+1,divisor_len-1);
}

string takeXOR(string a, string b)
{
	for(int i=0; i<a.size(); i++)
		if(a[i] == b[i])
			a[i] = '0';
		else
			a[i] = '1';
	return a;
}

string generateErrorMask(int k, int n)
{ // generates n bit string with exactly k ones
	string mask(n,'0');
	int i=0, j;

	while(i<k)
	{
		j = rand()%n;
		if(mask[j] == '0')
		{
			mask[j] = '1';
			i++;
		}
	}
	return mask;
}

string generateBurstErrorMask(int k, int n)
{ // generates n bit string with exactly k consectuive ones
	int x = rand()%(n-k+1);
	return string(x,'0') + string(k,'1') + string(n-k-x,'0');
}

int main()
{
	srand(time(NULL));
    // see if argc, argv need to be done for i/o files
    string generator = "11000000000000101";
    string input, crc, corrupted;
    int num_errors;

    while(cin>>input)
    {
    	crc = input + getRemainder(input, generator);
    	cout<<"Input: "<<input<<endl;
    	cout<<"CRC: "<<crc<<endl;
    	cout<<"......................\n";

    	for(int j=0; j<10; j++)
    	{
    		num_errors = (rand()%4 + 1)*2 + 1;
    		corrupted = takeXOR(crc, generateErrorMask(num_errors, 32+16));

    		cout<<"Original String:          "<<input<<endl;
    		cout<<"Original String with CRC: "<<crc<<endl;
    		cout<<"Corrupted String:         "<<corrupted<<endl;
    		cout<<"Number of Errors Introduced: "<<num_errors<<endl;
    		if(getRemainder(corrupted, generator) == string(generator.size()-1,'0'))
    			cout<<"CRC Check: Passed\n\n";
    		else
    			cout<<"CRC Check: Failed\n\n";
    	}
    	cout<<"......................\n";

    	for(int j=0; j<10; j++)
    	{
    		num_errors = 2;
    		corrupted = takeXOR(crc, generateErrorMask(num_errors, 32+16));

    		cout<<"Original String:          "<<input<<endl;
    		cout<<"Original String with CRC: "<<crc<<endl;
    		cout<<"Corrupted String:         "<<corrupted<<endl;
    		cout<<"Number of Errors Introduced: "<<num_errors<<endl;
    		if(getRemainder(corrupted, generator) == string(generator.size()-1,'0'))
    			cout<<"CRC Check: Passed\n\n";
    		else
    			cout<<"CRC Check: Failed\n\n";
    	}
    	cout<<"......................\n";

    	for(int j=0; j<10; j++)
    	{
    		num_errors = 10;
    		corrupted = takeXOR(crc, generateBurstErrorMask(num_errors, 32+16));

    		cout<<"Original String:          "<<input<<endl;
    		cout<<"Original String with CRC: "<<crc<<endl;
    		cout<<"Corrupted String:         "<<corrupted<<endl;
    		cout<<"Number of Errors Introduced: "<<num_errors<<endl;
    		if(getRemainder(corrupted, generator) == string(generator.size()-1,'0'))
    			cout<<"CRC Check: Passed\n\n";
    		else
    			cout<<"CRC Check: Failed\n\n";
    	}
    	cout<<"======================\n";
    }

    return 0;
}