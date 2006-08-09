<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>Current</title>
</head>

<body>
    <h1>Current Web Interface</h1>

    <p>The following systems are registered:</p>

    <table>
        <tr><th>Profile Name</th><th>UUID</th></tr>
        <tr py:for="profile in profiles">
            <td py:content="profile['name']">Name goes here</td>
            <td py:content="profile['uuid']">uuid string here</td>
        </tr>
    </table>
    
</body>
</html>
