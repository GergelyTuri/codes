count=0;
Count=[];
trialname=char(inputdlg('Enter a trial name'));
trialn=str2double(char(inputdlg('Enter a trial number')));
while (count<1000)

output=menu('Lick counting', ['LICK:' ' ' num2str(count)],'STOP');

if(output==1)
    count=count+1;
    Count(count,:)=[count hour(datetime) minute(datetime) second(datetime)];
elseif(output==2)
    break;
end
end
close all
save([pwd '/' trialname num2str(trialn) '_lickcount' '.mat'],'Count')