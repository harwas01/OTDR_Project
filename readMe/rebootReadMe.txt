sudo visudo
Scroll to the bottom of the file and add this rule:
pi ALL=(ALL) NOPASSWD: ALL		
This rule allows Python to issue os.system("sudo reboot")