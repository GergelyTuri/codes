function Read_treadmill_behavior
% aa=a(1:10000);
% clear

[transfile transdir]=uigetfile('*.','Locate the behavioral data');
a=importdata([transdir transfile]);

a([1:4 end])=[];
% 
% nn=char(inputdlg('Enter the name of file'));
% dir=[beh_dir nn]
%%
% a=importdata('D2_A7_trial_20160331T184053.txt');
aa=a;
pos=[];DD=[];DDist=[];time=[]
for i=1:length(aa)
    aaa=cell2mat(aa(i));
    temp=regexp(aaa,['\y']);
    temp2=regexp(aaa,['\e']);
    if(length(temp)>1)
%     time(i)=str2double(aaa(temp(1)+1:temp(1)+7));
%    pos(i)=str2double(aaa(temp(2)+1:temp(2)+3));
%    displace(i)=str2double(aaa(temp(3)+1:temp(3)+3));
   
   indx=temp(2);
   c=[];for ij=indx:indx+6
if(isnan(str2double(aaa(ij))))
else
c=char([c char(aaa(ij))]);
end
end
 DDist=abs(str2double(c));
 DD(i)=DDist;
    end
    
    
    timestop=regexp(aaa,['\.']); %taking only in seconds must be revised later
    indx2=temp2+4;
     if(length(temp2)>0)
         if(length(aaa)<(timestop(end)+3))
   c=[];for ij=indx2:(timestop(end)-1)
if(isnan(str2double(aaa(ij))))
else
c=char([c char(aaa(ij))]);
end
end
 TTist=abs(str2double(c));
 time(i)=TTist;
         else
             c=[];for ij=indx2:(length(aaa)-1)
% if(isnan(str2double(aaa(ij))))
% else
c=char([c char(aaa(ij))]);
% end
             end
 TTist=abs(str2double(c));
 time(i)=TTist;   
         
         
         end   
         end
   
%    pause
end
figure;stairs(time,DD,'b','LineWidth',2)
xlabel('seconds','FontSize',16)
ylabel('cm','FontSize',16);
%%
% displace(displace>20)=0;
% 
% figure;plot(time,pos,'k','LineWidth',2)
% hold on;plot(time,abs(displace),'r','LineWidth',2)
% xlabel('seconds','FontSize',16)
% ylabel('cm','FontSize',16);
% legend('position','displacement');box off;
% set(gcf,'Color',[1 1 1])