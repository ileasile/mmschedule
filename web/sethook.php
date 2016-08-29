<?php
define('WEBHOOK_URL', 'https://mmscedule.herokuapp.com/hellobot.php');
apiRequest('setWebhook', array('url' => isset($argv[1]) && $argv[1] == 'delete' ? '' : WEBHOOK_URL));