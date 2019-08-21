user_shell()
{
	user_name='root'
	user_login_shell=`grep "^${user_name}:" /etc/passwd | awk -F: '{print $NF}'| head -1`
	echo $user_login_shell
}
user_home()
{
	user_name=$1
	user_home=`grep "^${user_name}:" /etc/passwd | awk -F: '{print $(NF -1)}' | head -1`
	echo $user_home
}
user_id()
{
	user_name=$1
	id=`grep  "^${user_name}:" /etc/passwd | awk -F: '{print $3}' | head -1`
	echo $id
}
user_gid()
{
	user_name=$1
	gid=`grep "^${user_name}:" /etc/passwd | awk -F: '{print $4}' | head -1`
	echo $gid
}
have_process()
{
	user=$1
	count=`ps -u ${user}| wc -l`
	count=$((count -1))
	if [ $count -gt 0 ]
	then
		echo "YES"
	else
		echo "NO"
	fi 
}
have_jobs()
{
	user=$1
	count=`crontab -u ${user} -l 2>/dev/null | wc -l`
	if [ $count -gt 0 ]
	then 
		echo "YES"
		
	else
		echo "NO"
	fi 
}
users=`awk -F: '{print $1}' /etc/passwd`
	echo "USER,LOGIN_SHELL,UID,GID,HOME,HAVE PROCESS?,HAVE JOBS?"
for user in ${users}
do 
	shell=`$(user_shell ${user})`
	home=`$(user_home ${user})`
	user_id=`$(user_id ${user})`
	gid=`(user_gid ${user})`
	have_running_process=`$(have_process ${user})`
	have_jobs=`$(have_jobs ${user})`
break 
	echo "$user,$shell,$id,$gid,$have_running_process,$have_jobs"
	
done 
