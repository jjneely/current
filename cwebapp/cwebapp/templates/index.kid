<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>Current</title>
</head>

<body>
    <h1>Current Web Interface</h1>

    <p>Welcome, <span py:replace="userID">foobar</span>!</p>

    <p>You have <span py:replace="systemTotal">42 billion</span> registered 
    <a href="systems/">systems</a>.</p>

    <p>View the available <a href="channels/">channels</a>.</p>
    
    <p>If you haven't already, you might check out some of the <a href="http://www.turbogears.org/docs/" target="_blank">documentation</a>.</p>
    
    <p>Thanks for using TurboGears! See you on the <a href="http://groups.google.com/group/turbogears" target="_blank">mailing list</a> and the "turbogears" channel on irc.freenode.org!</p>
    
</body>
</html>
