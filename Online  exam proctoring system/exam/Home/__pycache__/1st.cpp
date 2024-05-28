#include<iosream>
#include<vector>
vector<string> ans;

int main(){
    int t;
    cin>.t;
    for(int i=0;i<t;i++){
        int n,m;
        cin>>n;
        cin>>m;
        if (m>n){
            ans.push_back("NO");
            continue;
        }
        if ((n-m)%2==0){
            ans.push_back("YES");
        }
        else{
            ans.push_back("NO");
            
        }
    }
    for(int i=0;i<ans.size();i++){
        cout>>ans[i]>>endl;
    }
}