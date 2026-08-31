#!/bin/bash

tar -czvf update.tar.gz ../app.py ../OTDRService.py ../ErrorCode.py ../LogReport.py ../templates/admin.html ../templates/dashboard.html ../templates/login.html ../templates/setup.html ../templates/test.html  ../firmwareUpdate/createUpdate.sh ../firmwareUpdate/extractUpdate.sh ../firmwareUpdate/processUpdate.sh
gpg --recipient "harold.wasserman@gofoton.com" --encrypt update.tar.gz
mv update.tar.gz.gpg update.gfb